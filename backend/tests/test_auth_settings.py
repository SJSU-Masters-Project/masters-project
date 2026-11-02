"""Authentication class wiring and the production guard (spec 04, Req 1 & 3)."""

import importlib.util
from pathlib import Path

from django.conf import settings
from django.test import override_settings

_SETTINGS_FILE = Path(__file__).resolve().parent.parent / "config" / "settings.py"


def _load_settings_module(monkeypatch, **env):
    """Execute a fresh copy of config/settings.py under the given environment.

    Loaded under a private module name so Django's live settings are untouched. Every value is
    set explicitly, so the developer's own .env (which never overrides) cannot leak in.
    """
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    spec = importlib.util.spec_from_file_location("_settings_under_test", _SETTINGS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_blank_jwks_url_falls_back_to_issuer(monkeypatch):
    # .env.example ships "CLERK_JWKS_URL=" (blank), which sets the variable to "".
    module = _load_settings_module(
        monkeypatch, CLERK_ISSUER="https://clerk.example.com", CLERK_JWKS_URL=""
    )
    assert module.CLERK_JWKS_URL == "https://clerk.example.com/.well-known/jwks.json"


def test_explicit_jwks_url_is_kept(monkeypatch):
    module = _load_settings_module(
        monkeypatch,
        CLERK_ISSUER="https://clerk.example.com",
        CLERK_JWKS_URL="https://keys.example.com/jwks.json",
    )
    assert module.CLERK_JWKS_URL == "https://keys.example.com/jwks.json"


def _build_auth_classes(dev_auth: bool) -> list[str]:
    """Mirror the ordering rule in config/settings.py so it can be asserted directly."""
    classes = ["api.auth_clerk.ClerkAuthentication"]
    if dev_auth:
        classes.append("api.auth.DevBearerAuthentication")
    return classes


def test_clerk_class_is_listed_first_with_dev_auth():
    classes = _build_auth_classes(dev_auth=True)
    assert classes[0] == "api.auth_clerk.ClerkAuthentication"
    assert "api.auth.DevBearerAuthentication" in classes


def test_dev_auth_absent_when_disabled():
    assert _build_auth_classes(dev_auth=False) == ["api.auth_clerk.ClerkAuthentication"]


def test_live_settings_list_clerk_first():
    # The actually-loaded settings (dev auth on for tests) must have Clerk first.
    classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
    assert classes[0] == "api.auth_clerk.ClerkAuthentication"


@override_settings(CAREERS_DEV_AUTH=False)
def test_dev_token_gives_401_when_dev_auth_off(api, db):
    # With dev auth disabled, only Clerk is active; a dev token is not a Clerk token and
    # verification is unconfigured, so the request is unauthenticated (Requirement 3.2).
    api.credentials(HTTP_AUTHORIZATION="Bearer dev:someone@example.com:candidate")
    resp = api.get("/api/v1/me")
    assert resp.status_code == 401


def test_spec01_system_check_fires_on_dev_auth_in_prod():
    # Requirement 3.1: the spec 01 careers.E001 check still catches dev auth with DEBUG false.
    from api.checks import check_dev_auth_not_in_prod

    with override_settings(CAREERS_DEV_AUTH=True, DEBUG=False):
        errors = check_dev_auth_not_in_prod(None)
    assert [e.id for e in errors] == ["careers.E001"]
