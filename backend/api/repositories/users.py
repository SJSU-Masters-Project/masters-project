"""Users collection repository.

Views never touch PyMongo directly; they call these functions.
"""

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from api.ids import parse_object_id
from api.mongo import get_database
from api.timeutils import utcnow

VALID_ROLES = {"candidate", "employer", "admin"}


def _col():
    return get_database().users


def get_by_id(user_id) -> dict | None:
    return _col().find_one({"_id": parse_object_id(user_id)})


def get_by_email(email: str) -> dict | None:
    return _col().find_one({"email": email.strip().lower()})


def get_or_create_external(provider: str, subject: str, email: str, role: str) -> dict:
    """Return the user for (provider, subject), creating it on first use.

    Safe under concurrent first requests: on a DuplicateKeyError (another request won the
    race) the existing document is re-read and returned.
    """
    email = email.strip().lower()
    existing = _col().find_one({"auth.provider": provider, "auth.subject": subject})
    if existing is not None:
        return existing

    now = utcnow()
    doc = {
        "_id": ObjectId(),
        "email": email,
        "role": role,
        "display_name": None,
        "auth": {"provider": provider, "subject": subject},
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    try:
        _col().insert_one(doc)
        return doc
    except DuplicateKeyError:
        found = _col().find_one({"auth.provider": provider, "auth.subject": subject})
        if found is not None:
            return found
        # Email collided with a different identity.
        return _col().find_one({"email": email})
