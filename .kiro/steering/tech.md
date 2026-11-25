---
inclusion: always
---

# Tech stack and conventions

## Fixed by the advisor and team (2026-09-09 and 2026-09-16)
- Python 3.12, Django 5.x, MongoDB accessed through **PyMongo directly** (no Django ORM,
  no MongoDB Django backend, no MongoEngine). Do not add `DATABASES` usage or migrations.
- MongoDB: Atlas free tier (shared team credentials) for dev; local MongoDB 8.0 in Docker for tests.
- React + Vite frontend (separate folder, not this backend's concern).
- GitHub Actions deploys to one AWS EC2 t3.micro behind nginx.

## Added for the backend (verified working with this repo on 2026-10-25)
- djangorestframework (APIView + plain `serializers.Serializer`; no ModelSerializer).
- drf-spectacular for the OpenAPI 3 schema and Swagger UI.
- jsonschema[format-nongpl] (Draft 2020-12 + FormatChecker) for the shared profile contract.
- pytest + pytest-django; ruff for lint and format.
- pypdf and python-docx for resume text extraction; boto3 only when S3 is enabled.
- PyJWT and argon2-cffi only if the auth spec needs them.

Verified versions (2026-10-25): Django 5.2, DRF 3.18, drf-spectacular 0.30,
jsonschema 4.26, PyMongo 4.19, pytest-django 4.14.

## DRF without django.contrib.auth (required settings)
Django's auth app is not installed and there is no SQL database, so:
- `REST_FRAMEWORK["UNAUTHENTICATED_USER"] = None` (anonymous `request.user` is `None`).
- Authentication classes return a `Principal` dataclass with `is_authenticated = True`.
- Every custom authentication class needs a drf-spectacular `OpenApiAuthenticationExtension`.
- Every view declares its request and response serializers with `@extend_schema`,
  so `manage.py spectacular --validate --fail-on-warn` passes.

## API conventions
- Base path `/api/v1/`. Keep `/api/health/` for existing checks.
- JSON field names: snake_case in careers APIs. One exception: the `/api/v1/profiles/`
  endpoints use the camelCase names of the shared profile contract
  (`backend/contracts/shared-user-profile.v1.schema.json`), because their body is that contract.
- IDs: MongoDB ObjectId as a 24-char hex string in field `id`. Never expose `_id`.
  An invalid id string returns 404, not 500.
- Timestamps: timezone-aware UTC, stored as BSON dates, returned as ISO 8601 with `Z`.
- Lists: `?limit=` (default 20, max 100) and `?offset=`; response
  `{"items": [...], "total": n, "limit": l, "offset": o}`.
- Errors, always: `{"error": {"code": "snake_case_code", "message": "...", "details": {...}}}`.
  Status codes: 400 validation, 401 unauthenticated, 403 forbidden, 404 not found
  (also for resources the caller may not see), 409 conflict or invalid state change,
  413 file too large, 415 unsupported file type, 422 profile incomplete for export.

## Code rules
- Views never call PyMongo directly. They call repository functions in `api/repositories/`.
- Each repository function takes the database handle from `api.mongo.get_database()`.
- Every collection's indexes live in `api/indexes.py` and are created by
  `python manage.py ensure_indexes` (idempotent).
- Secrets only from environment variables (see `.env.example`). Never commit `.env`.
- Write the test first for every endpoint: happy path, auth failure, permission failure,
  validation failure, not found.
