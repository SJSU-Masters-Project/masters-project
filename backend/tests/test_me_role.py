"""Nullable role, role selection, role_required denial, and set_admin (spec 04, Req 2)."""

from django.core.management import call_command
from django.test import override_settings
from tests.clerk_fixtures import clerk_env, make_token

TEST_URLS = "tests.urls_test"


def _signin(api, sub="user_role", email="pick@example.com"):
    """Sign in via Clerk, creating a null-role user, and return the response."""
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(sub=sub, email=email)}")
    return api.get("/api/v1/me")


def test_new_user_has_null_role(api, db):
    with clerk_env():
        resp = _signin(api)
    assert resp.status_code == 200
    assert resp.json()["role"] is None


def test_set_role_once_returns_user(api, db):
    with clerk_env():
        _signin(api, email="c@example.com")
        resp = api.post("/api/v1/me/role", {"role": "candidate"}, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "candidate"
    assert body["email"] == "c@example.com"
    assert db.users.find_one({"email": "c@example.com"})["role"] == "candidate"


def test_set_role_employer(api, db):
    with clerk_env():
        _signin(api, email="e@example.com")
        resp = api.post("/api/v1/me/role", {"role": "employer"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["role"] == "employer"


def test_second_role_attempt_gives_409(api, db):
    with clerk_env():
        _signin(api, email="d@example.com")
        first = api.post("/api/v1/me/role", {"role": "candidate"}, format="json")
        assert first.status_code == 200
        second = api.post("/api/v1/me/role", {"role": "employer"}, format="json")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "role_already_set"
    # Role unchanged.
    assert db.users.find_one({"email": "d@example.com"})["role"] == "candidate"


def test_cannot_self_assign_admin(api, db):
    with clerk_env():
        _signin(api, email="sneaky@example.com")
        resp = api.post("/api/v1/me/role", {"role": "admin"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"
    assert db.users.find_one({"email": "sneaky@example.com"})["role"] is None


def test_invalid_role_value_gives_400(api, db):
    with clerk_env():
        _signin(api, email="bad@example.com")
        resp = api.post("/api/v1/me/role", {"role": "wizard"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


@override_settings(ROOT_URLCONF=TEST_URLS)
def test_null_role_user_gets_role_required_on_candidate_endpoint(api, db):
    with clerk_env():
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(sub='nr', email='nr@example.com')}")
        resp = api.get("/api/_test/candidate")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "role_required"


@override_settings(ROOT_URLCONF=TEST_URLS)
def test_wrong_but_set_role_still_gets_forbidden(api, db):
    # A user who has chosen "employer" hitting a candidate-only endpoint gets forbidden,
    # not role_required.
    with clerk_env():
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(sub='wr', email='wr@example.com')}")
        api.post("/api/v1/me/role", {"role": "employer"}, format="json")
        resp = api.get("/api/_test/candidate")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_set_admin_command_grants_admin(api, db):
    with clerk_env():
        _signin(api, email="boss@example.com")
    call_command("set_admin", "Boss@Example.com")  # case-insensitive
    assert db.users.find_one({"email": "boss@example.com"})["role"] == "admin"


def test_set_admin_command_unknown_email_errors(db):
    import pytest
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("set_admin", "nobody@example.com")
