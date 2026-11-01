import json
from pathlib import Path

import pytest
from tests.conftest import as_user

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts"
CANDIDATE = "jordan@example.com"


def _minimal_body(**overrides):
    body = {
        "personal": {"fullName": "Jordan Lee"},
        "career": {"skills": ["Python"]},
        "jobPreferences": {
            "targetRoles": ["SWE"],
            "employmentTypes": ["full_time"],
            "workModes": ["remote"],
        },
    }
    body.update(overrides)
    return body


def test_put_creates_then_replaces(api):
    as_user(api, CANDIDATE, "candidate")
    r1 = api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    assert r1.status_code == 201
    assert r1.json()["personal"]["fullName"] == "Jordan Lee"
    # account email filled in
    assert r1.json()["personal"]["email"] == CANDIDATE

    r2 = api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    assert r2.status_code == 200


def test_full_example_round_trips(api):
    example = json.loads((CONTRACTS / "shared-user-profile.v1.example.json").read_text())
    body = {
        k: example[k]
        for k in (
            "personal",
            "academic",
            "certifications",
            "achievements",
            "career",
            "jobPreferences",
        )
    }
    # The example's resumeId is a placeholder that is not an owned resume; drop it.
    body["career"].pop("resumeId", None)
    as_user(api, CANDIDATE, "candidate")
    resp = api.put("/api/v1/profiles/me", body, format="json")
    assert resp.status_code == 201, resp.json()
    assert resp.json()["career"]["skills"] == example["career"]["skills"]


def test_missing_full_name_400(api):
    as_user(api, CANDIDATE, "candidate")
    body = _minimal_body(personal={})
    resp = api.put("/api/v1/profiles/me", body, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


def test_unknown_key_400_with_path(api):
    as_user(api, CANDIDATE, "candidate")
    body = _minimal_body()
    body["bogus"] = 1
    resp = api.put("/api/v1/profiles/me", body, format="json")
    assert resp.status_code == 400
    assert "bogus" in resp.json()["error"]["details"]


def test_employer_403(api):
    as_user(api, "boss@acme.com", "employer")
    resp = api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    assert resp.status_code == 403


def test_get_before_create_404(api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.get("/api/v1/profiles/me")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "profile_not_found"


def test_put_emits_event_with_changed_sections(api, db):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    evt = db.events.find_one({"type": "profile.updated"})
    assert evt is not None
    assert set(evt["payload"]["sections"]) == {"personal", "career", "jobPreferences"}


def test_patch_one_section(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"career": {"skills": ["Go", "Rust"]}}, format="json")
    assert resp.status_code == 200
    assert resp.json()["career"]["skills"] == ["Go", "Rust"]
    assert resp.json()["personal"]["fullName"] == "Jordan Lee"


def test_patch_before_create_404(api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.patch("/api/v1/profiles/me", {"career": {"skills": []}}, format="json")
    assert resp.status_code == 404


def test_patch_invalid_section_400_nothing_saved(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch(
        "/api/v1/profiles/me",
        {"personal": {"fullName": "X", "email": "bad-email"}},
        format="json",
    )
    assert resp.status_code == 400
    # original unchanged
    got = api.get("/api/v1/profiles/me").json()
    assert got["personal"]["fullName"] == "Jordan Lee"


def test_visibility_change_alone(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"visibility": "public"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["visibility"] == "public"


# ---- contract export ----


def test_shared_minimal_and_full_valid(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.get("/api/v1/profiles/me/shared")
    assert resp.status_code == 200
    body = resp.json()
    assert body["schemaVersion"] == "1.0"
    assert "visibility" not in body
    assert "section_updated_at" not in body
    # ids are strings
    assert isinstance(body["profileId"], str)
    assert isinstance(body["userId"], str)


# ---- public view ----


@pytest.fixture
def public_profile(api):
    example = json.loads((CONTRACTS / "shared-user-profile.v1.example.json").read_text())
    body = {
        k: example[k]
        for k in (
            "personal",
            "academic",
            "certifications",
            "achievements",
            "career",
            "jobPreferences",
        )
    }
    body["career"].pop("resumeId", None)
    body["visibility"] = "public"
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", body, format="json")
    user_id = api.get("/api/v1/me").json()["id"]
    return user_id


def test_public_view_hides_sensitive(public_profile, api):
    as_user(api, "viewer@example.com", "candidate")
    resp = api.get(f"/api/v1/profiles/{public_profile}")
    assert resp.status_code == 200
    body = resp.json()
    assert "email" not in body["personal"]
    assert "phone" not in body["personal"]
    assert "jobPreferences" not in body
    for rec in body["academic"]:
        assert "studentId" not in rec
        assert "gpa" not in rec
    assert "resumeId" not in body["career"]


def test_owner_sees_full(public_profile, api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.get(f"/api/v1/profiles/{public_profile}")
    assert resp.status_code == 200
    assert "jobPreferences" in resp.json()


def test_admin_sees_full(public_profile, api):
    as_user(api, "admin@example.com", "admin")
    resp = api.get(f"/api/v1/profiles/{public_profile}")
    assert resp.status_code == 200
    assert "jobPreferences" in resp.json()


def test_private_profile_404_to_others(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")  # private default
    user_id = api.get("/api/v1/me").json()["id"]

    as_user(api, "viewer@example.com", "candidate")
    assert api.get(f"/api/v1/profiles/{user_id}").status_code == 404


def test_unknown_user_404(api):
    from bson import ObjectId

    as_user(api, "viewer@example.com", "candidate")
    assert api.get(f"/api/v1/profiles/{ObjectId()}").status_code == 404


def test_anonymous_401(api, public_profile):
    api.credentials()
    assert api.get(f"/api/v1/profiles/{public_profile}").status_code == 401
