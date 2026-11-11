# Implementation Plan

Prerequisites: specs 01 to 03 merged. Tasks 1 and 9 to 10 can run before the gates.
Tasks 2 to 8 need Gate B for the collection they read.

- [ ] 1. Share the proposed contracts
  - Send design.md "Proposed collection shapes" to Uday, Eshan and Nitish (and yourself as scorer owner); record each owner's agreement or changes in design.md with the date.
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

- [ ] 2. Read-side repositories and seed fixtures
  - `api/repositories/runs.py` (latest done score run, latest done allocation round), `matches.py`, `explanations.py`, `skills.py`; indexes from design.md appended to `api/indexes.py`.
  - `tests/fixtures/services.py` seeding each collection in the agreed shape.
  - Tests: latest-run selection ignores `requested`, `running` and `failed` runs.
  - _Requirements: 1.1, 2.1, 2.2_

- [ ] 3. Candidate matches endpoint
  - `GET /api/v1/me/matches`.
  - Tests: ordered by `rank_for_candidate`; closed jobs excluded; no run gives empty list; employer gets 403.
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 4. Employer matches endpoint
  - `GET /api/v1/jobs/{id}/matches?mode=ranked|allocated` using the spec 03 public view.
  - Tests: ranked order; allocated never exceeds `openings`; private profiles excluded; non-member 404; bad `mode` 400.
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Explanation endpoint
  - `GET /api/v1/matches/explanation`.
  - Tests: candidate sees own; job member sees it; another candidate 404; missing explanation 404.
  - _Requirements: 3.1, 3.2_

- [ ] 6. Extracted skills endpoint
  - `GET /api/v1/me/skills` for the primary resume and profile, grouped by backend, with unlinked spans.
  - Tests: both backends returned with spans; no extraction yet gives empty lists.
  - _Requirements: 4.1, 4.2_

- [ ] 7. Admin allocation rounds
  - `POST` and `GET /api/v1/admin/allocation-rounds` with the one-active-run check from design.md and the `allocation.requested` event.
  - Tests: 202 on create; second create while active 409 `run_in_progress`; non-admin 403; status and results readable when the fixture marks it done.
  - _Requirements: 5.1, 5.3, 5.4, 5.5_

- [ ] 8. Admin audit runs
  - Same as task 7 for `audit-runs`, with `backends` validation (`baseline`, `agentic`).
  - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [ ] 9. Sync consent flag
  - Add careers-only `syncConsent` (default false) to the profile API from spec 03; keep it out of the export.
  - Tests: default false; PATCH to true; export unchanged.
  - _Requirements: 6.1, 6.2_

- [ ] 10. MyAcademic read-only stub
  - `ServiceTokenAuthentication`, `IsService`, `GET /api/v1/integrations/myacademic/profile?email=`; `MYACADEMIC_SERVICE_TOKEN` setting (system check: required and at least 32 characters when DEBUG is false).
  - Tests: correct token and consent 200 with a schema-valid export; no consent 404; unknown email 404; wrong or missing token 401; a candidate's bearer token cannot call it; log line has no token.
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 11. OpenAPI and handover
  - `@extend_schema` everywhere; schema validation passes; README sections; send the stub's URL, header and response example to Mourya (MyAcademic) through Prof. Dhar.
  - _Requirements: 7.1_
