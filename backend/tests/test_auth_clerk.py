"""Clerk session-token verification (spec 04, Requirements 4.1-4.5, 2.1, 3a)."""

import time

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from tests.clerk_fixtures import clerk_env, make_token, make_unsigned_token


def _auth(api, token):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api.get("/api/v1/me")


def test_valid_token_authenticates(api, db):
    with clerk_env():
        resp = _auth(api, make_token(email="Jordan@Example.com"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "jordan@example.com"
    assert body["role"] is None  # new Clerk user has no role yet (Requirement 2.1)


def test_token_without_azp_is_accepted(api, db):
    with clerk_env():
        resp = _auth(api, make_token(azp=None))
    assert resp.status_code == 200


def test_first_call_creates_user_second_reuses(api, db):
    with clerk_env():
        r1 = _auth(api, make_token(sub="user_abc", email="a@example.com"))
        assert r1.status_code == 200
        assert db.users.count_documents({}) == 1
        first_id = r1.json()["id"]

        r2 = _auth(api, make_token(sub="user_abc", email="a@example.com"))
        assert r2.status_code == 200
        assert db.users.count_documents({}) == 1
        assert r2.json()["id"] == first_id

    created = db.users.find_one({"auth.provider": "clerk", "auth.subject": "user_abc"})
    assert created is not None
    assert created["role"] is None


def test_subject_maps_to_auth_identity(api, db):
    with clerk_env():
        _auth(api, make_token(sub="user_xyz", email="z@example.com"))
    doc = db.users.find_one({"email": "z@example.com"})
    assert doc["auth"] == {"provider": "clerk", "subject": "user_xyz"}


@pytest.mark.parametrize(
    "token_kwargs",
    [
        {"exp_delta": -10},  # expired
        {"nbf_delta": 3600},  # not yet valid (beyond 5s leeway)
        {"issuer": "https://evil.example"},  # wrong issuer
        {"azp": "https://evil.example"},  # azp not authorized
        {"sts": "pending"},  # pending status
    ],
    ids=["expired", "future_nbf", "wrong_issuer", "wrong_azp", "sts_pending"],
)
def test_bad_claims_give_401(api, db, token_kwargs):
    with clerk_env():
        resp = _auth(api, make_token(**token_kwargs))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "authentication_failed"


def test_nbf_within_leeway_is_accepted(api, db):
    # 3 seconds in the future is within the 5s leeway.
    with clerk_env():
        resp = _auth(api, make_token(nbf_delta=3))
    assert resp.status_code == 200


def test_wrong_signature_gives_401(api, db):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with clerk_env():
        resp = _auth(api, make_token(key=other_key))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "authentication_failed"


def test_alg_none_token_gives_401(api, db):
    with clerk_env():
        resp = _auth(api, make_unsigned_token())
    assert resp.status_code == 401


def test_hs256_token_gives_401(api, db):
    # HS256-signed token must be rejected: only RS256 is accepted.
    with clerk_env():
        token = make_token(key="a-shared-secret-that-is-long-enough-32b", algorithm="HS256")
        resp = _auth(api, token)
    assert resp.status_code == 401


def test_missing_required_claim_gives_401(api, db):
    # A token without exp is missing a required claim.
    import jwt
    from tests.clerk_fixtures import _PRIVATE_KEY, ISSUER

    now = int(time.time())
    claims = {"sub": "u", "iss": ISSUER, "iat": now, "nbf": now - 5, "email": "x@example.com"}
    token = jwt.encode(claims, _PRIVATE_KEY, algorithm="RS256")
    with clerk_env():
        resp = _auth(api, token)
    assert resp.status_code == 401


def test_dev_token_ignored_by_clerk_falls_through(api, db):
    # A "dev:" token is not a Clerk token; with dev auth on it still authenticates via
    # DevBearerAuthentication, proving ClerkAuthentication returns None rather than erroring.
    with clerk_env():
        api.credentials(HTTP_AUTHORIZATION="Bearer dev:devguy@example.com:candidate")
        resp = api.get("/api/v1/me")
    assert resp.status_code == 200
    assert resp.json()["role"] == "candidate"


def test_no_outbound_call_to_myacademic_during_signin(api, db, monkeypatch):
    """Requirement 3a.2: sign-in must not call MyAcademic or any outbound host.

    We block the low-level socket connect and HTTP client constructors; a valid sign-in must
    still succeed, proving verification is local (the JWKS client is the fake one).
    """
    import socket

    calls = []

    real_create_connection = socket.create_connection

    def _blocked_create_connection(address, *args, **kwargs):
        calls.append(address)
        raise AssertionError(f"Unexpected outbound connection to {address!r} during sign-in")

    monkeypatch.setattr(socket, "create_connection", _blocked_create_connection)

    import http.client

    def _blocked_http(*args, **kwargs):
        calls.append(("http", args))
        raise AssertionError("Unexpected HTTP connection during sign-in")

    monkeypatch.setattr(http.client.HTTPConnection, "connect", _blocked_http)
    monkeypatch.setattr(http.client.HTTPSConnection, "connect", _blocked_http)

    with clerk_env():
        resp = _auth(api, make_token(sub="user_local", email="local@example.com"))

    assert resp.status_code == 200
    assert calls == []
    # Restore for cleanliness (monkeypatch also undoes this at teardown).
    socket.create_connection = real_create_connection
