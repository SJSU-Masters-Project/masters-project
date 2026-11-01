from unittest.mock import patch

from django.test import override_settings


def test_health_ok(api):
    resp = api.get("/api/v1/health/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["mongodb"] == "connected"
    assert "version" in body


def test_legacy_health_ok(api):
    resp = api.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_degraded_when_mongo_down(api):
    with patch("api.views.health.get_database") as mock_db:
        mock_db.return_value.command.side_effect = RuntimeError("no mongo")
        resp = api.get("/api/v1/health/")
    assert resp.status_code == 503
    assert resp.json()["mongodb"] == "unavailable"


@override_settings(DEBUG=False)
def test_health_hides_detail_when_not_debug(api):
    with patch("api.views.health.get_database") as mock_db:
        mock_db.return_value.command.side_effect = RuntimeError("secret detail")
        resp = api.get("/api/v1/health/")
    assert resp.status_code == 503
    assert "detail" not in resp.json()
