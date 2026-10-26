from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from rest_framework.exceptions import NotFound

from api.timeutils import to_iso


def parse_object_id(value) -> ObjectId:
    """Parse a 24-char hex string into an ObjectId.

    Raises DRF ``NotFound`` (404 ``not_found``) for any invalid string, so an invalid
    path id never surfaces as a 500.
    """
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise NotFound("Resource not found.") from None


def _convert(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return to_iso(value)
    if isinstance(value, dict):
        return {k: _convert(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert(v) for v in value]
    return value


def doc_to_api(doc: dict | None) -> dict | None:
    """Convert a MongoDB document into an API-safe dict.

    Renames ``_id`` to ``id`` (as a hex string), converts nested ObjectIds to strings
    and datetimes to ISO 8601. The original document is not mutated.
    """
    if doc is None:
        return None
    out = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        else:
            out[key] = _convert(value)
    return out
