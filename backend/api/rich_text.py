"""Sanitise the HTML of a rich text ("text") profile section.

The allowlist matches the frontend (``frontend/src/profile/safeHtml.js``): p, br, strong, em, ul,
ol, li and ``a[href]`` where the href is an absolute http(s) URL. Everything else is removed.
"""

import re

import nh3

ALLOWED_TAGS = {"p", "br", "strong", "em", "ul", "ol", "li", "a"}
ALLOWED_ATTRIBUTES = {"a": {"href"}}
_HTTP_URL = re.compile(r"^https?://", re.IGNORECASE)


def _attribute_filter(tag: str, attribute: str, value: str) -> str | None:
    # Keep only absolute http(s) hrefs; scheme-relative ("//host") and relative links are dropped.
    if tag == "a" and attribute == "href":
        return value if _HTTP_URL.match(value.strip()) else None
    return value


def sanitize_html(html: str) -> str:
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https"},
        link_rel=None,
        attribute_filter=_attribute_filter,
    )
