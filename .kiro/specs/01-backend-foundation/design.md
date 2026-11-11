# Design: backend foundation

## Overview
Add DRF and drf-spectacular to the existing Django + PyMongo scaffold without adding the
Django ORM or `django.contrib.auth`. All cross-cutting behaviour (errors, ids, paging,
identity, permissions, indexes, events) lives in small modules under `backend/api/` so the
feature specs only add repositories, serializers and views.

## Settings (`config/settings.py`)
```python
DEBUG = env_bool("DJANGO_DEBUG", default=False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CAREERS_DEV_AUTH = env_bool("CAREERS_DEV_AUTH", default=False)
APP_VERSION = os.getenv("APP_VERSION", "dev")

INSTALLED_APPS = [
    "django.contrib.contenttypes", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "drf_spectacular", "api",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["api.auth.DevBearerAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "UNAUTHENTICATED_USER": None,          # required: django.contrib.auth is not installed
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "api.errors.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}
SPECTACULAR_SETTINGS = {"TITLE": "Careers API", "VERSION": APP_VERSION,
                        "SERVE_INCLUDE_SCHEMA": False, "COMPONENT_SPLIT_REQUEST": True}
```
`CORS_ALLOW_ALL_ORIGINS = DEBUG` is removed; origins come from the list.
Add `DJANGO_DEBUG=true` and `CAREERS_DEV_AUTH=true` to `.env.example` so local runs keep working.

System checks (`api/checks.py`, registered in `ApiConfig.ready()`):
- `careers.E001`: `CAREERS_DEV_AUTH` true while `DEBUG` false.
- `careers.E002`: `DEBUG` false and `SECRET_KEY` is unset or `"local-development-only"`.

Why the dev-auth gate is the setting, not `DEBUG`: pytest-django forces `DEBUG = False`
during tests, so the authentication class checks only `CAREERS_DEV_AUTH`, and the system
check (which runs on `runserver`, `check` and deploy) stops it reaching production.

## Errors (`api/errors.py`)
```python
class ApiError(APIException):          # raise ApiError(409, "invalid_state", "Job is closed")
    def __init__(self, status_code, code, message, details=None): ...
```
`exception_handler(exc, context)`:
1. Call DRF's default handler. If it returns a response, rewrap as
   `{"error": {"code", "message", "details"}}`:
   `ValidationError` → `validation_error` with field messages in `details`;
   `NotAuthenticated` → `not_authenticated`; `AuthenticationFailed` → `authentication_failed`;
   `PermissionDenied` → `forbidden`; `NotFound`/`Http404` → `not_found`;
   `ApiError` → its own code.
2. If DRF returns `None` (unhandled): log with `logger.exception`; when `DEBUG` is false return
   500 `internal_error`; when `DEBUG` is true return `None` so Django shows the trace.

Unknown `/api/` URLs: the last pattern in `api/urls.py` is
`re_path(r"^.*$", views.not_found)`, which returns the 404 envelope whatever `DEBUG` is.

## Helpers
- `api/ids.py`: `parse_object_id(value) -> ObjectId` raising `NotFound` for invalid strings;
  `doc_to_api(doc)` renames `_id` to `id` (str) and converts nested ObjectIds and datetimes.
- `api/timeutils.py`: `utcnow()` returns aware UTC with millisecond precision (BSON keeps ms);
  `to_iso(dt)` gives `2026-10-25T18:00:00.123Z`. PyMongo returns naive datetimes by default,
  so `get_database()` creates the client with `tz_aware=True`.
- `api/pagination.py`: `PageParams` serializer (`limit` 1..100 default 20, `offset` ≥ 0 default 0)
  and `page_response(items, total, params)`.

## Identity (`api/auth.py`)
```python
@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    role: str                 # "candidate" | "employer" | "admin"
    is_authenticated: bool = True
```
`DevBearerAuthentication.authenticate(request)`:
- Return `None` (anonymous) if `CAREERS_DEV_AUTH` is false or the header does not start with `Bearer dev:`.
- Parse `dev:<email>:<role>` with `rpartition(":")`; lowercase the email; validate role.
- `users.get_or_create_external(provider="dev", subject=email, email=email, role=role)`.
- If the stored role differs from the token role, raise `AuthenticationFailed`.
- `authenticate_header()` returns `"Bearer"` so DRF answers 401, not 403.

`DevBearerScheme(OpenApiAuthenticationExtension)` with `target_class = "api.auth.DevBearerAuthentication"`,
`name = "devBearer"`, security definition `{"type": "http", "scheme": "bearer"}`. Without
it drf-spectacular warns and CI fails.

Spec 04 adds the real authentication class next to this one; nothing else changes.

