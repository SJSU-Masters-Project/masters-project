"""Shared helpers for exercising Clerk authentication in tests.

A locally generated RSA key pair signs tokens; a fake ``PyJWKClient`` returns the matching
public key so no network call is made. ``clerk_env`` installs the fake client and the
``CLERK_ISSUER`` / ``CLERK_AUTHORIZED_PARTIES`` settings for the duration of a test.
"""

import contextlib
import time
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import override_settings

ISSUER = "https://clerk.test.example"
AUTHORIZED_PARTY = "http://localhost:5173"

# One key pair for the whole test session.
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


class _FakeSigningKey:
    key = _PUBLIC_KEY


class _FakeJWKS:
    """Stand-in for PyJWKClient that returns the session public key without any HTTP call."""

    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey()


def make_token(
    *,
    sub="user_123",
    email="jordan@example.com",
    issuer=ISSUER,
    azp=AUTHORIZED_PARTY,
    sts=None,
    exp_delta=3600,
    nbf_delta=-5,
    key=None,
    algorithm="RS256",
    extra=None,
    include_nbf=True,
):
    """Mint a signed JWT. Defaults produce a valid token; override to build bad ones."""
    now = int(time.time())
    claims = {"sub": sub, "iss": issuer, "iat": now, "exp": now + exp_delta}
    if include_nbf:
        claims["nbf"] = now + nbf_delta
    if email is not None:
        claims["email"] = email
    if azp is not None:
        claims["azp"] = azp
    if sts is not None:
        claims["sts"] = sts
    if extra:
        claims.update(extra)
    signing_key = key if key is not None else _PRIVATE_KEY
    headers = {"alg": algorithm}
    return jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)


def make_unsigned_token(**kwargs):
    """A token with ``alg: none`` and no signature."""
    now = int(time.time())
    claims = {
        "sub": kwargs.get("sub", "user_123"),
        "iss": kwargs.get("issuer", ISSUER),
        "iat": now,
        "exp": now + 3600,
        "nbf": now - 5,
        "email": kwargs.get("email", "jordan@example.com"),
    }
    return jwt.encode(claims, key=None, algorithm="none")


@contextlib.contextmanager
def clerk_env(authorized_parties=(AUTHORIZED_PARTY,)):
    """Install the fake JWKS client and Clerk settings for the duration of the block."""
    from api import auth_clerk

    with override_settings(
        CLERK_ISSUER=ISSUER,
        CLERK_JWKS_URL=f"{ISSUER}/.well-known/jwks.json",
        CLERK_AUTHORIZED_PARTIES=list(authorized_parties),
    ):
        with mock.patch.object(auth_clerk, "_get_jwks", return_value=_FakeJWKS()):
            yield
