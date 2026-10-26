"""Startup system checks for the careers backend.

Registered in ``ApiConfig.ready()`` so they run on ``runserver``, ``check`` and deploy.
"""

from django.conf import settings
from django.core.checks import Error, register

_DEV_SECRET = "local-development-only"


def check_dev_auth_not_in_prod(app_configs, **kwargs):
    """careers.E001: CAREERS_DEV_AUTH must not be enabled when DEBUG is false."""
    errors = []
    if getattr(settings, "CAREERS_DEV_AUTH", False) and not settings.DEBUG:
        errors.append(
            Error(
                "CAREERS_DEV_AUTH is enabled while DEBUG is false.",
                hint="Development authentication must never run in production. "
                "Set CAREERS_DEV_AUTH=false.",
                id="careers.E001",
            )
        )
    return errors


def check_secret_key_in_prod(app_configs, **kwargs):
    """careers.E002: a real SECRET_KEY is required when DEBUG is false."""
    errors = []
    if not settings.DEBUG and (not settings.SECRET_KEY or settings.SECRET_KEY == _DEV_SECRET):
        errors.append(
            Error(
                "DJANGO_SECRET_KEY is unset or uses the development default while DEBUG is false.",
                hint="Set DJANGO_SECRET_KEY to a strong, unique value in production.",
                id="careers.E002",
            )
        )
    return errors


def register_checks():
    register(check_dev_auth_not_in_prod)
    register(check_secret_key_in_prod)
