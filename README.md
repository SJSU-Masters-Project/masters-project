# masters-project

SJSU Masters project — a two-sided job application portal for companies and students/job seekers.

## Structure

- `backend/` — Django API with a PyMongo connection layer (no Django ORM, no SQL database).
- `frontend/` — React + Vite portal interface with company and candidate entry points.
- `experiments/` — isolated prototypes and research spikes.

## Local setup

1. Copy `.env.example` to `.env` (the defaults are safe for local development:
   `DJANGO_DEBUG=true`, `CAREERS_DEV_AUTH=true`).
2. Start MongoDB 8.0: `docker compose up -d mongo`.
3. Install backend dependencies:
   `pip install -r requirements.txt -r requirements-dev.txt`.
4. Create the MongoDB indexes: `cd backend && python manage.py ensure_indexes`.
5. Run the tests: `cd backend && pytest`.
6. Start the API: `cd backend && python manage.py runserver`.
7. In another terminal, run `cd frontend && npm install && npm run dev`.

## API

- Base path: `/api/v1/`. The legacy health check stays at `/api/health/`.
- OpenAPI schema: `GET /api/v1/schema/`. Interactive docs (Swagger UI):
  <http://localhost:8000/api/v1/docs/>.
- Errors always use one shape: `{"error": {"code", "message", "details"}}`.
- Lists use `?limit=` (default 20, max 100) and `?offset=`, returning
  `{"items": [...], "total": n, "limit": l, "offset": o}`.

### Development authentication

Real sign-in is a later spec. While `CAREERS_DEV_AUTH=true` (never in production), send a
bearer token shaped `dev:<email>:<role>`, where role is `candidate`, `employer` or `admin`:

```bash
curl -H "Authorization: Bearer dev:jordan@example.com:candidate" \
  http://localhost:8000/api/v1/me
```

The user is created on first use. A token that reuses an email with a different role is
rejected (the stored role never changes).

### Jobs API

```bash
# Create a company (employer)
curl -X POST http://localhost:8000/api/v1/companies \
  -H "Authorization: Bearer dev:boss@acme.com:employer" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme", "location": "San Jose, CA"}'

# Create a job (draft)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer dev:boss@acme.com:employer" \
  -H "Content-Type: application/json" \
  -d '{"title":"Backend Intern","description":"'"$(printf 'x%.0s' {1..60})"'","location":"San Jose","work_mode":"hybrid","employment_type":"internship","openings":2,"skills":[{"name":"Python","required":true}]}'

# Publish it
curl -X POST http://localhost:8000/api/v1/jobs/<id>/publish \
  -H "Authorization: Bearer dev:boss@acme.com:employer"

# Browse open jobs (no auth required)
curl "http://localhost:8000/api/v1/jobs?q=python&work_mode=hybrid"
```

Job field mapping for the frontend: `company.name → company`, `employment_type → type`.
There is no `salary` field in the API.

### Profiles and resumes API

```bash
# Create or replace my profile (candidate). Body is the shared profile contract (camelCase).
curl -X PUT http://localhost:8000/api/v1/profiles/me \
  -H "Authorization: Bearer dev:jordan@example.com:candidate" \
  -H "Content-Type: application/json" \
  -d '{"personal":{"fullName":"Jordan Lee"},"career":{"skills":["Python"]},"jobPreferences":{"targetRoles":["SWE"],"employmentTypes":["full_time"],"workModes":["remote"]}}'

# Upload a resume (multipart)
curl -X POST http://localhost:8000/api/v1/resumes \
  -H "Authorization: Bearer dev:jordan@example.com:candidate" \
  -F file=@resume.pdf

# Export my profile in the shared contract shape
curl http://localhost:8000/api/v1/profiles/me/shared \
  -H "Authorization: Bearer dev:jordan@example.com:candidate"
```

The MongoDB integration uses PyMongo directly. See `docs/backend/IMPLEMENTATION_PLAN.md`
and `.kiro/specs/` for the full backend plan.
