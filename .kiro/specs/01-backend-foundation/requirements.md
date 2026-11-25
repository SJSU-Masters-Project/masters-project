# Requirements Document

## Introduction

Turn the existing Django + PyMongo scaffold in `backend/` into a tested API foundation that
specs 02 to 06 build on: DRF, OpenAPI docs, one error format, ID/time/pagination helpers,
a users collection with a development-only authentication method, role permissions,
index management, an outbox for events, a test harness on real MongoDB, and backend CI.
Real sign-in is out of scope (spec 04).

## Requirements

### Requirement 1: API framework and documentation

**User Story:** As a frontend developer on the team, I want a versioned API with generated
documentation, so that I can integrate without reading backend code.

#### Acceptance Criteria
1. THE SYSTEM SHALL serve all new endpoints under `/api/v1/`.
2. WHEN a client requests `GET /api/v1/schema/` THEN THE SYSTEM SHALL return an OpenAPI 3 document.
3. WHEN a client requests `GET /api/v1/docs/` THEN THE SYSTEM SHALL return a Swagger UI page for that schema.
4. WHEN `python manage.py spectacular --validate --fail-on-warn` runs THEN it SHALL exit with status 0.

### Requirement 2: Health checks

**User Story:** As the person deploying the backend, I want a health endpoint, so that CI
and nginx can tell whether the API and its database are up.

#### Acceptance Criteria
1. WHEN MongoDB answers a ping THEN `GET /api/health/` and `GET /api/v1/health/` SHALL return 200 with `{"status": "ok", "mongodb": "connected", "version": "<app version>"}`.
2. WHEN MongoDB does not answer within 1.5 s THEN both SHALL return 503 with `{"status": "degraded", "mongodb": "unavailable"}`.
3. WHILE `DEBUG` is false THE SYSTEM SHALL NOT include exception text in the health response.
4. THE health endpoints SHALL NOT require authentication.

### Requirement 3: Error format

**User Story:** As a client developer, I want every error in one shape, so that the
portal can handle errors in one place.

#### Acceptance Criteria
1. WHEN any `/api/` request fails THEN THE SYSTEM SHALL respond with `{"error": {"code", "message", "details"}}`.
2. WHEN request data fails validation THEN THE SYSTEM SHALL return 400 with code `validation_error` and field-level messages in `details`.
3. WHEN authentication is missing or invalid THEN THE SYSTEM SHALL return 401 with code `not_authenticated` or `authentication_failed`.
4. WHEN the caller lacks permission THEN THE SYSTEM SHALL return 403 with code `forbidden`.
5. WHEN a URL under `/api/` does not exist THEN THE SYSTEM SHALL return 404 JSON with code `not_found`, not an HTML page.
6. WHEN an unhandled exception occurs AND `DEBUG` is false THEN THE SYSTEM SHALL return 500 with code `internal_error` and no stack trace, and log the exception.

### Requirement 4: IDs, timestamps and pagination

**User Story:** As a developer, I want shared helpers for ids, times and paging, so that
every endpoint behaves the same way.

#### Acceptance Criteria
1. THE SYSTEM SHALL expose document ids as 24-character hex strings in a field named `id` and SHALL NOT expose `_id`.
2. WHEN a path id is not a valid ObjectId THEN THE SYSTEM SHALL return 404 with code `not_found`.
3. THE SYSTEM SHALL store timestamps as timezone-aware UTC and return them as ISO 8601 strings ending in `Z`.
4. WHEN a list endpoint receives `limit` and `offset` THEN THE SYSTEM SHALL apply them, defaulting to 20 and 0, and SHALL reject `limit` above 100 or below 1 and negative `offset` with 400.
5. THE list response SHALL be `{"items": [...], "total": <int>, "limit": <int>, "offset": <int>}`.

### Requirement 5: Users and development authentication

**User Story:** As the backend developer, I want a users collection and a safe stand-in for
sign-in, so that I can build role-protected endpoints before the auth decision.

