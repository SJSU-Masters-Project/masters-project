# Requirements Document

> **Coordinate with Eshan before running.** He set up the EC2 instance, nginx and the frontend
> deploy workflow (repo notes 2026-09-16 and 2026-09-23). Tasks that change nginx or the
> instance need his agreement and, for AWS resources, Prof. Dhar's (the university is not
> paying for hosting).

## Introduction

Deploy the backend to the existing EC2 t3.micro that already serves the frontend at
`careers.myacademic.org`, behind the same nginx, so the portal calls `/api/v1/` on its own
origin. Deploys run from GitHub Actions only after the backend CI passes, switch releases
atomically and roll back automatically if the health check fails.

## Requirements

### Requirement 1: Process

**User Story:** As the backend owner, I want the API to run as a managed service, so that it restarts on failure and on reboot.

#### Acceptance Criteria
1. THE SYSTEM SHALL run under gunicorn with 2 workers bound to `127.0.0.1:8000`, as a systemd service `careers-api` running as a dedicated non-root user `careers`.
2. WHEN the process exits unexpectedly or the instance reboots THEN systemd SHALL start it again.
3. THE service SHALL read its configuration from `/etc/careers-api/env`, readable only by root and the `careers` group.

### Requirement 2: nginx routing

**User Story:** As a portal user, I want the site and its API on one domain, so that the browser needs no cross-origin setup.

#### Acceptance Criteria
1. WHEN a request path starts with `/api/` THEN nginx SHALL proxy it to `127.0.0.1:8000` with `Host`, `X-Forwarded-For` and `X-Forwarded-Proto` headers.
2. nginx SHALL accept request bodies up to 6 MB on `/api/`.
3. All other paths SHALL keep serving the frontend exactly as before.

### Requirement 3: Production configuration

**User Story:** As the person responsible for security, I want production settings locked down.

#### Acceptance Criteria
1. THE production environment SHALL set `DJANGO_DEBUG=false`, `CAREERS_DEV_AUTH=false`, a random `DJANGO_SECRET_KEY` of at least 50 characters, `DJANGO_ALLOWED_HOSTS=careers.myacademic.org`, and the auth secrets chosen in spec 04.
2. WHEN `python manage.py check --deploy` runs with production settings THEN it SHALL report no errors, and every warning left SHALL be listed with its reason in the README.
3. WHEN the site is served over HTTPS THEN Django SHALL trust `X-Forwarded-Proto` from nginx and mark cookies secure.

### Requirement 4: Database

**User Story:** As the backend owner, I want production data kept apart from development data.

#### Acceptance Criteria
1. THE production API SHALL use database `careers_prod` on the team's Atlas cluster through a database user that can read and write only that database.
2. THE Atlas network access list SHALL include the instance's public IP address.
3. WHEN a release is deployed THEN `python manage.py ensure_indexes` SHALL run before traffic switches to it.

### Requirement 5: Automated deploys

**User Story:** As the backend owner, I want every merge to `main` to deploy itself safely.

#### Acceptance Criteria
1. WHEN a push to `main` changes `backend/**`, `requirements*.txt`, `deploy/backend/**` or the deploy workflow THEN GitHub Actions SHALL run the backend tests and, only if they pass, deploy.
2. THE workflow SHALL use the existing repository secrets `EC2_SSH_KEY`, `KNOWN_HOSTS`, `EC2_USER` and `EC2_HOST`.
3. THE workflow SHALL never run two deploys at the same time.
4. THE deploy SHALL install exact dependency versions from `requirements.lock`.

### Requirement 6: Releases and rollback

**User Story:** As the backend owner, I want a broken release to undo itself.

#### Acceptance Criteria
1. THE deploy SHALL place each release in `/opt/careers-api/releases/<git sha>` and switch the `/opt/careers-api/current` symlink to it.
2. WHEN the health check at `http://127.0.0.1:8000/api/health/` does not return 200 within 30 seconds after the switch THEN the deploy SHALL point `current` back to the previous release, restart the service and fail the workflow.
3. THE deploy SHALL keep the 3 most recent releases and delete older ones.
4. Resume files SHALL live in `/var/lib/careers-api/resumes`, outside the release folders, so deploys never touch them.

### Requirement 7: Smoke test

**User Story:** As the team, we want proof after each deploy that the public site works.

#### Acceptance Criteria
1. AFTER a successful deploy THEN the workflow SHALL check through the public domain that `GET /api/health/` returns 200, `GET /api/v1/jobs` returns 200, and a request with `Authorization: Bearer dev:x@y.z:candidate` to `GET /api/v1/me` returns 401.
