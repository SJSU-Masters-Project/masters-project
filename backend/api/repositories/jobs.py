"""Jobs collection repository: lifecycle state machine and search."""

import re

from bson import ObjectId
from pymongo import ReturnDocument

from api.ids import parse_object_id
from api.mongo import get_database
from api.timeutils import to_iso, utcnow


def _col():
    return get_database().jobs


def _skills_to_storage(skills: list[dict]) -> list[dict]:
    return [
        {
            "name": s["name"].strip(),
            "name_lower": s["name"].strip().lower(),
            "required": s["required"],
        }
        for s in skills
    ]


def to_job_api(doc: dict | None) -> dict | None:
    """Convert a stored job document into the public job shape (Requirement 7)."""
    if doc is None:
        return None
    return {
        "id": str(doc["_id"]),
        "company": {"id": str(doc["company_id"]), "name": doc.get("company_name")},
        "title": doc["title"],
        "description": doc["description"],
        "location": doc.get("location") or None,
        "work_mode": doc["work_mode"],
        "employment_type": doc["employment_type"],
        "skills": [{"name": s["name"], "required": s["required"]} for s in doc.get("skills", [])],
        "openings": doc["openings"],
        "status": doc["status"],
        "published_at": to_iso(doc["published_at"]) if doc.get("published_at") else None,
        "closed_at": to_iso(doc["closed_at"]) if doc.get("closed_at") else None,
        "created_at": to_iso(doc["created_at"]),
        "updated_at": to_iso(doc["updated_at"]),
    }


def get(job_id) -> dict | None:
    return _col().find_one({"_id": parse_object_id(job_id)})


def create(company: dict, owner_id, data: dict) -> dict:
    now = utcnow()
    doc = {
        "_id": ObjectId(),
        "company_id": company["_id"],
        "company_name": company["name"],
        "title": data["title"],
        "description": data["description"],
        "location": data.get("location") or None,
        "work_mode": data["work_mode"],
        "employment_type": data["employment_type"],
        "skills": _skills_to_storage(data["skills"]),
        "openings": data["openings"],
        "status": "draft",
        "published_at": None,
        "closed_at": None,
        "created_by": parse_object_id(owner_id),
        "created_at": now,
        "updated_at": now,
    }
    _col().insert_one(doc)
    return doc


def update(job_id, data: dict) -> dict | None:
    """Apply fields to a draft or open job. Returns ``None`` if the job is closed."""
    oid = parse_object_id(job_id)
    updates = dict(data)
    if "skills" in updates:
        updates["skills"] = _skills_to_storage(updates["skills"])
    if "location" in updates:
        updates["location"] = updates["location"] or None
    updates["updated_at"] = utcnow()
    return _col().find_one_and_update(
        {"_id": oid, "status": {"$in": ["draft", "open"]}},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )


def publish(job_id) -> dict | None:
    """draft -> open. Returns ``None`` if the job was not in ``draft``."""
    now = utcnow()
    return _col().find_one_and_update(
        {"_id": parse_object_id(job_id), "status": "draft"},
        {"$set": {"status": "open", "published_at": now, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )


def close(job_id) -> dict | None:
    """open -> closed. Returns ``None`` if the job was not ``open``."""
    now = utcnow()
    return _col().find_one_and_update(
        {"_id": parse_object_id(job_id), "status": "open"},
        {"$set": {"status": "closed", "closed_at": now, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )


def _build_search_filter(filters: dict) -> dict:
    query: dict = {"status": "open"}
    if filters.get("q"):
        query["$text"] = {"$search": filters["q"]}
    if filters.get("work_mode"):
        query["work_mode"] = filters["work_mode"]
    if filters.get("employment_type"):
        query["employment_type"] = filters["employment_type"]
    if filters.get("skill"):
        query["skills.name_lower"] = filters["skill"].strip().lower()
    if filters.get("location"):
        query["location"] = {"$regex": re.escape(filters["location"]), "$options": "i"}
    if filters.get("company_id"):
        query["company_id"] = parse_object_id(filters["company_id"])
    return query


def search(filters: dict, page: dict) -> tuple[list[dict], int]:
    query = _build_search_filter(filters)
    col = _col()
    total = col.count_documents(query)
    if filters.get("q"):
        cursor = col.find(query, {"score": {"$meta": "textScore"}}).sort(
            [("score", {"$meta": "textScore"}), ("published_at", -1)]
        )
    else:
        cursor = col.find(query).sort([("published_at", -1), ("_id", -1)])
    docs = list(cursor.skip(page["offset"]).limit(page["limit"]))
    return docs, total


def list_for_company(company_id, statuses: list[str] | None, page: dict) -> tuple[list[dict], int]:
    query: dict = {"company_id": parse_object_id(company_id)}
    if statuses:
        query["status"] = {"$in": statuses}
    col = _col()
    total = col.count_documents(query)
    docs = list(
        col.find(query)
        .sort([("created_at", -1), ("_id", -1)])
        .skip(page["offset"])
        .limit(page["limit"])
    )
    return docs, total
