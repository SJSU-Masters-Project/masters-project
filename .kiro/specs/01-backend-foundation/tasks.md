# Implementation Plan

- [ ] 1. Dependencies, tooling and local MongoDB
  - Update `requirements.txt` and add `requirements-dev.txt` exactly as listed in design.md "Dependencies".
  - Add `backend/pytest.ini` and a ruff config (`backend/ruff.toml`: line length 100, target py312, rules E, F, I, B, UP).
  - Add `docker-compose.yml` at the repo root with a `mongo:8.0` service on 27017 and a named volume.
  - Rewrite `.env.example` with every variable from Requirement 9.1 plus `APP_VERSION`, with local-safe values (`DJANGO_DEBUG=true`, `CAREERS_DEV_AUTH=true`).
  - Done when `docker compose up -d mongo` and `pip install -r requirements.txt -r requirements-dev.txt` both succeed.
  - _Requirements: 9.1, 9.4, 10.2_

- [ ] 2. Test harness
  - Write `backend/tests/conftest.py` per design.md "Tests": per-session `careers_test_<hex>` database, dropped at the end; per-test cleanup; `api` client fixture; `as_user` helper.
  - Change `api/mongo.py` to create the client with `tz_aware=True`; keep `lru_cache` and the ping.
  - Add `tests/test_smoke.py` asserting the test database name starts with `careers_test_` and is empty at test start.
  - _Requirements: 10.1_

- [ ] 3. Settings and system checks
  - Rewrite `config/settings.py` per design.md "Settings": env helpers `env_bool` and `env_list`, `DEBUG` default false, DRF and spectacular settings, CORS origins list.
  - Add `api/checks.py` with `careers.E001` and `careers.E002`; register them in `ApiConfig.ready()`.
  - Tests: each check fires on the bad combination and is silent on the good one (call the check function directly with `override_settings`).
  - _Requirements: 5.3, 9.1, 9.2, 9.3_

- [ ] 4. Error envelope and JSON 404
  - Write `api/errors.py` with `ApiError` and `exception_handler` per design.md "Errors".
  - Add the catch-all `re_path(r"^.*$", not_found)` as the last route in `api/urls.py`.
  - Tests: validation error shape, 401 shape, 403 shape, unknown URL gives JSON 404, unhandled exception gives 500 `internal_error` without a trace (use a test-only view raising `RuntimeError`).
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 5. ID, time and pagination helpers
  - Write `api/ids.py`, `api/timeutils.py`, `api/pagination.py` per design.md "Helpers".
  - Unit tests: invalid id raises `NotFound`; `doc_to_api` converts `_id`, nested ObjectIds and datetimes; ISO output ends in `Z`; `limit` 0, 101 and negative `offset` are rejected; defaults are 20 and 0.
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Restructure views and health endpoints
  - Replace `api/views.py` with a `views/` package; move `health` to `views/health.py` as a DRF `APIView` with `AllowAny` and a response serializer.
  - Delete the placeholder `login` and the old `jobs` views and their routes (spec 02 adds real jobs).
  - Route health at `/api/health/` and `/api/v1/health/`.
  - Tests: 200 with Mongo up; 503 with Mongo down (patch `get_database` to raise); no `detail` when `DEBUG` is false.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.7_

- [ ] 7. Users repository and development authentication
  - Write `api/repositories/users.py` per design.md "Users collection", including the `DuplicateKeyError` retry.
  - Write `api/auth.py` with `Principal`, `DevBearerAuthentication` and the `DevBearerScheme` spectacular extension.
  - Add `GET /api/v1/me` (`views/me.py`) returning `id`, `email`, `role`, `created_at`.
  - Tests: first dev request creates the user; second reuses it; email is lowercased; role mismatch gives 401; no header gives 401 on `/me`; dev auth off gives 401 even with the header.
  - _Requirements: 5.1, 5.2, 5.4, 5.5, 5.6_

- [ ] 8. Role permissions
  - Write `api/permissions.py` per design.md "Permissions".
  - Tests with a test-only view per class: allowed role gets 200, other roles get 403 `forbidden`, anonymous gets 401.
  - _Requirements: 6.1, 6.2_

- [ ] 9. Index definitions and `ensure_indexes`
  - Write `api/indexes.py` with the `users` and `events` indexes from design.md.
  - Write `api/management/commands/ensure_indexes.py`.
  - Tests: running the command twice succeeds; `users` rejects a duplicate email; the `events` TTL index exists with 30 days.
  - _Requirements: 7.1, 7.2, 8.2_

- [ ] 10. Event outbox
  - Write `api/events.py` with `emit_event(type, entity_type, entity_id, payload=None)`.
  - Tests: one document inserted with all fields; payload larger than 2 KB is rejected with `ValueError` (keeps events small).
  - _Requirements: 8.1, 8.3_

- [ ] 11. OpenAPI schema and docs
  - Route `SpectacularAPIView` at `/api/v1/schema/` and `SpectacularSwaggerView` at `/api/v1/docs/`, both `AllowAny`.
  - Add `@extend_schema` with serializers to every view so far.
  - Test: `call_command("spectacular", "--validate", "--fail-on-warn", "--file", tmp_path/"s.yml")` succeeds; `/api/v1/schema/` returns 200.
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 12. Backend CI workflow
  - Add `.github/workflows/backend-ci.yml` per design.md "CI". No deploy steps.
  - Done when the workflow is green on the pull request for this spec.
  - _Requirements: 10.3, 10.4_

- [ ] 13. Documentation
  - Update `README.md` "Local setup": `docker compose up -d mongo`, install both requirement files, `python manage.py ensure_indexes`, `pytest`, dev-auth header format, and the docs URL `http://localhost:8000/api/v1/docs/`.
  - _Requirements: 1.3, 9.4_
