"""Identity for the careers API.

Django's auth app is not installed and there is no SQL database, so an anonymous
``request.user`` is ``None`` (``REST_FRAMEWORK["UNAUTHENTICATED_USER"] = None``) and an
authenticated principal is a lightweight dataclass with ``is_authenticated = True``.

Spec 04 adds the real authentication class next to this one; nothing else changes.
"""

from dataclasses import dataclass

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api.repositories import users as users_repo


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    role: str  # "candidate" | "employer" | "admin"
    is_authenticated: bool = True


class DevBearerAuthentication(BaseAuthentication):
    """Development-only bearer auth: ``Authorization: Bearer dev:<email>:<role>``.

    Active only while ``CAREERS_DEV_AUTH`` is true (a startup system check forbids that
    combination with ``DEBUG`` false). Creates the user on first use.
    """

    keyword = "Bearer dev:"

    def authenticate(self, request):
        if not getattr(settings, "CAREERS_DEV_AUTH", False):
            return None

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith(self.keyword):
            return None

        token = header[len("Bearer ") :]  # "dev:<email>:<role>"
        body = token[len("dev:") :]
        email, sep, role = body.rpartition(":")
        if not sep or not email or not role:
            raise AuthenticationFailed("Malformed dev token.")

        email = email.strip().lower()
        role = role.strip().lower()
        if role not in users_repo.VALID_ROLES:
            raise AuthenticationFailed("Unknown role in dev token.")

        user = users_repo.get_or_create_external(
            provider="dev", subject=email, email=email, role=role
        )
        if user is None:
            raise AuthenticationFailed("Could not resolve dev user.")
        if user["role"] != role:
            # Do not change the stored role; reject the mismatched token.
            raise AuthenticationFailed("Role does not match the stored user.")

        principal = Principal(user_id=str(user["_id"]), email=user["email"], role=user["role"])
        return (principal, None)

    def authenticate_header(self, request):
        # Returning a value makes DRF answer 401 (not 403) when auth is missing.
        return "Bearer"


class DevBearerScheme(OpenApiAuthenticationExtension):
    target_class = "api.auth.DevBearerAuthentication"
    name = "devBearer"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer"}
