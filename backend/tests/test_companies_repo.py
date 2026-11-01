from api.repositories import companies as companies_repo
from bson import ObjectId


def test_create_and_one_company_rule(db):
    owner = ObjectId()
    c1 = companies_repo.create(owner, {"name": "Acme"})
    assert c1 is not None
    assert c1["member_ids"] == [owner]
    # same owner cannot create a second company
    c2 = companies_repo.create(owner, {"name": "Beta"})
    assert c2 is None


def test_rename_propagates_to_jobs(db):
    owner = ObjectId()
    company = companies_repo.create(owner, {"name": "OldName"})
    db.jobs.insert_one(
        {
            "_id": ObjectId(),
            "company_id": company["_id"],
            "company_name": "OldName",
            "status": "open",
        }
    )
    companies_repo.update(company["_id"], {"name": "NewName"})
    job = db.jobs.find_one({"company_id": company["_id"]})
    assert job["company_name"] == "NewName"


def test_is_member(db):
    owner = ObjectId()
    company = companies_repo.create(owner, {"name": "Acme"})
    assert companies_repo.is_member(company, owner) is True
    assert companies_repo.is_member(company, ObjectId()) is False