#### Acceptance Criteria
1. THE SYSTEM SHALL keep users in a `users` collection with a unique lowercase `email`, a `role` of `candidate`, `employer` or `admin`, and an `auth` object holding `provider` and `subject`.
2. WHILE `CAREERS_DEV_AUTH` is true, WHEN a request carries `Authorization: Bearer dev:<email>:<role>` THEN THE SYSTEM SHALL authenticate it as that user, creating the user on first use.
3. IF `CAREERS_DEV_AUTH` is true AND `DEBUG` is false THEN THE SYSTEM SHALL fail its startup system check with an error.
4. WHEN a dev token names an existing email with a different role THEN THE SYSTEM SHALL return 401 with code `authentication_failed` and SHALL NOT change the stored role.
5. WHEN an authenticated user calls `GET /api/v1/me` THEN THE SYSTEM SHALL return `id`, `email`, `role` and `created_at`.
6. WHEN an unauthenticated client calls `GET /api/v1/me` THEN THE SYSTEM SHALL return 401.
7. THE SYSTEM SHALL remove the placeholder `POST /api/auth/login/` endpoint that returns a fixed token.

### Requirement 6: Role permissions

**User Story:** As a product owner, I want endpoints restricted by role, so that candidates
cannot act as employers and the reverse.

#### Acceptance Criteria
1. THE SYSTEM SHALL provide permission classes that allow only candidates, only employers, only admins, and employers or admins.
2. WHEN a user with the wrong role calls a protected endpoint THEN THE SYSTEM SHALL return 403 with code `forbidden`.

### Requirement 7: Indexes

**User Story:** As the backend developer, I want indexes defined in code, so that every
environment has the same ones.

#### Acceptance Criteria
1. THE SYSTEM SHALL define every collection's indexes in `api/indexes.py`.
2. WHEN `python manage.py ensure_indexes` runs THEN THE SYSTEM SHALL create missing indexes and SHALL succeed when run again with no changes.

### Requirement 8: Event outbox

**User Story:** As an owner of another project service, I want a record of changes the API
makes, so that my service can react without the API calling it directly.

#### Acceptance Criteria
1. WHEN application code calls `emit_event(type, entity_type, entity_id, payload)` THEN THE SYSTEM SHALL insert one document into `events` with those fields and `created_at`.
2. THE SYSTEM SHALL keep events for 30 days and then let MongoDB delete them automatically.
3. THE event payload SHALL hold ids and small metadata only, never file contents or full profiles.

### Requirement 9: Configuration

**User Story:** As the person deploying, I want all settings from environment variables, so
that the same code runs locally and on EC2.

#### Acceptance Criteria
1. THE SYSTEM SHALL read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `MONGODB_URI`, `MONGODB_DATABASE` and `CAREERS_DEV_AUTH` from the environment.
2. WHEN `DJANGO_DEBUG` is not set THEN THE SYSTEM SHALL run with `DEBUG` false.
3. IF `DEBUG` is false AND `DJANGO_SECRET_KEY` is unset or the development default THEN THE SYSTEM SHALL fail its startup system check.
4. THE `.env.example` file SHALL list every variable with a safe local value.

### Requirement 10: Tests and CI

**User Story:** As the backend owner, I want automated tests against real MongoDB on every
change, so that regressions are caught before deployment.

#### Acceptance Criteria
1. WHEN `pytest` runs THEN it SHALL use a fresh database named `careers_test_<random>` and drop it at the end of the session.
2. THE repository SHALL provide `docker-compose.yml` that starts MongoDB 8.0 on port 27017 for local development and tests.
3. WHEN a pull request or push to `main` changes `backend/**`, `requirements*.txt` or the CI workflow THEN GitHub Actions SHALL run ruff, `manage.py check`, the OpenAPI validation and pytest against a MongoDB 8.0 service.
4. THE CI workflow SHALL NOT deploy anything.
