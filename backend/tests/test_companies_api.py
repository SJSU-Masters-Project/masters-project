from tests.conftest import as_user


def test_create_company_201(api):
    as_user(api, "boss@acme.com", "employer")
    resp = api.post("/api/v1/companies", {"name": "Acme", "location": "San Jose"}, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme"
    assert "member_ids" not in body
    assert "id" in body


def test_second_create_409_already_member(api):
    as_user(api, "boss@acme.com", "employer")
    api.post("/api/v1/companies", {"name": "Acme"}, format="json")
    resp = api.post("/api/v1/companies", {"name": "Beta"}, format="json")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "already_member"


def test_candidate_cannot_create_company(api):
    as_user(api, "c@example.com", "candidate")
    resp = api.post("/api/v1/companies", {"name": "Acme"}, format="json")
    assert resp.status_code == 403


def test_get_company_hides_members(api):
    as_user(api, "boss@acme.com", "employer")
    cid = api.post("/api/v1/companies", {"name": "Acme"}, format="json").json()["id"]

    as_user(api, "viewer@example.com", "candidate")
    resp = api.get(f"/api/v1/companies/{cid}")
    assert resp.status_code == 200
    assert "member_ids" not in resp.json()


def test_non_member_patch_403(api):
    as_user(api, "boss@acme.com", "employer")
    cid = api.post("/api/v1/companies", {"name": "Acme"}, format="json").json()["id"]

    as_user(api, "other@acme.com", "employer")
    resp = api.patch(f"/api/v1/companies/{cid}", {"name": "Hacked"}, format="json")
    assert resp.status_code == 403


def test_mine_404_no_company(api):
    as_user(api, "lonely@acme.com", "employer")
    resp = api.get("/api/v1/companies/mine")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "no_company"


def test_mine_returns_company(api):
    as_user(api, "boss@acme.com", "employer")
    api.post("/api/v1/companies", {"name": "Acme"}, format="json")
    resp = api.get("/api/v1/companies/mine")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme"


def test_invalid_company_id_404(api):
    as_user(api, "boss@acme.com", "employer")
    resp = api.get("/api/v1/companies/not-an-id")
    assert resp.status_code == 404


def test_bad_website_400(api):
    as_user(api, "boss@acme.com", "employer")
    resp = api.post("/api/v1/companies", {"name": "Acme", "website": "not a url"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"
