"""Prof. Dhar's profile section templates: schema, sanitising and skill derivation."""

import copy

import pytest
from api.profile_sections import derive_skills, sanitize_sections, schema_errors
from api.rich_text import sanitize_html

EDUCATION = {
    "heading": "Education",
    "visible": True,
    "template": "timeline",
    "data": [
        {
            "degree": "MS Software Engineering",
            "institute": "San Jose State University",
            "grade": "3.9 GPA",
            "link": "https://www.sjsu.edu",
            "startDate": "2025-08-01",
            "endDate": None,
        },
        {
            "degree": "BTech",
            "institute": "Example Institute",
            "startDate": None,
            "endDate": "2025-05-01",
        },
    ],
}

SECTIONS = [
    {
        "heading": "Projects",
        "visible": True,
        "template": "cards",
        "data": [
            {
                "title": "Careers portal",
                "purpose": "A job portal.",
                "link": "https://example.com/careers",
                "techStack": ["React", "Django"],
                "features": ["Job search", "Profiles"],
            },
            {"title": "Bare card"},
            {
                "title": "Empty optionals",
                "purpose": "",
                "link": "",
                "techStack": [],
                "features": [],
            },
        ],
    },
    {
        "heading": "Experience",
        "visible": True,
        "template": "timeline",
        "data": [
            {
                "title": "Intern",
                "subtitle": "Northstar Labs",
                "link": "https://example.com/n",
                "description": "Built dashboards.",
                "startDate": "2026-06-01",
                "endDate": None,
            },
            {"title": "Tutor", "subtitle": "SJSU", "startDate": None, "endDate": None},
        ],
    },
    {
        "heading": "Certifications",
        "visible": False,
        "template": "list",
        "data": [
            {
                "title": "AWS Cloud Practitioner",
                "subtitle": "Amazon Web Services",
                "link": "https://example.com/verify",
                "date": "2026-03-15",
                "description": "Foundational.",
            },
            {"title": "Dean's list", "date": None},
        ],
    },
    {
        "heading": "Skills",
        "visible": True,
        "template": "chips",
        "data": [
            {
                "category": "Frontend",
                "skillsList": [
                    {"skillName": "React", "proficiency": 4},
                    {"skillName": "CSS", "proficiency": 3},
                ],
            },
            {
                "category": "Backend",
                "skillsList": [
                    {"skillName": "Python", "proficiency": 5},
                    {"skillName": "react", "proficiency": 2},
                ],
            },
        ],
    },
    {
        "heading": "Links",
        "visible": True,
        "template": "links",
        "data": [
            {"name": "GitHub", "url": "https://github.com/example", "description": "My code."},
            {"name": "Blog", "url": "https://example.com/blog"},
        ],
    },
    {
        "heading": "About me",
        "visible": True,
        "template": "text",
        "data": [
            '<p>Hello <strong>there</strong>, see <a href="https://example.com">my site</a>.</p>'
        ],
    },
]


def body():
    return {"sections": copy.deepcopy(SECTIONS), "education": copy.deepcopy(EDUCATION)}


def section(template):
    return next(s for s in body()["sections"] if s["template"] == template)


def with_section(sec):
    return {"sections": [sec]}


def test_full_body_is_valid():
    assert schema_errors(body()) == {}


def test_empty_data_arrays_are_valid():
    assert (
        schema_errors(
            {"sections": [{"heading": "X", "visible": True, "template": "cards", "data": []}]}
        )
        == {}
    )
    assert schema_errors({"education": {**EDUCATION, "data": []}}) == {}


def test_each_template_accepts_its_items_only():
    # A timeline item is not a valid card (unknown keys) and a card is not a valid timeline entry.
    sec = section("cards")
    sec["data"] = [SECTIONS[1]["data"][0]]
    assert any("subtitle" in m for msgs in schema_errors(with_section(sec)).values() for m in msgs)
    sec = section("timeline")
    sec["data"] = [{"title": "Only a title"}]
    errors = schema_errors(with_section(sec))
    assert "sections/0/data/0" in errors  # missing subtitle / startDate / endDate


