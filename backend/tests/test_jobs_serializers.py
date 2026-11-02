import pytest
from api.serializers.jobs import JobCreateIn


def _valid_payload(**overrides):
    payload = {
        "title": "Backend Intern",
        "description": "x" * 60,
        "location": "San Jose",
        "work_mode": "hybrid",
        "employment_type": "internship",
        "openings": 2,
        "skills": [{"name": "Python", "required": True}],
    }
    payload.update(overrides)
    return payload


def test_valid_payload_passes():
    assert JobCreateIn(data=_valid_payload()).is_valid() is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": "ab"},  # too short
        {"description": "short"},  # under 50
        {"work_mode": "office"},  # bad enum
        {"employment_type": "gig"},  # bad enum
        {"openings": 0},
        {"openings": 101},
        {"openings": 2.5},  # non-integer
        {"skills": []},  # zero skills
        {"skills": [{"name": "s", "required": True}] * 51},  # over 50
        {"skills": [{"name": "Python", "required": False}]},  # no required skill
        {
            "skills": [{"name": "Python", "required": True}, {"name": "python", "required": False}]
        },  # dup
    ],
)
def test_invalid_payloads_fail(overrides):
    s = JobCreateIn(data=_valid_payload(**overrides))
    assert s.is_valid() is False
