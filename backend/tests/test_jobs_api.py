import pytest
from tests.conftest import as_user

EMPLOYER = "boss@acme.com"


def _job_payload(**overrides):
    p = {
        "title": "Backend Intern",
        "description": "x" * 60,
        "location": "San Jose",
        "work_mode": "hybrid",
        "employment_type": "internship",
        "openings": 2,
        "skills": [{"name": "Python", "required": True}],
    }
    p.update(overrides)
    return p


@pytest.fixture
def employer_with_company(api):
    as_user(api, EMPLOYER, "employer")
    api.post("/api/v1/companies", {"name": "Acme"}, format="json")
    return api


def _create_job(api, **overrides):
    return api.post("/api/v1/jobs", _job_payload(**overrides), format="json")


def test_employer_without_company_409(api):
    as_user(api, "nocompany@acme.com", "employer")
    resp = _create_job(api)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "no_company"


def test_candidate_cannot_post_job(api):
    as_user(api, "c@example.com", "candidate")
    assert _create_job(api).status_code == 403


def test_create_job_draft_201(employer_with_company):
    resp = _create_job(employer_with_company)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "draft"
    assert body["company"]["name"] == "Acme"
    assert body["skills"] == [{"name": "Python", "required": True}]


def test_draft_hidden_from_others_visible_to_members_and_admin(employer_with_company, api):
    jid = _create_job(employer_with_company).json()["id"]

    # another candidate: 404
    as_user(api, "someone@example.com", "candidate")
    assert api.get(f"/api/v1/jobs/{jid}").status_code == 404

    # admin: 200
    as_user(api, "admin@acme.com", "admin")
    assert api.get(f"/api/v1/jobs/{jid}").status_code == 200

    # member sees it
    as_user(api, EMPLOYER, "employer")
    assert api.get(f"/api/v1/jobs/{jid}").status_code == 200


def test_publish_sets_status_and_emits_event(employer_with_company, db):
    jid = _create_job(employer_with_company).json()["id"]
    resp = employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"
    assert resp.json()["published_at"] is not None
    assert db.events.count_documents({"type": "job.published"}) == 1


def test_double_publish_409_with_status(employer_with_company):
    jid = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    resp = employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"
    assert resp.json()["error"]["details"]["status"] == "open"


def test_close_emits_event(employer_with_company, db):
    jid = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    resp = employer_with_company.post(f"/api/v1/jobs/{jid}/close")
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
    assert db.events.count_documents({"type": "job.closed"}) == 1


def test_patch_closed_409(employer_with_company):
    jid = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    employer_with_company.post(f"/api/v1/jobs/{jid}/close")
    resp = employer_with_company.patch(f"/api/v1/jobs/{jid}", {"title": "New Title"}, format="json")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_patch_open_emits_job_updated(employer_with_company, db):
    jid = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{jid}/publish")
    resp = employer_with_company.patch(
        f"/api/v1/jobs/{jid}", {"title": "Updated Title"}, format="json"
    )
    assert resp.status_code == 200
    assert db.events.count_documents({"type": "job.updated"}) == 1


def test_patch_draft_no_event(employer_with_company, db):
    jid = _create_job(employer_with_company).json()["id"]
    employer_with_company.patch(f"/api/v1/jobs/{jid}", {"title": "Draft Edit"}, format="json")
    assert db.events.count_documents({"type": "job.updated"}) == 0


def test_non_member_patch_open_403_draft_404(employer_with_company, api):
    draft_id = _create_job(employer_with_company).json()["id"]
    open_id = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{open_id}/publish")

    as_user(api, "intruder@acme.com", "employer")
    assert (
        api.patch(f"/api/v1/jobs/{draft_id}", {"title": "x" * 5}, format="json").status_code == 404
    )
    assert (
        api.patch(f"/api/v1/jobs/{open_id}", {"title": "New Title"}, format="json").status_code
        == 403
    )


def test_non_member_publish_draft_404(employer_with_company, api):
    jid = _create_job(employer_with_company).json()["id"]
    as_user(api, "intruder@acme.com", "employer")
    assert api.post(f"/api/v1/jobs/{jid}/publish").status_code == 404


def test_public_search_open_only_newest_first(employer_with_company, api):
    a = _create_job(employer_with_company, title="First Role").json()["id"]
    b = _create_job(employer_with_company, title="Second Role").json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{a}/publish")
    employer_with_company.post(f"/api/v1/jobs/{b}/publish")
    # one draft remains hidden
    _create_job(employer_with_company, title="Hidden Draft")

    api.credentials()  # anonymous
    resp = api.get("/api/v1/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["items"][0]["id"] == b  # newest published first


def test_search_q_ranks_title_over_description(employer_with_company, api):
    title_match = _create_job(
        employer_with_company, title="Python Engineer", description="General backend work " * 4
    ).json()["id"]
    desc_match = _create_job(
        employer_with_company,
        title="Backend Engineer",
        description=("We use python a lot here. " * 3) + "x" * 10,
        skills=[{"name": "Go", "required": True}],
    ).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{title_match}/publish")
    employer_with_company.post(f"/api/v1/jobs/{desc_match}/publish")

    api.credentials()
    body = api.get("/api/v1/jobs?q=python").json()
    assert body["total"] >= 1
    assert body["items"][0]["id"] == title_match


def test_company_job_list_member_sees_all_others_open_only(employer_with_company, api):
    draft = _create_job(employer_with_company).json()["id"]
    opened = _create_job(employer_with_company).json()["id"]
    employer_with_company.post(f"/api/v1/jobs/{opened}/publish")
    company_id = employer_with_company.get("/api/v1/companies/mine").json()["id"]

    # member sees both
    body = employer_with_company.get(f"/api/v1/companies/{company_id}/jobs").json()
    assert body["total"] == 2

    # another candidate sees only open
    as_user(api, "viewer@example.com", "candidate")
    body2 = api.get(f"/api/v1/companies/{company_id}/jobs").json()
    assert body2["total"] == 1
    assert body2["items"][0]["id"] == opened
    assert draft not in [i["id"] for i in body2["items"]]
