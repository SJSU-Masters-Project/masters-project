"""Prof. Dhar's profile section templates: the ``sections`` array and the ``education`` section.

The schema lives in ``api/schemas/profile-sections.schema.json``. It is deliberately not in
``backend/contracts/``, which holds Eshan's shared v1 profile contract and is never edited.
These keys are stored on the profile but are not part of the v1 export.
"""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from api.rich_text import sanitize_html

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "profile-sections.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

CUSTOM_KEYS = ("sections", "education")

# Limits taken from the v1 contract's ``career.skills``, so derived skills always export cleanly.
MAX_SKILLS = 100
MAX_SKILL_LENGTH = 100


def _message(error) -> str:
    """Plain-language message for the schema keywords used in the profile sections schema."""
    if error.validator == "anyOf":
        return "Must be empty, or a link that starts with http:// or https://."
    if error.validator == "pattern":
        if error.validator_value == "\\S":
            return "This field is required."
        if error.validator_value.startswith("^[Hh]"):
            return "Must be a link that starts with http:// or https://."
        return "Must be a date in YYYY-MM-DD format, or null."
    if error.validator == "format" and error.validator_value == "date":
        return "Must be a real calendar date in YYYY-MM-DD format, or null."
    if error.validator == "minimum" or error.validator == "maximum":
        return "Must be a whole number from 1 to 5."
    if error.validator == "type" and error.validator_value == "integer":
        return "Must be a whole number from 1 to 5."
    if error.validator == "additionalProperties":
        return error.message.replace("Additional properties are not allowed", "Unknown field")
    return error.message


def schema_errors(value: dict) -> dict[str, list[str]]:
    """Validate ``{"sections": ..., "education": ...}``; return ``{json_pointer: [messages]}``."""
    out: dict[str, list[str]] = {}
    errors = sorted(VALIDATOR.iter_errors(value), key=lambda e: list(map(str, e.absolute_path)))
    for error in errors:
        path = "/".join(str(p) for p in error.absolute_path) or "(root)"
        message = _message(error)
        if message not in out.setdefault(path, []):
            out[path].append(message)
    return out


def sanitize_sections(value: dict) -> dict:
    """Return a copy with every rich text string sanitised. Input must already be valid."""
    clean = copy.deepcopy(value)
    for section in clean.get("sections", []) or []:
        if section.get("template") == "text":
            section["data"] = [sanitize_html(text) for text in section["data"]]
    return clean


def derive_skills(sections) -> list[str]:
    """Unique skill names (ignoring case, first spelling wins) from every ``chips`` section."""
    seen: set[str] = set()
    names: list[str] = []
    for section in sections or []:
        if not isinstance(section, dict) or section.get("template") != "chips":
            continue
        for category in section.get("data") or []:
            for skill in (category or {}).get("skillsList") or []:
                name = str((skill or {}).get("skillName", "")).strip()
                key = name.lower()
                if name and len(name) <= MAX_SKILL_LENGTH and key not in seen:
                    seen.add(key)
                    names.append(name)
    return names[:MAX_SKILLS]


def public_sections(doc: dict) -> dict:
    """The parts of ``sections`` / ``education`` other users may see: visible ones only."""
    education = doc.get("education")
    return {
        "education": education if education and education.get("visible") else None,
        "sections": [s for s in doc.get("sections") or [] if s.get("visible")],
    }
