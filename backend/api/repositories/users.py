"""Users collection repository.

Views never touch PyMongo directly; they call these functions.
"""

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from api.ids import parse_object_id
from api.mongo import get_database
from api.timeutils import utcnow

VALID_ROLES = {"candidate", "employer", "admin"}
# Roles a user may choose for themselves via POST /api/v1/me/role. "admin" is granted
# only by the set_admin management command (spec 04, Requirement 2.5).
SELF_SELECTABLE_ROLES = {"candidate", "employer"}


def _col():
    return get_database().users


def get_by_id(user_id) -> dict | None:
    return _col().find_one({"_id": parse_object_id(user_id)})


def get_by_email(email: str) -> dict | None:
    return _col().find_one({"email": email.strip().lower()})


def get_or_create_external(provider: str, subject: str, email: str, role: str | None) -> dict:
    """Return the user for (provider, subject), creating it on first use.

    ``role`` may be ``None`` (spec 04): a user signing in through a real provider for the
    first time has no role until they pick one via ``POST /api/v1/me/role``. Development
    tokens still pass an explicit role.

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


def set_role(user_id, role: str) -> dict | None:
    """Set a user's role once, only while it is still ``None`` (spec 04, Requirement 2.2).

    Uses a conditional update guarded on ``role: None`` so a concurrent second request
    cannot overwrite an already-chosen role. Returns the updated document when the role
    was set, or ``None`` when no document matched (already set, or no such user), which the
    caller turns into 409 ``role_already_set``.
    """
    oid = parse_object_id(user_id)
    result = _col().update_one(
        {"_id": oid, "role": None},
        {"$set": {"role": role, "updated_at": utcnow()}},
    )
    if result.matched_count == 0:
        return None
    return _col().find_one({"_id": oid})


def set_admin_by_email(email: str) -> dict | None:
    """Grant the ``admin`` role to the user with ``email`` (management command only).

    Returns the updated document, or ``None`` when no user has that email. This is the only
    path that assigns ``admin`` (spec 04, Requirement 2.5); users cannot self-assign it.
    """
    email = email.strip().lower()
    result = _col().update_one(
        {"email": email},
        {"$set": {"role": "admin", "updated_at": utcnow()}},
    )
    if result.matched_count == 0:
        return None
    return _col().find_one({"email": email})