@pytest.mark.parametrize("proficiency", [0, 6, 2.5, "3", None, True, -1])
def test_bad_proficiency_names_its_path(proficiency):
    sec = section("chips")
    sec["data"][0]["skillsList"][1]["proficiency"] = proficiency
    errors = schema_errors(with_section(sec))
    assert "sections/0/data/0/skillsList/1/proficiency" in errors


@pytest.mark.parametrize("proficiency", [1, 2, 3, 4, 5])
def test_good_proficiency(proficiency):
    sec = section("chips")
    sec["data"][0]["skillsList"][0]["proficiency"] = proficiency
    assert schema_errors(with_section(sec)) == {}


def test_skills_list_needs_at_least_one_entry():
    sec = section("chips")
    sec["data"][0]["skillsList"] = []
    assert "sections/0/data/0/skillsList" in schema_errors(with_section(sec))


@pytest.mark.parametrize(
    ("template", "field", "path"),
    [
        ("cards", "link", "sections/0/data/0/link"),
        ("timeline", "link", "sections/0/data/0/link"),
        ("list", "link", "sections/0/data/0/link"),
        ("links", "url", "sections/0/data/0/url"),
    ],
)
@pytest.mark.parametrize(
    "bad",
    [
        "javascript:alert(1)",
        "data:text/html,hi",
        "ftp://example.com",
        "//example.com",
        "example.com",
    ],
)
def test_non_http_links_are_rejected(template, field, path, bad):
    sec = section(template)
    sec["data"][0][field] = bad
    assert path in schema_errors(with_section(sec))


def test_education_link_must_be_http():
    edu = copy.deepcopy(EDUCATION)
    edu["data"][0]["link"] = "javascript:alert(1)"
    assert "education/data/0/link" in schema_errors({"education": edu})


def test_scheme_is_case_insensitive():
    sec = section("links")
    sec["data"][0]["url"] = "HTTPS://Example.com"
    assert schema_errors(with_section(sec)) == {}


def test_required_url_cannot_be_empty():
    sec = section("links")
    sec["data"][0]["url"] = ""
    assert "sections/0/data/0/url" in schema_errors(with_section(sec))


@pytest.mark.parametrize("field", ["startDate", "endDate"])
@pytest.mark.parametrize("bad", ["06/01/2026", "", "2026-6-1", "2026-02-30", "June 2026", 5])
def test_timeline_dates_must_be_iso_or_null(field, bad):
    sec = section("timeline")
    sec["data"][0][field] = bad
    assert f"sections/0/data/0/{field}" in schema_errors(with_section(sec))


def test_list_date_rejects_mm_dd_yyyy():
    sec = section("list")
    sec["data"][0]["date"] = "03/15/2026"
    assert "sections/0/data/0/date" in schema_errors(with_section(sec))


@pytest.mark.parametrize("field", ["startDate", "endDate"])
def test_dates_must_be_present_even_when_null(field):
    sec = section("timeline")
    del sec["data"][0][field]
    assert "sections/0/data/0" in schema_errors(with_section(sec))


def test_current_flag_is_not_allowed():
    sec = section("timeline")
    sec["data"][0]["current"] = True
    errors = schema_errors(with_section(sec))
    assert any("current" in m for m in errors["sections/0/data/0"])


def test_unknown_item_key_is_rejected():
    sec = section("cards")
    sec["data"][0]["color"] = "red"
    errors = schema_errors(with_section(sec))
    assert any("color" in m for m in errors["sections/0/data/0"])


@pytest.mark.parametrize("extra", ["id", "order", "_key"])
def test_envelope_stores_exactly_four_keys(extra):
    sec = section("cards")
    sec[extra] = "x"
    assert "sections/0" in schema_errors(with_section(sec))


def test_unknown_template_is_rejected():
    sec = section("cards")
    sec["template"] = "grid"
    assert "sections/0/template" in schema_errors(with_section(sec))


def test_envelope_fields_are_required():
    for key in ("heading", "visible", "template", "data"):
        sec = section("cards")
        del sec[key]
        assert "sections/0" in schema_errors(with_section(sec)), key


