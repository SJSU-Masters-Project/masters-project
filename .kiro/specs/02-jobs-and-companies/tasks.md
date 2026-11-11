# Implementation Plan

Prerequisite: spec 01 merged (dev auth, errors, ids, pagination, indexes, events, test harness).

- [ ] 1. Indexes for companies and jobs
  - Append the `companies` and `jobs` entries from design.md "Indexes" to `api/indexes.py`.
  - Test: `ensure_indexes` creates `job_text` with the given weights and is idempotent.
  - _Requirements: 5.2, 5.3_

- [ ] 2. Companies repository and serializers
  - `api/repositories/companies.py`: `create(owner_id, data)` with the one-company rule, `get(id)`, `get_for_member(user_id)`, `update(id, data)` (also renames on jobs), `is_member(company, user_id)`.
  - `api/serializers/companies.py`: `CompanyIn`, `CompanyPatchIn`, `CompanyOut` (no member ids).
  - Unit tests for the repository, including the one-company rule and rename propagation.
  - _Requirements: 1.1, 1.2, 1.6_

- [ ] 3. Company endpoints
  - Views and routes: `POST /companies`, `GET /companies/mine`, `GET /companies/{id}`, `PATCH /companies/{id}`.
  - Tests: create 201; second create 409 `already_member`; candidate 403; get hides members; non-member PATCH 403; `mine` 404 `no_company`; invalid id 404; bad website 400.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7_

- [ ] 4. Job serializers and validation
  - `api/serializers/jobs.py`: `SkillIn`, `JobCreateIn`, `JobPatchIn`, `JobOut`, `JobListOut`.
  - Unit tests for each rule in Requirement 2: title and description lengths, enums, 0 and 51 skills, duplicate names ignoring case, no required skill, openings 0 and 101, non-integer openings.
  - _Requirements: 2.2, 2.3, 2.4, 7.1, 7.2_

- [ ] 5. Jobs repository with state machine
  - `api/repositories/jobs.py`: `create`, `get`, `update` (refuse closed), `publish`, `close` (conditional `find_one_and_update` per design.md "State machine"), `search(filters, page)`, `list_for_company(company_id, statuses, page)`. Store `name_lower` for each skill.
  - Unit tests: transitions draft→open→closed; publish twice gives `None` on the second call; closed cannot be updated; search filters each work alone and combined; location regex escapes special characters (search for `C++` must not error).
  - _Requirements: 3.2, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

- [ ] 6. Job create, read and edit endpoints
  - Views and routes: `POST /jobs`, `GET /jobs/{id}`, `PATCH /jobs/{id}` with the membership and visibility rules in design.md "Endpoints".
  - Emit `job.updated` when an open job is patched.
  - Tests: employer without company 409 `no_company`; candidate 403; draft hidden from others (404) but visible to members and admin; PATCH on closed 409; non-member PATCH on open 403 and on draft 404; event emitted only for open jobs.
  - _Requirements: 2.1, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 5.4, 5.5_

- [ ] 7. Publish and close endpoints
  - `POST /jobs/{id}/publish` and `POST /jobs/{id}/close`; emit `job.published` and `job.closed`.
  - Tests: happy paths set timestamps and emit one event each; wrong transitions give 409 with current status in `details`; non-member gets 404 on a draft.
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 8. Public job search and company job list
  - `GET /jobs` with `AllowAny`, filters `q`, `work_mode`, `employment_type`, `skill`, `location`, `company_id`, and pagination; `GET /companies/{id}/jobs` with the `status` filter for members.
  - Tests: anonymous sees only open jobs, newest first; `q` ranks a title match above a description-only match; each filter; pagination totals; members see drafts in the company list, others do not.
  - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2_

- [ ] 9. OpenAPI and handover
  - `@extend_schema` on every new view (query parameters listed with `OpenApiParameter`); `spectacular --validate --fail-on-warn` passes.
  - Add a short "Jobs API" section to `README.md` with one curl example per endpoint, and send the frontend owner the field mapping from design.md "Frontend contract".
  - _Requirements: 7.1_
