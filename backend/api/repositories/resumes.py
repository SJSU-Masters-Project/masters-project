"""Resumes collection repository. File contents live in storage, never in MongoDB."""

from bson import ObjectId

from api.ids import parse_object_id
from api.mongo import get_database
from api.timeutils import utcnow

_MAX_RESUMES = 10


def _col():
    return get_database().resumes


def new_id() -> ObjectId:
    return ObjectId()


def count_active(user_id) -> int:
    return _col().count_documents({"user_id": parse_object_id(user_id), "deleted_at": None})


def find_active_by_hash(user_id, sha256: str) -> dict | None:
    return _col().find_one(
        {"user_id": parse_object_id(user_id), "sha256": sha256, "deleted_at": None}
    )


def at_limit(user_id) -> bool:
    return count_active(user_id) >= _MAX_RESUMES


def insert(doc: dict) -> dict:
    _col().insert_one(doc)
    return doc


def get_active(resume_id) -> dict | None:
    return _col().find_one({"_id": parse_object_id(resume_id), "deleted_at": None})


def get_owned_active(user_id, resume_id) -> dict | None:
    return _col().find_one(
        {
            "_id": parse_object_id(resume_id),
            "user_id": parse_object_id(user_id),
            "deleted_at": None,
        }
    )


def list_active(user_id, page: dict) -> tuple[list[dict], int]:
    uid = parse_object_id(user_id)
    query = {"user_id": uid, "deleted_at": None}
    col = _col()
    total = col.count_documents(query)
    docs = list(
        col.find(query, {"text": 0})
        .sort([("created_at", -1), ("_id", -1)])
        .skip(page["offset"])
        .limit(page["limit"])
    )
    return docs, total


def update_text(resume_id, text: str, status: str, chars: int) -> None:
    _col().update_one(
        {"_id": parse_object_id(resume_id)},
        {"$set": {"text": text, "text_status": status, "text_chars": chars}},
    )


def soft_delete(resume_id) -> None:
    _col().update_one(
        {"_id": parse_object_id(resume_id)},
        {"$set": {"deleted_at": utcnow()}},
    )


def hard_remove(resume_id) -> None:
    """Remove the record outright (used only to roll back a failed upload)."""
    _col().delete_one({"_id": parse_object_id(resume_id)})