def test_heading_cannot_be_blank():
    sec = section("cards")
    sec["heading"] = "   "
    assert "sections/0/heading" in schema_errors(with_section(sec))


@pytest.mark.parametrize("data", [["a", "b"], [], [5], "text", [None]])
def test_text_data_is_exactly_one_string(data):
    sec = section("text")
    sec["data"] = data
    assert any(p.startswith("sections/0/data") for p in schema_errors(with_section(sec)))


def test_text_accepts_one_string():
    sec = section("text")
    sec["data"] = ["plain text"]
    assert schema_errors(with_section(sec)) == {}


def test_missing_required_titles():
    sec = section("cards")
    sec["data"][0]["title"] = ""
    assert "sections/0/data/0/title" in schema_errors(with_section(sec))
    sec = section("timeline")
    del sec["data"][0]["subtitle"]
    assert "sections/0/data/0" in schema_errors(with_section(sec))
    edu = copy.deepcopy(EDUCATION)
    edu["data"][0]["degree"] = " "
    assert "education/data/0/degree" in schema_errors({"education": edu})


def test_education_envelope_is_fixed():
    for key, value in (("heading", "Schooling"), ("template", "cards")):
        edu = copy.deepcopy(EDUCATION)
        edu[key] = value
        assert f"education/{key}" in schema_errors({"education": edu})


def test_education_uses_its_own_item_fields():
    edu = copy.deepcopy(EDUCATION)
    edu["data"][0] = {"title": "MS", "subtitle": "SJSU", "startDate": None, "endDate": None}
    assert "education/data/0" in schema_errors({"education": edu})


# ---- rich text ----


def test_sanitize_strips_scripts_handlers_and_unknown_markup():
    dirty = (
        '<p onclick="x()">hi</p><script>alert(1)</script><img src=x onerror=alert(1)>'
        '<h1 style="color:red">t</h1><iframe src="https://e.com"></iframe>'
    )
    out = sanitize_html(dirty)
    for bad in ("script", "onclick", "onerror", "<img", "<h1", "style", "iframe"):
        assert bad not in out
    assert "hi" in out


def test_sanitize_keeps_the_allowed_tags():
    html = (
        "<p>a<br>b</p><ul><li><strong>x</strong></li></ul><ol><li><em>y</em></li></ol>"
        '<a href="https://example.com">z</a>'
    )
    assert sanitize_html(html) == html


@pytest.mark.parametrize(
    "href", ["javascript:alert(1)", "data:text/html,x", "//evil.com", "/relative"]
)
def test_sanitize_drops_unsafe_hrefs(href):
    assert "href" not in sanitize_html(f'<a href="{href}">x</a>')


def test_sanitize_drops_other_attributes():
    out = sanitize_html('<a href="https://e.com" target="_self" class="c" rel="x">x</a>')
    assert out == '<a href="https://e.com">x</a>'


def test_sanitize_sections_only_touches_text_and_does_not_mutate_input():
    original = body()
    original["sections"][-1]["data"] = ['<p onclick="x()">hi</p><script>alert(1)</script>']
    snapshot = copy.deepcopy(original)
    cleaned = sanitize_sections(original)
    assert original == snapshot
    assert cleaned["sections"][-1]["data"] == ["<p>hi</p>"]
    assert cleaned["sections"][0] == original["sections"][0]


# ---- skills ----


def test_derive_skills_is_unique_ignoring_case_across_chips_sections():
    assert derive_skills(SECTIONS) == ["React", "CSS", "Python"]


def test_derive_skills_ignores_other_templates_and_empty_input():
    assert derive_skills([SECTIONS[0], SECTIONS[1]]) == []
    assert derive_skills([]) == []
    assert derive_skills(None) == []


def test_derive_skills_respects_the_v1_limits():
    long_name = "x" * 101
    many = [{"skillName": f"s{i}", "proficiency": 3} for i in range(150)]
    sections = [
        {
            "heading": "S",
            "visible": True,
            "template": "chips",
            "data": [
                {"category": "c", "skillsList": [{"skillName": long_name, "proficiency": 3}, *many]}
            ],
        }
    ]
    skills = derive_skills(sections)
    assert len(skills) == 100
    assert long_name not in skills
