from django.test import override_settings
from tests.conftest import as_user


def test_dev_request_creates_then_reuses_user(api, db):
    as_user(api, "Jordan@Example.com", "candidate")
    resp = api.get("/api/v1/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "jordan@example.com"  # lowercased
    assert body["role"] == "candidate"
    assert db.users.count_documents({}) == 1

    # second request reuses
    resp2 = api.get("/api/v1/me")
    assert resp2.status_code == 200
    assert db.users.count_documents({}) == 1
    assert resp2.json()["id"] == body["id"]


def test_me_returns_expected_fields(api):
    as_user(api, "a@example.com", "employer")
    body = api.get("/api/v1/me").json()
    assert set(body.keys()) == {"id", "email", "role", "created_at"}
    assert body["created_at"].endswith("Z")


def test_no_header_gives_401(api):
    resp = api.get("/api/v1/me")
    assert resp.status_code == 401


def test_role_mismatch_gives_401_and_keeps_role(api, db):
    as_user(api, "x@example.com", "candidate")
    assert api.get("/api/v1/me").status_code == 200

    as_user(api, "x@example.com", "employer")
    resp = api.get("/api/v1/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "authentication_failed"
    assert db.users.find_one({"email": "x@example.com"})["role"] == "candidate"


@override_settings(CAREERS_DEV_AUTH=False)
def test_dev_auth_disabled_gives_401_even_with_header(api):
    as_user(api, "y@example.com", "candidate")
    assert api.get("/api/v1/me").status_code == 401
