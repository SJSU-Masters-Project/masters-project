import json
from pathlib import Path

from api.contracts import (
    FULL,
    SCHEMA,  # noqa: F401
    section_errors,
)

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts"


def test_example_passes_full():
    example = json.loads((CONTRACTS / "shared-user-profile.v1.example.json").read_text())
    assert FULL.is_valid(example), [e.message for e in FULL.iter_errors(example)]


def test_minimal_profile_with_empty_arrays_passes():
    doc = {
        "schemaVersion": "1.0",
        "profileId": "p1",
        "userId": "u1",
        "personal": {"fullName": "A B", "email": "a@example.com"},
        "academic": [],
        "certifications": [],
        "achievements": [],
        "career": {"skills": []},
        "jobPreferences": {"targetRoles": [], "employmentTypes": [], "workModes": []},
        "updatedAt": "2026-10-09T18:00:00Z",
    }
    assert FULL.is_valid(doc), [e.message for e in FULL.iter_errors(doc)]


def test_bad_email_rejected_with_path():
    errors = section_errors("personal", {"fullName": "A", "email": "not-an-email"})
    assert any("email" in key for key in errors)


def test_bad_uri_rejected():
    errors = section_errors(
        "certifications", [{"name": "C", "issuer": "X", "credentialUrl": "not a uri"}]
    )
    assert errors  # some error reported


def test_bad_date_time_rejected():
    errors = section_errors(
        "academic",
        [
            {
                "recordId": "r1",
                "institution": "I",
                "program": "P",
                "status": "enrolled",
                "verified": True,
                "lastSyncedAt": "not-a-datetime",
            }
        ],
    )
    assert errors


def test_unknown_field_rejected_with_path():
    errors = section_errors("personal", {"fullName": "A", "email": "a@example.com", "nope": 1})
    assert errors
