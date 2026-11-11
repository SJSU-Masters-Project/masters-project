"""Profiles collection repository.

Sections are stored exactly in the shared contract shape. ``section_updated_at`` is a
careers-internal per-section timestamp map for later sync conflict handling.
"""

from bson import ObjectId

from api.contracts import SECTION_NAMES
from api.ids import parse_object_id
from api.mongo import get_database
from api.profile_sections import CUSTOM_KEYS, derive_skills
from api.timeutils import utcnow

# Every top-level key a write can set: the shared v1 sections plus Prof. Dhar's section templates.
ALL_NAMES = (*SECTION_NAMES, *CUSTOM_KEYS)


def _col():
    return get_database().profiles


def _empty_sections() -> dict:
    return {
        "personal": {},
        "academic": [],
        "certifications": [],
        "achievements": [],
        "career": {"skills": []},
        "jobPreferences": {
            "targetRoles": [],
            "employmentTypes": [],
            "workModes": [],
        },
        "sections": [],
        "education": None,
    }


def get_by_user(user_id) -> dict | None:
    return _col().find_one({"user_id": parse_object_id(user_id)})


def upsert(user_id, sections: dict, visibility: str | None = None) -> tuple[dict, bool, list[str]]:
    """Create or replace the whole profile. Returns (doc, created, changed_sections)."""
    uid = parse_object_id(user_id)
    now = utcnow()
    existing = _col().find_one({"user_id": uid})

    merged = _empty_sections()
    merged.update({k: v for k, v in sections.items() if k in ALL_NAMES})
    if "sections" in sections:
        # career.skills always follows the chips sections, so the client is never trusted for it.
        merged["career"] = {**merged["career"], "skills": derive_skills(sections["sections"])}

    changed = [name for name in ALL_NAMES if name in sections]
    section_updated_at = {name: now for name in ALL_NAMES}

    vis = visibility or (existing.get("visibility") if existing else None) or "private"

    doc = {
        "user_id": uid,
        "visibility": vis,
        **merged,
        "section_updated_at": section_updated_at,
        "updated_at": now,
    }
    if existing is None:
        doc["_id"] = ObjectId()
        doc["created_at"] = now
        _col().insert_one(doc)
        return doc, True, changed

    doc["created_at"] = existing["created_at"]
    _col().replace_one({"_id": existing["_id"]}, {"_id": existing["_id"], **doc})
    doc["_id"] = existing["_id"]
    return doc, False, changed


def replace_sections(
    user_id, sections: dict, visibility: str | None = None
) -> tuple[dict | None, list[str]]:
    """Replace only the given sections; leave others and their timestamps unchanged.

    Returns (doc, changed_sections). ``doc`` is ``None`` if no profile exists.
    """
    uid = parse_object_id(user_id)
    existing = _col().find_one({"user_id": uid})
    if existing is None:
        return None, []

    now = utcnow()
    updates: dict = {"updated_at": now}
    changed: list[str] = []
    for name in ALL_NAMES:
        if name in sections:
            updates[name] = sections[name]
            updates[f"section_updated_at.{name}"] = now
            changed.append(name)
    if "sections" in sections:
        # career.skills always follows the chips sections. Set it inside "career" when that is also
        # being replaced (Mongo rejects setting both "career" and "career.skills").
        skills = derive_skills(sections["sections"])
        if "career" in updates:
            updates["career"] = {**updates["career"], "skills": skills}
        else:
            updates["career.skills"] = skills
    if visibility is not None:
        updates["visibility"] = visibility

    _col().update_one({"_id": existing["_id"]}, {"$set": updates})
    return _col().find_one({"_id": existing["_id"]}), changed


def set_resume_id(user_id, resume_id: str) -> None:
    uid = parse_object_id(user_id)
    _col().update_one(
        {"user_id": uid},
        {"$set": {"career.resumeId": resume_id, "updated_at": utcnow()}},
    )


def unset_resume_id_if(user_id, resume_id: str) -> None:
    """Clear ``career.resumeId`` only if it currently equals ``resume_id``."""
    uid = parse_object_id(user_id)
    _col().update_one(
        {"user_id": uid, "career.resumeId": resume_id},
        {"$unset": {"career.resumeId": ""}, "$set": {"updated_at": utcnow()}},
    )
