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


# ---- Prof. Dhar's section templates: "sections" and "education" ----

from tests.test_profile_sections_schema import EDUCATION, SECTIONS  # noqa: E402


def _sections_body(**overrides):
    import copy

    body = _minimal_body(sections=copy.deepcopy(SECTIONS), education=copy.deepcopy(EDUCATION))
    body.update(overrides)
    return body


def _with_text(html):
    import copy

    sections = copy.deepcopy(SECTIONS)
    sections[-1]["data"] = [html]
    return sections


def test_sections_and_education_save_and_read_back_unchanged(api):
    as_user(api, CANDIDATE, "candidate")
    created = api.put("/api/v1/profiles/me", _sections_body(), format="json")
    assert created.status_code == 201, created.json()
    got = api.get("/api/v1/profiles/me").json()
    assert got["sections"] == SECTIONS
    assert got["education"] == EDUCATION


def test_stored_envelopes_have_exactly_the_four_keys(api, db):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(), format="json")
    doc = db.profiles.find_one({})
    for section in doc["sections"]:
        assert set(section) == {"heading", "visible", "template", "data"}
    assert set(doc["education"]) == {"heading", "visible", "template", "data"}


def test_profile_without_sections_returns_empty_defaults(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    got = api.get("/api/v1/profiles/me").json()
    assert got["sections"] == []
    assert got["education"] is None


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (
            lambda s: s[3]["data"][0]["skillsList"][0].update(proficiency=0),
            "sections/3/data/0/skillsList/0/proficiency",
        ),
        (
            lambda s: s[3]["data"][0]["skillsList"][0].update(proficiency=6),
            "sections/3/data/0/skillsList/0/proficiency",
        ),
        (
            lambda s: s[3]["data"][0]["skillsList"][0].update(proficiency=2.5),
            "sections/3/data/0/skillsList/0/proficiency",
        ),
        (
            lambda s: s[3]["data"][0]["skillsList"][0].update(proficiency="3"),
            "sections/3/data/0/skillsList/0/proficiency",
        ),
        (lambda s: s[0]["data"][0].update(link="javascript:alert(1)"), "sections/0/data/0/link"),
        (lambda s: s[4]["data"][0].update(url="javascript:alert(1)"), "sections/4/data/0/url"),
        (lambda s: s[0]["data"][0].update(color="red"), "sections/0/data/0"),
        (lambda s: s[0].update(template="grid"), "sections/0/template"),
        (lambda s: s[5].update(data=["one", "two"]), "sections/5/data"),
        (lambda s: s[2]["data"][0].update(date="03/15/2026"), "sections/2/data/0/date"),
        (lambda s: s[1]["data"][0].update(startDate="06/01/2026"), "sections/1/data/0/startDate"),
        (lambda s: s[0].update(id="abc"), "sections/0"),
    ],
)
def test_invalid_sections_return_400_naming_the_path(api, mutate, path):
    import copy

    as_user(api, CANDIDATE, "candidate")
    sections = copy.deepcopy(SECTIONS)
    mutate(sections)
    resp = api.put("/api/v1/profiles/me", _sections_body(sections=sections), format="json")
    assert resp.status_code == 400
    error = resp.json()["error"]
    assert error["code"] == "validation_error"
    assert path in error["details"]


def test_invalid_education_returns_400_naming_the_path(api):
    import copy

    as_user(api, CANDIDATE, "candidate")
    education = copy.deepcopy(EDUCATION)
    education["data"][0]["link"] = "javascript:alert(1)"
    resp = api.put("/api/v1/profiles/me", _sections_body(education=education), format="json")
    assert resp.status_code == 400
    assert "education/data/0/link" in resp.json()["error"]["details"]


def test_script_and_event_handlers_are_stripped_from_text(api):
    as_user(api, CANDIDATE, "candidate")
    dirty = '<p onclick="x()">hi</p><script>alert(1)</script><img src=x onerror=alert(1)>'
    resp = api.put("/api/v1/profiles/me", _sections_body(sections=_with_text(dirty)), format="json")
    assert resp.status_code == 201, resp.json()
    stored = resp.json()["sections"][-1]["data"][0]
    assert stored == "<p>hi</p>"
    assert "onerror" not in stored
    assert "<script" not in stored


