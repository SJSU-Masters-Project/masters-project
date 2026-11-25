---
inclusion: always
---

# Repository structure (backend)

Monorepo: github.com/SJSU-Masters-Project/masters-project

```
backend/
  manage.py
  config/
    settings.py            # env-driven; DRF + spectacular settings
    urls.py                # /api/ -> api.urls
    wsgi.py
  contracts/
    shared-user-profile.v1.schema.json    # sync contract (from Eshan, 2026-10-09)
    shared-user-profile.v1.example.json
  api/
    mongo.py               # get_database() (exists)
    indexes.py             # index definitions for every collection
    checks.py              # startup system checks (dev auth, secret key)
    timeutils.py           # utcnow(), to_iso()
    auth.py                # Principal, dev authentication, spectacular extensions
                           # (spec 04 adds auth_clerk.py or auth_local.py)
    permissions.py         # IsCandidate, IsEmployer, IsAdmin, object checks
    errors.py              # ApiError + custom DRF exception handler
    pagination.py          # limit/offset helpers
    ids.py                 # ObjectId parsing and serialization
    events.py              # outbox events for other services
    contracts.py           # load + validate the shared profile schema
    storage.py             # resume file storage (local, s3)
    text_extract.py        # PDF/DOCX -> text
    repositories/
      users.py  companies.py  jobs.py  profiles.py  resumes.py
    serializers/
      common.py  companies.py  jobs.py  profiles.py  resumes.py
    views/
      health.py  me.py  companies.py  jobs.py  profiles.py  resumes.py
    urls.py
    management/commands/ensure_indexes.py
  tests/
    conftest.py            # test database per session, auth header helpers
    test_*.py
requirements.txt           # runtime deps (root of repo, existing)
requirements-dev.txt       # pytest, ruff
docker-compose.yml         # local MongoDB 8.0 (and backend)
.github/workflows/backend-ci.yml
```

Existing code: keep `backend/api/mongo.py`. `backend/api/views.py` becomes the `views/`
package: health moves to `views/health.py`, the jobs placeholder is replaced by the jobs spec,
and the placeholder `auth/login/` endpoint is deleted (the frontend does not call it;
real auth comes from spec 04).
Do not touch `frontend/` or the existing frontend deploy workflows from backend tasks.
