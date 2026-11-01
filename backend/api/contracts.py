"""Load and validate against the shared user profile contract (Draft 2020-12).

The contract files in ``backend/contracts/`` are Eshan's, committed unchanged. A new version
is a new file, never an edit.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"

SCHEMA = json.loads((CONTRACTS_DIR / "shared-user-profile.v1.schema.json").read_text())

FULL = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

SECTION_NAMES = (
    "personal",
    "academic",
    "certifications",
    "achievements",
    "career",
    "jobPreferences",
)

SECTION = {
    name: Draft202012Validator(SCHEMA["properties"][name], format_checker=FormatChecker())
    for name in SECTION_NAMES
}


def _path_str(error) -> str:
    parts = [str(p) for p in error.absolute_path]
    return "/".join(parts) if parts else "(root)"


def section_errors(name: str, value) -> dict[str, list[str]]:
    """Validate one section; return ``{json_pointer: [messages]}`` ({} when valid)."""
    validator = SECTION[name]
    out: dict[str, list[str]] = {}
    for error in validator.iter_errors(value):
        key = f"{name}/{_path_str(error)}" if error.absolute_path else name
        out.setdefault(key, []).append(error.message)
    return out
