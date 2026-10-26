"""Outbox events for other project services.

Other services keep their own checkpoint (last processed ``_id``) and poll the ``events``
collection. The API never calls those services directly and never waits for them.
"""

import json

from bson import ObjectId

from api.mongo import get_database
from api.timeutils import utcnow

# Payloads carry ids and small metadata only, never file contents or full profiles.
_MAX_PAYLOAD_BYTES = 2048


def emit_event(type: str, entity_type: str, entity_id, payload: dict | None = None) -> ObjectId:
    """Insert one document into ``events`` and return its ``_id``.

    Raises ``ValueError`` if the payload serializes to more than 2 KB, keeping events small.
    """
    payload = payload or {}
    encoded = json.dumps(payload, default=str)
    if len(encoded.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise ValueError("Event payload exceeds 2 KB; store ids and metadata only.")

    if entity_id is not None and not isinstance(entity_id, ObjectId):
        try:
            entity_id = ObjectId(entity_id)
        except Exception:
            # Keep the raw value if it is not an ObjectId-shaped string.
            pass

    doc = {
        "type": type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
        "created_at": utcnow(),
    }
    result = get_database().events.insert_one(doc)
    return result.inserted_id
