import json

from rest_framework import serializers

from api.contracts import SECTION_NAMES
from api.errors import ApiError
from api.profile_sections import CUSTOM_KEYS, sanitize_sections, schema_errors

ALLOWED_TOP_LEVEL = set(SECTION_NAMES) | set(CUSTOM_KEYS) | {"visibility"}

# A whole profile body larger than this is rejected. Prof. Dhar's spec sets no per-field limits.
MAX_BODY_BYTES = 256 * 1024


def enforce_body_cap(request) -> None:
    """Reject a request body over 256 KB with a 400, before any validation work."""
    too_big = ApiError(
        400,
        "validation_error",
        "The request data is invalid.",
        {"(root)": [f"The request body must be at most {MAX_BODY_BYTES // 1024} KB."]},
    )
    try:
        declared = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        declared = 0
    if declared > MAX_BODY_BYTES:
        raise too_big
    # No (or a wrong) Content-Length: measure what was actually parsed.
    if len(json.dumps(request.data, separators=(",", ":")).encode()) > MAX_BODY_BYTES:
        raise too_big


class ProfileBodyValidator:
    """Validate a PUT/PATCH profile body against the shared contract sections.

    Not a DRF Serializer: the body is the contract shape (camelCase, nested), so we validate
    with jsonschema per section rather than redeclaring every field.
    """

    def __init__(self, data: dict, account_email: str | None = None):
        self.data = data if isinstance(data, dict) else {}
        self.account_email = account_email

    def validate(self) -> tuple[dict, str | None, dict]:
        """Return (sections, visibility, errors)."""
        errors: dict[str, list[str]] = {}

        unknown = set(self.data.keys()) - ALLOWED_TOP_LEVEL
        for key in sorted(unknown):
            errors.setdefault(key, []).append("Unknown field.")

        visibility = self.data.get("visibility")
        if visibility is not None and visibility not in ("private", "public"):
            errors.setdefault("visibility", []).append("Must be 'private' or 'public'.")

        from api.contracts import section_errors

        sections = {}
        for name in SECTION_NAMES:
            if name in self.data:
                sections[name] = self.data[name]
        custom = {name: self.data[name] for name in CUSTOM_KEYS if name in self.data}

        # Fill a missing personal.email from the account email before validating,
        # so the section's required "email" is satisfied (Requirement 1.3).
        if self.account_email and "personal" in sections:
            personal = sections["personal"]
            if isinstance(personal, dict) and not personal.get("email"):
                personal["email"] = self.account_email

        for name, value in sections.items():
            errors.update(section_errors(name, value))

        # Prof. Dhar's section templates ("sections", "education"), checked on their own schema.
        if custom:
            custom_errors = schema_errors(custom)
            for path, messages in custom_errors.items():
                errors.setdefault(path, []).extend(messages)
            if not custom_errors:
                sections.update(sanitize_sections(custom))

        return sections, visibility, errors


class ProfileOut(serializers.Serializer):
    id = serializers.CharField()
    visibility = serializers.CharField()
    createdAt = serializers.CharField()
    updatedAt = serializers.CharField()
    personal = serializers.DictField()
    academic = serializers.ListField()
    certifications = serializers.ListField()
    achievements = serializers.ListField()
    career = serializers.DictField()
    jobPreferences = serializers.DictField()
    sections = serializers.ListField(required=False)
    education = serializers.DictField(required=False, allow_null=True)


class SharedProfileOut(serializers.Serializer):
    schemaVersion = serializers.CharField()
    profileId = serializers.CharField()
    userId = serializers.CharField()
    personal = serializers.DictField()
    academic = serializers.ListField()
    certifications = serializers.ListField()
    achievements = serializers.ListField()
    career = serializers.DictField()
    jobPreferences = serializers.DictField()
    updatedAt = serializers.CharField()
