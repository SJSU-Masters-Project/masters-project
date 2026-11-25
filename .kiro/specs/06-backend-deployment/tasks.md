# Implementation Plan

Prerequisites: spec 01 merged (backend CI exists). Dev auth is always off in production, so
until spec 04 is done nobody can sign in there: only public endpoints (health, job search)
work. That is enough to prove the pipeline, so tasks 1 to 6 can run before spec 04.

- [ ] 1. Lock file and production settings
  - Generate `requirements.lock` with `pip freeze` from a clean venv built from `requirements.txt`; document how to regenerate it in README.
  - Add the HTTPS-dependent settings from design.md, driven by an env flag `DJANGO_BEHIND_HTTPS`.
  - Run `manage.py check --deploy` with production-like env; fix errors; list remaining warnings and reasons in README.
  - _Requirements: 3.1, 3.2, 3.3, 5.4_

- [ ] 2. Deployment files in the repo
  - Add `deploy/backend/careers-api.service`, `deploy/backend/nginx-api.conf`, `deploy/backend/deploy.sh`, `deploy/backend/env.example` (every production variable, no values) exactly as in design.md.
  - Run `shellcheck deploy/backend/deploy.sh` in CI.
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 6.1, 6.2, 6.3, 6.4_

- [ ] 3. Atlas production database
  - With the cluster owner: create `careers_prod` and user `careers_api_prod` (`readWrite@careers_prod`), add the instance IP (ask Prof. Dhar for an Elastic IP), test the connection string from the instance with `mongosh`.
  - _Requirements: 4.1, 4.2_

- [ ] 4. One-time instance setup (with Eshan)
  - Follow design.md "One-time setup" steps 1 to 6. Record what was done in `deploy/backend/README.md`.
  - Verify: `systemctl status careers-api` is active after a manual first release; `curl 127.0.0.1:8000/api/health/` returns 200; a reboot brings it back.
  - _Requirements: 1.1, 1.2, 1.3, 6.4_

- [ ] 5. Deploy workflow
  - Make `backend-ci.yml` callable (`on: workflow_call` in addition to its triggers).
  - Add `deploy-backend.yml` per design.md "Workflow" with the concurrency group.
  - Test the rollback once on purpose: push a commit whose health check fails (for example, a wrong `MONGODB_DATABASE` in a test branch deployed manually), confirm `current` points back and the workflow fails.
  - _Requirements: 4.3, 5.1, 5.2, 5.3, 6.2_

- [ ] 6. nginx route and smoke test
  - Eshan adds the include for `nginx-api.conf` and reloads nginx.
  - Add the `smoke` job; confirm all three checks pass on the public domain and the frontend still loads.
  - Tell the frontend owner to build with `VITE_API_URL=/api/v1`.
  - _Requirements: 2.1, 2.2, 2.3, 7.1_
