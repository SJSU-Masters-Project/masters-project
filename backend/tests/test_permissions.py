import pytest
from django.test import override_settings

TEST_URLS = "tests.urls_test"

CASES = [
    ("/api/_test/candidate", "candidate", "employer"),
    ("/api/_test/employer", "employer", "candidate"),
    ("/api/_test/admin", "admin", "candidate"),
]


@override_settings(ROOT_URLCONF=TEST_URLS)
@pytest.mark.parametrize("path,allowed,denied", CASES)
def test_role_allowed(api, path, allowed, denied):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer dev:u@example.com:{allowed}")
    assert api.get(path).status_code == 200


@override_settings(ROOT_URLCONF=TEST_URLS)
@pytest.mark.parametrize("path,allowed,denied", CASES)
def test_role_denied(api, path, allowed, denied):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer dev:u2@example.com:{denied}")
    resp = api.get(path)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


@override_settings(ROOT_URLCONF=TEST_URLS)
@pytest.mark.parametrize("path,allowed,denied", CASES)
def test_role_anonymous_401(api, path, allowed, denied):
    assert api.get(path).status_code == 401


@override_settings(ROOT_URLCONF=TEST_URLS)
@pytest.mark.parametrize("role", ["employer", "admin"])
def test_employer_or_admin_allowed(api, role):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer dev:eoa@example.com:{role}")
    assert api.get("/api/_test/employer-or-admin").status_code == 200


@override_settings(ROOT_URLCONF=TEST_URLS)
def test_employer_or_admin_denies_candidate(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer dev:c@example.com:candidate")
    assert api.get("/api/_test/employer-or-admin").status_code == 403
