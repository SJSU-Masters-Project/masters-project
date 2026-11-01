from django.core.management import call_command


def test_spectacular_validates(tmp_path):
    out = tmp_path / "schema.yml"
    # --fail-on-warn makes this raise if the schema has any warning.
    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(out))
    assert out.exists()
    assert out.stat().st_size > 0


def test_schema_endpoint_200(api):
    resp = api.get("/api/v1/schema/")
    assert resp.status_code == 200