## Users collection
```json
{ "_id": ObjectId, "email": "jordan@example.com", "role": "candidate",
  "display_name": null, "auth": {"provider": "dev", "subject": "jordan@example.com"},
  "status": "active", "created_at": ISODate, "updated_at": ISODate }
```
Repository `api/repositories/users.py`: `get_by_id`, `get_by_email`,
`get_or_create_external(provider, subject, email, role)` (insert, on `DuplicateKeyError`
re-read: safe under concurrent first requests).

## Permissions (`api/permissions.py`)
`IsCandidate`, `IsEmployer`, `IsAdmin`, `IsEmployerOrAdmin`: each checks
`request.user is not None and request.user.role in {...}`; message code `forbidden`.

## Indexes (`api/indexes.py`)
```python
INDEXES = {
  "users":  [IndexModel([("email", 1)], unique=True, name="email_unique"),
             IndexModel([("auth.provider", 1), ("auth.subject", 1)], unique=True, name="auth_identity")],
  "events": [IndexModel([("created_at", 1)], expireAfterSeconds=30*24*3600, name="ttl_30d"),
             IndexModel([("type", 1), ("_id", 1)], name="type_id")],
}
```
Later specs append their collections to this dict. `ensure_indexes` calls
`create_indexes` per collection; MongoDB treats an identical existing index as a no-op.

## Events (`api/events.py`)
```json
{ "_id": ObjectId, "type": "job.published", "entity_type": "job",
  "entity_id": ObjectId, "payload": {"company_id": "..."}, "created_at": ISODate }
```
Consumers keep their own checkpoint (last processed `_id`) and query
`{"type": {"$in": [...]}, "_id": {"$gt": last}}`. The API never waits for consumers.
Event types used later: `job.published`, `job.updated`, `job.closed`, `resume.uploaded`,
`resume.deleted`, `profile.updated`.

## Health
`views/health.py` keeps the current behaviour, adds `version`, hides `detail` when `DEBUG` is
false, and is served at both `/api/health/` and `/api/v1/health/` with `AllowAny`.

## Tests (`backend/tests/`)
`conftest.py`:
- Session fixture: set `settings.MONGODB_DATABASE = f"careers_test_{uuid4().hex[:8]}"`,
  `get_database.cache_clear()`, run `ensure_indexes`, yield, drop the database.
- Autouse function fixture: `delete_many({})` on every collection after each test (keeps indexes).
- Fixture `api` = `rest_framework.test.APIClient()`; helper `as_user(api, email, role)` sets
  `HTTP_AUTHORIZATION=f"Bearer dev:{email}:{role}"`.
- `settings.CAREERS_DEV_AUTH = True` for the session.

`backend/pytest.ini`: `DJANGO_SETTINGS_MODULE = config.settings`, `pythonpath = .`, `testpaths = tests`.

## Local MongoDB (`docker-compose.yml`, repo root)
Service `mongo` (image `mongo:8.0`, port `27017:27017`, named volume `mongo-data`).
Local `.env`: `MONGODB_URI=mongodb://localhost:27017`. The shared Atlas cluster is for the
team's integration data, never for tests.

## CI (`.github/workflows/backend-ci.yml`)
Triggers: `pull_request` and `push` to `main` on paths `backend/**`, `requirements*.txt`,
`.github/workflows/backend-ci.yml`. Job on `ubuntu-latest` with service `mongo:8.0` (port 27017,
health check `mongosh --eval "db.adminCommand('ping')"`). Steps: checkout,
`actions/setup-python` 3.12 with pip cache, install `requirements.txt` and
`requirements-dev.txt`, `ruff check backend`, `ruff format --check backend`,
`python manage.py check`, `python manage.py spectacular --validate --fail-on-warn --file schema.yml`,
`pytest`. Env: `DJANGO_DEBUG=true`, `CAREERS_DEV_AUTH=true`, `DJANGO_SECRET_KEY=ci-only`,
`MONGODB_URI=mongodb://localhost:27017`.

## Dependencies
`requirements.txt` (runtime): `Django>=5.2,<6.0`, `djangorestframework>=3.16,<4.0`,
`drf-spectacular>=0.28,<1.0`, `django-cors-headers>=4.3,<5.0`, `pymongo>=4.6,<5.0`,
`python-dotenv>=1.0,<2.0`, `jsonschema[format-nongpl]>=4.23,<5.0`, `gunicorn>=22`.
After the first green CI run, freeze exact versions with `pip freeze` into `requirements.lock`
for deployment (spec 06).
`requirements-dev.txt`: `pytest>=8`, `pytest-django>=4.9`, `ruff>=0.6`.
