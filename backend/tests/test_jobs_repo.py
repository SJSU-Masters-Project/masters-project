from api.repositories import jobs as jobs_repo
from bson import ObjectId


def _company():
    return {"_id": ObjectId(), "name": "Acme"}


def _data(**overrides):
    d = {
        "title": "Backend Intern",
        "description": "x" * 60,
        "location": "San Jose",
        "work_mode": "hybrid",
        "employment_type": "internship",
        "openings": 2,
        "skills": [{"name": "Python", "required": True}, {"name": "Docker", "required": False}],
    }
    d.update(overrides)
    return d


def test_state_machine_transitions(db):
    company = _company()
    owner = ObjectId()
    job = jobs_repo.create(company, owner, _data())
    assert job["status"] == "draft"

    opened = jobs_repo.publish(job["_id"])
    assert opened["status"] == "open"
    assert opened["published_at"] is not None

    # publish twice: second returns None
    assert jobs_repo.publish(job["_id"]) is None

    closed = jobs_repo.close(job["_id"])
    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None

    # close twice: None
    assert jobs_repo.close(job["_id"]) is None


def test_closed_cannot_be_updated(db):
    company = _company()
    job = jobs_repo.create(company, ObjectId(), _data())
    jobs_repo.publish(job["_id"])
    jobs_repo.close(job["_id"])
    assert jobs_repo.update(job["_id"], {"title": "New Title Here"}) is None


def test_name_lower_stored(db):
    company = _company()
    job = jobs_repo.create(company, ObjectId(), _data())
    stored = db.jobs.find_one({"_id": job["_id"]})
    assert stored["skills"][0]["name_lower"] == "python"


def test_search_filters(db):
    company = _company()
    j1 = jobs_repo.create(company, ObjectId(), _data(work_mode="remote", location="Austin"))
    j2 = jobs_repo.create(
        company, ObjectId(), _data(title="Data Analyst", work_mode="on_site", location="San Jose")
    )
    jobs_repo.publish(j1["_id"])
    jobs_repo.publish(j2["_id"])

    page = {"limit": 20, "offset": 0}
    docs, total = jobs_repo.search({"work_mode": "remote"}, page)
    assert total == 1 and docs[0]["_id"] == j1["_id"]

    docs, total = jobs_repo.search({"skill": "PYTHON"}, page)
    assert total == 2

    docs, total = jobs_repo.search({"location": "san jose"}, page)
    assert total == 1 and docs[0]["_id"] == j2["_id"]


def test_search_location_escapes_regex(db):
    company = _company()
    j = jobs_repo.create(company, ObjectId(), _data(location="C++ shop"))
    jobs_repo.publish(j["_id"])
    # Must not raise on special regex characters.
    docs, total = jobs_repo.search({"location": "C++"}, {"limit": 20, "offset": 0})
    assert total == 1


def test_search_only_open(db):
    company = _company()
    draft = jobs_repo.create(company, ObjectId(), _data())
    opened = jobs_repo.create(company, ObjectId(), _data())
    jobs_repo.publish(opened["_id"])
    docs, total = jobs_repo.search({}, {"limit": 20, "offset": 0})
    assert total == 1
    assert docs[0]["_id"] == opened["_id"]
    assert draft["_id"] not in [d["_id"] for d in docs]
