from rest_framework import serializers

from api.contracts import SECTION_NAMES

ALLOWED_TOP_LEVEL = set(SECTION_NAMES) | {"visibility"}


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

        # Fill a missing personal.email from the account email before validating,
        # so the section's required "email" is satisfied (Requirement 1.3).
        if self.account_email and "personal" in sections:
            personal = sections["personal"]
            if isinstance(personal, dict) and not personal.get("email"):
                personal["email"] = self.account_email

        for name, value in sections.items():
            errors.update(section_errors(name, value))

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
