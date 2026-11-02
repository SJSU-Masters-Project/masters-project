import pytest
from api.events import emit_event
from bson import ObjectId


def test_emit_inserts_one_document(db):
    eid = ObjectId()
    emit_event("job.published", "job", eid, {"company_id": "abc"})
    doc = db.events.find_one({"entity_id": eid})
    assert doc is not None
    assert doc["type"] == "job.published"
    assert doc["entity_type"] == "job"
    assert doc["payload"] == {"company_id": "abc"}
    assert "created_at" in doc


def test_emit_rejects_large_payload(db):
    big = {"blob": "x" * 3000}
    with pytest.raises(ValueError):
        emit_event("resume.uploaded", "resume", ObjectId(), big)
    assert db.events.count_documents({}) == 0