def test_text_is_sanitised_on_patch_too(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch(
        "/api/v1/profiles/me",
        {"sections": _with_text('<a href="javascript:alert(1)">x</a><b>bold</b>')},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["sections"][-1]["data"] == ["<a>x</a>bold"]


def test_career_skills_are_derived_from_chips_sections_on_put(api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.put("/api/v1/profiles/me", _sections_body(), format="json")
    # The client sent career.skills = ["Python"]; the server derives them from the chips sections.
    assert resp.json()["career"]["skills"] == ["React", "CSS", "Python"]


def test_career_skills_are_derived_on_patch_without_a_career_block(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"sections": SECTIONS}, format="json")
    assert resp.status_code == 200
    assert resp.json()["career"]["skills"] == ["React", "CSS", "Python"]


def test_career_skills_derivation_wins_when_patch_also_sends_career(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch(
        "/api/v1/profiles/me",
        {"sections": SECTIONS, "career": {"headline": "Student", "skills": ["Forged"]}},
        format="json",
    )
    assert resp.status_code == 200
    career = resp.json()["career"]
    assert career["skills"] == ["React", "CSS", "Python"]
    assert career["headline"] == "Student"


def test_career_skills_are_untouched_when_sections_are_not_written(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    api.patch("/api/v1/profiles/me", {"education": EDUCATION}, format="json")
    assert api.get("/api/v1/profiles/me").json()["career"]["skills"] == ["Python"]


def test_deleting_all_chips_sections_clears_derived_skills(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"sections": []}, format="json")
    assert resp.json()["career"]["skills"] == []
    assert resp.json()["sections"] == []


def test_patch_sections_leaves_other_parts_alone(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"sections": SECTIONS[:1]}, format="json")
    got = resp.json()
    assert got["sections"] == SECTIONS[:1]
    assert got["education"] == EDUCATION
    assert got["personal"]["fullName"] == "Jordan Lee"


def test_patch_education_leaves_sections_alone(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(), format="json")
    changed = {**EDUCATION, "visible": False}
    resp = api.patch("/api/v1/profiles/me", {"education": changed}, format="json")
    assert resp.json()["education"]["visible"] is False
    assert resp.json()["sections"] == SECTIONS


def test_section_updated_at_is_set_for_the_new_keys(api, db):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    before = db.profiles.find_one({})["section_updated_at"]
    api.patch("/api/v1/profiles/me", {"sections": SECTIONS[:1]}, format="json")
    after = db.profiles.find_one({})["section_updated_at"]
    assert {"sections", "education"} <= set(after)
    assert after["sections"] >= before["sections"]
    assert after["education"] == before["education"]


def test_shared_export_still_validates_against_v1_and_omits_the_new_keys(api):
    from api.contracts import FULL

    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(), format="json")
    resp = api.get("/api/v1/profiles/me/shared")
    assert resp.status_code == 200
    doc = resp.json()
    assert FULL.is_valid(doc), [e.message for e in FULL.iter_errors(doc)]
    assert "sections" not in doc
    assert "education" not in doc
    assert doc["career"]["skills"] == ["React", "CSS", "Python"]


def test_public_view_leaves_out_hidden_sections_and_hidden_education(api):
    import copy

    as_user(api, CANDIDATE, "candidate")
    education = {**copy.deepcopy(EDUCATION), "visible": False}
    api.put(
        "/api/v1/profiles/me",
        _sections_body(education=education, visibility="public"),
        format="json",
    )
    user_id = api.get("/api/v1/me").json()["id"]

    as_user(api, "viewer@example.com", "candidate")
    body = api.get(f"/api/v1/profiles/{user_id}").json()
    headings = [s["heading"] for s in body["sections"]]
    assert "Certifications" not in headings  # visible: false
    assert headings == ["Projects", "Experience", "Skills", "Links", "About me"]
    assert body["education"] is None

    # The owner still sees everything, including the hidden section and education.
    as_user(api, CANDIDATE, "candidate")
    own = api.get(f"/api/v1/profiles/{user_id}").json()
    assert [s["heading"] for s in own["sections"]] == [s["heading"] for s in SECTIONS]
    assert own["education"]["visible"] is False


def test_public_view_shows_visible_education(api):
    as_user(api, CANDIDATE, "candidate")
    api.put("/api/v1/profiles/me", _sections_body(visibility="public"), format="json")
    user_id = api.get("/api/v1/me").json()["id"]
    as_user(api, "viewer@example.com", "candidate")
    assert api.get(f"/api/v1/profiles/{user_id}").json()["education"] == EDUCATION


def test_unknown_top_level_key_is_still_rejected(api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.put("/api/v1/profiles/me", _minimal_body(extras=[]), format="json")
    assert resp.status_code == 400
    assert "extras" in resp.json()["error"]["details"]


def test_sections_must_be_a_list_and_education_an_object(api):
    as_user(api, CANDIDATE, "candidate")
    resp = api.put(
        "/api/v1/profiles/me", _minimal_body(sections={"a": 1}, education=[]), format="json"
    )
    assert resp.status_code == 400
    details = resp.json()["error"]["details"]
    assert "sections" in details
    assert "education" in details


def test_body_over_256_kb_is_rejected_with_400(api):
    as_user(api, CANDIDATE, "candidate")
    big = [
        {
            "heading": "Big",
            "visible": True,
            "template": "text",
            "data": ["x" * (300 * 1024)],
        }
    ]
    resp = api.put("/api/v1/profiles/me", _minimal_body(sections=big), format="json")
    assert resp.status_code == 400
    assert "256 KB" in resp.json()["error"]["details"]["(root)"][0]

    api.put("/api/v1/profiles/me", _minimal_body(), format="json")
    resp = api.patch("/api/v1/profiles/me", {"sections": big}, format="json")
    assert resp.status_code == 400


def test_body_just_under_the_cap_is_accepted(api):
    as_user(api, CANDIDATE, "candidate")
    ok = [{"heading": "Big", "visible": True, "template": "text", "data": ["x" * (200 * 1024)]}]
    resp = api.put("/api/v1/profiles/me", _minimal_body(sections=ok), format="json")
    assert resp.status_code == 201
