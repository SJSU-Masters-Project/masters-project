# Design: jobs and companies

## Collections

### companies
```json
{ "_id": ObjectId, "name": "Northstar Health", "website": "https://northstar.example",
  "description": "...", "location": "San Jose, CA",
  "member_ids": [ObjectId], "created_by": ObjectId,
  "created_at": ISODate, "updated_at": ISODate }
```
One company per employer in this prototype (enforced in the repository: an employer who is
already in any `member_ids` cannot create another).

### jobs
```json
{ "_id": ObjectId, "company_id": ObjectId, "company_name": "Northstar Health",
  "title": "Backend Engineering Intern", "description": "...",
  "location": "San Jose, CA", "work_mode": "hybrid", "employment_type": "internship",
  "skills": [ {"name": "Python", "name_lower": "python", "required": true},
              {"name": "Docker", "name_lower": "docker", "required": false} ],
  "openings": 2, "status": "draft",
  "published_at": null, "closed_at": null, "created_by": ObjectId,
  "created_at": ISODate, "updated_at": ISODate }
```
- `company_name` is copied from the company so list pages need no join; a company rename
  runs `update_many({"company_id": id}, {"$set": {"company_name": new}})`.
- `name_lower` supports case-insensitive skill filters and uniqueness; it is never returned.
- Enum values match the shared profile schema's `employmentTypes` and `workModes`, so
  candidate preferences and jobs compare directly.
- `openings` is the employer's capacity for the allocation engine (spec 05).

## Indexes (append to `api/indexes.py`)
```python
"companies": [IndexModel([("member_ids", 1)], name="members")],
"jobs": [
  IndexModel([("status", 1), ("published_at", -1)], name="status_published"),
  IndexModel([("company_id", 1), ("status", 1)], name="company_status"),
  IndexModel([("skills.name_lower", 1)], name="skill"),
  IndexModel([("title", "text"), ("skills.name", "text"), ("description", "text")],
             weights={"title": 5, "skills.name": 3, "description": 1}, name="job_text"),
],
```
MongoDB allows one text index per collection; `job_text` is it.

## State machine
```
draft --publish--> open --close--> closed
```
Implemented in the repository with a conditional update so two requests cannot both win:
`find_one_and_update({"_id": id, "status": "draft"}, {"$set": {...}}, return_document=AFTER)`.
`None` means the job was not in the expected state, and the view returns 409 `invalid_state`
with the current status.

## Endpoints

| Method and path | Who | Notes |
|---|---|---|
| POST `/api/v1/companies` | employer | 409 `already_member` |
| GET `/api/v1/companies/mine` | employer | 404 `no_company` |
| GET `/api/v1/companies/{id}` | authenticated | no member ids in output |
| PATCH `/api/v1/companies/{id}` | member | rename propagates to jobs |
| GET `/api/v1/companies/{id}/jobs` | anyone | members and admin see all statuses |
| POST `/api/v1/jobs` | employer with company | creates `draft` |
| GET `/api/v1/jobs` | anyone (`AllowAny`) | open only; filters; paginated |
| GET `/api/v1/jobs/{id}` | anyone | non-open visible to members and admin only, else 404 |
| PATCH `/api/v1/jobs/{id}` | member | 409 if closed |
| POST `/api/v1/jobs/{id}/publish` | member | draft → open |
| POST `/api/v1/jobs/{id}/close` | member | open → closed |

Membership check: `principal.role == "admin"` or the caller's ObjectId is in the company's
`member_ids`. Visibility rule for non-members: hide drafts and closed jobs with 404
(do not reveal they exist); for open jobs a forbidden edit is 403.

## Search query
```python
filter = {"status": "open"}
if q:               filter["$text"] = {"$search": q}
if work_mode:       filter["work_mode"] = work_mode
if employment_type: filter["employment_type"] = employment_type
if skill:           filter["skills.name_lower"] = skill.strip().lower()
if location:        filter["location"] = {"$regex": re.escape(location), "$options": "i"}
if company_id:      filter["company_id"] = parse_object_id(company_id)
sort = [("score", {"$meta": "textScore"}), ("published_at", -1)] if q else [("published_at", -1), ("_id", -1)]
```
`re.escape` is required: user input must never be used as a raw regex.
`total` uses `count_documents(filter)`.

## Serializers (`api/serializers/jobs.py`, `companies.py`)
- `SkillIn`: `name` CharField(1..100, trimmed), `required` BooleanField.
- `JobCreateIn`: fields of Requirement 2; `validate_skills` checks count, case-insensitive
  uniqueness and at least one required skill.
- `JobPatchIn`: same fields, all optional (`partial=True`); at least one field present.
- `JobOut`, `CompanyIn`, `CompanyPatchIn`, `CompanyOut`, and `JobListOut` (page wrapper).
Repositories take and return plain dicts; views map with `doc_to_api`.

## Events
`job.published`, `job.updated` (open jobs only) and `job.closed`, each with payload
`{"company_id": "<hex>"}`.

## Frontend contract
`frontend/src/main.jsx` currently renders a hard-coded `jobs` array with `title`, `company`,
`location`, `type` and `salary`. The API job shape (Requirement 7) maps as
`company.name → company`, `employment_type → type`. There is no salary field; tell the
frontend owner when this spec merges.
