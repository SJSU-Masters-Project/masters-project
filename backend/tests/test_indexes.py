import pytest
from django.core.management import call_command
from pymongo.errors import DuplicateKeyError


def test_ensure_indexes_idempotent(db):
    call_command("ensure_indexes")
    call_command("ensure_indexes")  # second run must not error


def test_users_unique_email(db):
    db.users.insert_one({"email": "dup@example.com", "role": "candidate"})
    with pytest.raises(DuplicateKeyError):
        db.users.insert_one({"email": "dup@example.com", "role": "employer"})


def test_events_ttl_index_30_days(db):
    info = db.events.index_information()
    ttl = info["ttl_30d"]
    assert ttl["expireAfterSeconds"] == 30 * 24 * 3600


def test_job_text_index_weights(db):
    info = db.jobs.index_information()
    assert "job_text" in info
    assert info["job_text"]["weights"] == {"title": 5, "skills.name": 3, "description": 1}
