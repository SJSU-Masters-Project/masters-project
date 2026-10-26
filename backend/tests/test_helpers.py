from datetime import UTC, datetime

import pytest
from api.ids import doc_to_api, parse_object_id
from api.pagination import parse_page_params
from api.timeutils import to_iso, utcnow
from bson import ObjectId
from rest_framework.exceptions import NotFound, ValidationError


def test_parse_object_id_valid():
    oid = ObjectId()
    assert parse_object_id(str(oid)) == oid


def test_parse_object_id_invalid_raises_notfound():
    with pytest.raises(NotFound):
        parse_object_id("not-an-id")


def test_doc_to_api_renames_id_and_converts():
    oid = ObjectId()
    nested = ObjectId()
    dt = datetime(2026, 10, 25, 18, 0, 0, 123000, tzinfo=UTC)
    doc = {"_id": oid, "company_id": nested, "created_at": dt, "items": [nested]}
    out = doc_to_api(doc)
    assert out["id"] == str(oid)
    assert "_id" not in out
    assert out["company_id"] == str(nested)
    assert out["created_at"] == "2026-10-25T18:00:00.123Z"
    assert out["items"] == [str(nested)]


def test_to_iso_ends_in_z():
    assert to_iso(utcnow()).endswith("Z")


def test_utcnow_is_aware():
    assert utcnow().tzinfo is not None


def test_page_defaults():
    params = parse_page_params({})
    assert params == {"limit": 20, "offset": 0}


@pytest.mark.parametrize("bad", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_page_rejects_bad_values(bad):
    with pytest.raises(ValidationError):
        parse_page_params(bad)
