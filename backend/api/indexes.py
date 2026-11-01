"""Index definitions for every collection.

Created idempotently by ``python manage.py ensure_indexes``.
"""

from pymongo import IndexModel

_TTL_30_DAYS = 30 * 24 * 3600

INDEXES = {
    # Spec 01
    "users": [
        IndexModel([("email", 1)], unique=True, name="email_unique"),
        IndexModel(
            [("auth.provider", 1), ("auth.subject", 1)],
            unique=True,
            name="auth_identity",
        ),
    ],
    "events": [
        IndexModel([("created_at", 1)], expireAfterSeconds=_TTL_30_DAYS, name="ttl_30d"),
        IndexModel([("type", 1), ("_id", 1)], name="type_id"),
    ],
    # Spec 02
    "companies": [
        IndexModel([("member_ids", 1)], name="members"),
    ],
    "jobs": [
        IndexModel([("status", 1), ("published_at", -1)], name="status_published"),
        IndexModel([("company_id", 1), ("status", 1)], name="company_status"),
        IndexModel([("skills.name_lower", 1)], name="skill"),
        IndexModel(
            [("title", "text"), ("skills.name", "text"), ("description", "text")],
            weights={"title": 5, "skills.name": 3, "description": 1},
            name="job_text",
        ),
    ],
    # Spec 03
    "profiles": [
        IndexModel([("user_id", 1)], unique=True, name="user_unique"),
    ],
    "resumes": [
        IndexModel(
            [("user_id", 1), ("deleted_at", 1), ("created_at", -1)],
            name="user_active",
        ),
        IndexModel([("user_id", 1), ("sha256", 1)], name="user_sha"),
    ],
}
