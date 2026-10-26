"""Companies collection repository."""

from bson import ObjectId

from api.ids import parse_object_id
from api.mongo import get_database
from api.timeutils import utcnow


def _col():
    return get_database().companies


def get(company_id) -> dict | None:
    return _col().find_one({"_id": parse_object_id(company_id)})


def get_for_member(user_id) -> dict | None:
    return _col().find_one({"member_ids": parse_object_id(user_id)})


def is_member(company: dict, user_id) -> bool:
    if company is None:
        return False
    return parse_object_id(user_id) in company.get("member_ids", [])


def create(owner_id, data: dict) -> dict:
    """Create a company with the caller as its only member.

    Returns ``None`` if the owner already belongs to a company (one-company rule).
    """
    owner = parse_object_id(owner_id)
    if _col().find_one({"member_ids": owner}) is not None:
        return None

    now = utcnow()
    doc = {
        "_id": ObjectId(),
        "name": data["name"],
        "website": data.get("website") or None,
        "description": data.get("description") or None,
        "location": data.get("location") or None,
        "member_ids": [owner],
        "created_by": owner,
        "created_at": now,
        "updated_at": now,
    }
    _col().insert_one(doc)
    return doc


def update(company_id, data: dict) -> dict:
    """Apply the given fields; propagate a name change to this company's jobs."""
    oid = parse_object_id(company_id)
    updates = {k: (v or None) for k, v in data.items()}
    updates["updated_at"] = utcnow()
    _col().update_one({"_id": oid}, {"$set": updates})

    if "name" in data and data["name"]:
        get_database().jobs.update_many(
            {"company_id": oid}, {"$set": {"company_name": data["name"]}}
        )
    return _col().find_one({"_id": oid})
