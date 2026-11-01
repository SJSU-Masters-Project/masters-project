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

### Authentication

Careers uses [Clerk](https://clerk.com) for real sign-in. The API verifies Clerk session
tokens locally (RS256 against Clerk's JWKS) and never calls Clerk per request beyond
fetching and caching signing keys. The `Principal` interface (`user_id`, `email`, `role`) is
unchanged from spec 01, so feature endpoints are unaffected.

Careers uses a **Clerk application created for careers alone** — it does not share a Clerk
instance, user pool or session with MyAcademic. Sign-in only finds or creates the careers
`users` record; it never reads or writes MyAcademic.

#### Settings (environment variables)

| Variable | Meaning |
|---|---|
| `CLERK_ISSUER` | The Clerk instance's Frontend API URL (e.g. `https://your-app.clerk.accounts.dev`). |
| `CLERK_JWKS_URL` | JWKS endpoint. Leave blank to default to `<issuer>/.well-known/jwks.json`. |
| `CLERK_AUTHORIZED_PARTIES` | Comma-separated portal origins allowed in the token's `azp` claim (e.g. `http://localhost:5173`). |

#### Clerk dashboard setup (one-time handover)

1. Create a **new Clerk application for careers only** — do not reuse any MyAcademic Clerk
   instance, user pool or session.
2. Add a **custom session-token claim** named `email`, mapped to the user's primary email.
   Clerk does not include email in the session token by default, and the API reads the email
   from this claim (spec 04, Requirement 4.4).
3. Add every portal origin to `CLERK_AUTHORIZED_PARTIES` (the values Clerk puts in `azp`).
4. Copy the Frontend API URL into `CLERK_ISSUER`.

Claim names and verification steps were confirmed against Clerk's manual JWT verification
guide: <https://clerk.com/docs/guides/sessions/manual-jwt-verification>.

#### Choosing a role

A user signs in with no role (`role: null`). They pick one once:

```bash
curl -X POST http://localhost:8000/api/v1/me/role \
  -H "Authorization: Bearer <clerk-session-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"role": "candidate"}'   # or "employer"
```

A second attempt returns 409 `role_already_set`. A user with no role who calls an endpoint
that needs one gets 403 `role_required`. Only `python manage.py set_admin <email>` grants the
`admin` role; it cannot be chosen through the API.

#### Frontend sign-in flow (handover to the portal owner)

The React portal signs users in with Clerk's hosted components (sign-up, sign-in, sign-out
and password reset are all Clerk's — the API has no login endpoints). Before **every** API
request, call Clerk's `getToken()` and send the result as `Authorization: Bearer <token>`.
Session tokens are short-lived, so never cache one — fetch a fresh token per request.

### Development authentication

For local runs and tests only. While `CAREERS_DEV_AUTH=true` (never in production; a startup
system check forbids it with `DEBUG=false`), the `DevBearerAuthentication` class is appended
*after* Clerk. Send a bearer token shaped `dev:<email>:<role>`, where role is `candidate`,
`employer` or `admin`:

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
