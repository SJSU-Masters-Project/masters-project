from api.repositories import profiles as profiles_repo
from bson import ObjectId


def test_upsert_fills_defaults(db):
    uid = ObjectId()
    doc, created, changed = profiles_repo.upsert(uid, {"personal": {"fullName": "A"}})
    assert created is True
    assert doc["academic"] == []
    assert doc["career"] == {"skills": []}
    assert doc["jobPreferences"] == {
        "targetRoles": [],
        "employmentTypes": [],
        "workModes": [],
    }
    assert doc["visibility"] == "private"
    assert changed == ["personal"]


def test_replace_sections_leaves_others(db):
    uid = ObjectId()
    profiles_repo.upsert(
        uid,
        {"personal": {"fullName": "A"}, "career": {"skills": ["Python"]}},
    )
    before = profiles_repo.get_by_user(uid)
    personal_ts = before["section_updated_at"]["personal"]

    doc, changed = profiles_repo.replace_sections(uid, {"career": {"skills": ["Go"]}})
    assert changed == ["career"]
    assert doc["career"] == {"skills": ["Go"]}
    assert doc["personal"] == {"fullName": "A"}
    # personal timestamp unchanged
    assert doc["section_updated_at"]["personal"] == personal_ts


def test_replace_sections_none_when_no_profile(db):
    doc, changed = profiles_repo.replace_sections(ObjectId(), {"career": {"skills": []}})
    assert doc is None


def test_unique_user_id(db):
    uid = ObjectId()
    profiles_repo.upsert(uid, {"personal": {"fullName": "A"}})
    # a second upsert replaces, does not duplicate
    profiles_repo.upsert(uid, {"personal": {"fullName": "B"}})
    assert db.profiles.count_documents({"user_id": uid}) == 1


def test_unset_resume_id_if(db):
    uid = ObjectId()
    profiles_repo.upsert(uid, {"career": {"skills": [], "resumeId": "r123"}})
    profiles_repo.unset_resume_id_if(uid, "other")
    assert profiles_repo.get_by_user(uid)["career"].get("resumeId") == "r123"
    profiles_repo.unset_resume_id_if(uid, "r123")
    assert "resumeId" not in profiles_repo.get_by_user(uid)["career"]
