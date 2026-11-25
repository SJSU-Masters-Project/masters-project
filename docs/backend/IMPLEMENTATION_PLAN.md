# Careers backend: implementation plan

Owner: Himanshu Jain · Written 2026-10-25 · Executed with Kiro from `.kiro/specs/`

## Where things stand (repo commit d70ba75, 2026-09-28)
- `backend/` is a scaffold: Django with PyMongo, three placeholder endpoints
  (`health/`, a fake `auth/login/` returning `"development-token"`, and `jobs/` listing
  up to 50 documents). No DRF, no tests, no validation, no backend deployment.
- CI deploys only the frontend (two identical workflows, `deploy.yml` and
  `deploy-frontend.yml`, both to `/var/www/careers.myacademic.org`).
- The frontend uses hard-coded sample jobs and calls no API yet.

## Order of work

| # | Spec | Can start | Sprint | Depends on |
|---|---|---|---|---|
| 01 | backend-foundation | Now | S3 (Oct 26 - Nov 8) | nothing |
| 02 | jobs-and-companies | After 01 | S3 | 01 |
| 03 | candidate-profiles-and-resumes | After 01 | S3 - S4 | 01 (02 not needed) |
| 04 | auth-provider | **Gate A** | S4 (Nov 9 - 22) | 01, decision at the Oct 26 meeting |
| 05 | service-integration | **Gate B** (part 5A after 02/03) | S4 - S5 | owners of the other services |
| 06 | backend-deployment | After 01 | S4 - S5 (Nov 23 - Dec 4) | Eshan (EC2, nginx); sign-in works in production only after 04 |

Specs 02 and 03 run on the dev authentication from spec 01, so nothing waits for the
auth decision. Spec 04 only swaps the authentication class and adds sign-in endpoints.

## Decision gates

**Gate A: auth (Oct 26 meeting).** Decide: (1) Clerk or self-managed auth;
(2) who builds it, you or Eshan; (3) how a user picks the candidate or employer role.
Spec 04 contains both options; delete the one not chosen before running it.

**Gate B: service contracts.** For each collection another service writes
(`extracted_skills`; `score_runs` and `match_scores`; `allocation_rounds` and `allocations`;
`explanations`; `audit_runs`), agree the document shape with its owner. Spec 05 has a
proposal for each. Per the repo's Sep 16 notes, the scorer and explanations are also yours.

**Gate C: MyAcademic sync.** Direction, scope, conflict rule and account linking.
Until then, only the consent flag and the read-only export stub in spec 05 are built.

## Technical decisions (verified in a throwaway copy of this repo, 2026-10-25)
1. DRF on top of Django with PyMongo works without `django.contrib.auth` or a SQL
   database, as long as `UNAUTHENTICATED_USER` is `None` and the auth class returns a
   principal object with `is_authenticated = True`. Tested: 401 without a token,
   200 with one, public views see `request.user is None`.
2. drf-spectacular generates a schema; it warns for any custom auth class without an
   `OpenApiAuthenticationExtension` and for any APIView without declared serializers.
   CI runs `spectacular --validate --fail-on-warn` to keep the docs complete.
3. The shared profile schema v1.0 is valid Draft 2020-12. Eshan's example record passes,
   a minimal profile with empty arrays passes, and bad emails, URIs, dates and unknown
   fields are rejected with field paths. Format checks need `jsonschema[format-nongpl]`.
4. Django's `make_password` and `check_password` with Argon2 work without the auth app
   (needed only for the self-managed auth option).

## Data written to MongoDB by this backend

| Collection | Holds | Spec |
|---|---|---|
| users | email, role, auth provider and subject | 01, 04 |
| companies | employer organisations and their member user ids | 02 |
| jobs | postings with skills (required or optional) and openings | 02 |
| profiles | candidate profiles shaped like the shared schema | 03 |
| resumes | file metadata, storage key, extracted text | 03 |
| events | outbox events for other services (job published, resume uploaded, profile updated) | 01 to 03 |

Other services write their own collections, which this backend only reads (spec 05).

## How to run each spec in Kiro
1. Copy `.kiro/`, `docs/` and `backend/contracts/` into the repo root.
2. Open the spec's `tasks.md` in Kiro and run tasks one at a time, in order.
3. After each task: `pytest` and `ruff check` must pass before the next one.
4. One branch and pull request per spec; Eshan reviews anything touching CI or deployment.

## Housekeeping to raise with the team
- The repo's 2026-09-16 team notes assign "portal, API, database, allocation engine and
  deployment" to Eshan. Update the notes and the Jira board to show the backend API is yours.
- Domain: the deploy workflow and the Sep 16 summary use `careers.myacademic.org`,
  Eshan's auth emails use `careers.myacademic.dev`. This plan uses `.org` (what is deployed).
