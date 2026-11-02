"""Clerk session-token authentication for the careers API (spec 04).

The React portal signs users in with Clerk's frontend SDK and sends Clerk's session token as
``Authorization: Bearer <jwt>``. This class verifies the token locally against Clerk's JWKS
(no network call to Clerk per request beyond fetching/refreshing signing keys) and maps it to
the spec 01 ``Principal``.

Careers uses a Clerk application created for careers alone; it does not share a Clerk
instance, user pool or session with MyAcademic, and nothing here reads or writes MyAcademic
(decision of 2026-10-03). Sign-in only finds or creates the careers ``users`` record.

Verification follows Clerk's manual JWT verification guide
(https://clerk.com/docs/guides/sessions/manual-jwt-verification):
RS256 against the Frontend API JWKS, check ``exp``/``nbf`` (5 s leeway), check ``azp`` only
when the claim is present, and reject ``sts: pending``. Checking ``iss`` against
``CLERK_ISSUER`` is an extra safeguard the guide does not require.

Only the ``Authorization`` header is read; Clerk's same-origin ``__session`` cookie is
ignored, so CSRF protection is not needed.
"""

import jwt
from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from jwt import PyJWKClient
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api.auth import Principal
from api.repositories import users as users_repo

# The signing-key client caches keys and refetches the JWKS when an unknown key id appears.
# Built lazily so importing this module does not require Clerk to be configured (local runs
# and tests leave CLERK_JWKS_URL empty); tests patch ``_get_jwks`` to inject a fake client.
_jwks_client: PyJWKClient | None = None


def _get_jwks() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.CLERK_JWKS_URL:
            raise AuthenticationFailed("Clerk is not configured.")
        _jwks_client = PyJWKClient(settings.CLERK_JWKS_URL, cache_keys=True)
    return _jwks_client


def bearer_token(request) -> str | None:
    """Return the raw bearer token, or ``None`` when absent or a development token.

    A ``Bearer dev:...`` token is left for ``DevBearerAuthentication`` to handle, so this
    class returns ``None`` (anonymous) and lets DRF try the next authenticator.
    """
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        return None
    token = header[len("Bearer ") :].strip()
    if not token or token.startswith("dev:"):
        return None
    return token


class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = bearer_token(request)
        if token is None:
            return None

        try:
            key = _get_jwks().get_signing_key_from_jwt(token).key
        except jwt.PyJWKClientError as exc:
            raise AuthenticationFailed("Could not resolve the token signing key.") from exc
        except jwt.DecodeError as exc:
            raise AuthenticationFailed("Malformed token.") from exc

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=settings.CLERK_ISSUER,
                leeway=5,
                options={"require": ["exp", "nbf", "sub", "iss"]},
            )
        except jwt.InvalidTokenError as exc:
            # Covers expired, not-yet-valid, wrong issuer, bad signature, wrong algorithm,
            # and missing required claims.
            raise AuthenticationFailed("Invalid token.") from exc

        # Check "azp" only when present (Clerk's guide: skip the check only when absent).
        if "azp" in claims and claims["azp"] not in settings.CLERK_AUTHORIZED_PARTIES:
            raise AuthenticationFailed("Token azp is not an authorized party.")

        # Reject pending sign-ins (only set with Organizations; a safeguard here).
        if claims.get("sts") == "pending":
            raise AuthenticationFailed("Token is in a pending state.")

        user = users_repo.get_or_create_external(
            "clerk", claims["sub"], claims.get("email"), role=None
        )
        return (Principal(str(user["_id"]), user["email"], user["role"]), None)

    def authenticate_header(self, request):
        # Returning a value makes DRF answer 401 (not 403) when auth is missing.
        return "Bearer"


class ClerkScheme(OpenApiAuthenticationExtension):
    target_class = "api.auth_clerk.ClerkAuthentication"
    name = "clerkBearer"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Clerk session token (JWT).",
        }
