# Design: backend deployment

## What exists (repo, 2026-09-28)
- One EC2 t3.micro (1 GiB memory). nginx serves the built frontend from
  `/var/www/careers.myacademic.org` and runs as user `nginx`.
- GitHub secrets: `EC2_SSH_KEY`, `KNOWN_HOSTS`, `EC2_USER`, `EC2_HOST`.
- Two identical frontend workflows (`deploy.yml`, `deploy-frontend.yml`); removing one is
  Eshan's task from 2026-09-23. Do not edit them here.

## Layout on the instance
```
/opt/careers-api/
  releases/<sha>/          # extracted repo tree + .venv/
  current -> releases/<sha>
  bin/deploy.sh            # installed copy of deploy/backend/deploy.sh
/etc/careers-api/env       # 0640 root:careers
/var/lib/careers-api/resumes/   # RESUME_LOCAL_ROOT, 0750 careers:careers
/etc/systemd/system/careers-api.service
```

## systemd unit (`deploy/backend/careers-api.service`)
```ini
[Unit]
Description=Careers API (gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
User=careers
Group=careers
WorkingDirectory=/opt/careers-api/current/backend
EnvironmentFile=/etc/careers-api/env
ExecStart=/opt/careers-api/current/.venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 --workers 2 --timeout 30 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
ReadWritePaths=/var/lib/careers-api

[Install]
WantedBy=multi-user.target
```
Two workers fit in 1 GiB alongside nginx. Logs go to journald (`journalctl -u careers-api`).

## nginx (`deploy/backend/nginx-api.conf`, included in the existing server block)
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 6m;
    proxy_read_timeout 60s;
}
```
Eshan adds the `include` line to the server block once; deploys never edit nginx.

## Django production settings
- `ALLOWED_HOSTS=careers.myacademic.org`; `CORS_ALLOWED_ORIGINS` empty (same origin).
- If HTTPS is on (check with Eshan): `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`,
  `SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True`, `SECURE_HSTS_SECONDS` starting at 3600.
  `SECURE_SSL_REDIRECT` stays false: nginx handles redirects.
- Frontend build uses `VITE_API_URL=/api/v1`.

## Atlas
- Database `careers_prod`; user `careers_api_prod` with `readWrite@careers_prod` only.
- Network access: the instance's Elastic IP. Without an Elastic IP the public IP changes on
  stop/start; ask Prof. Dhar to attach one (free while attached to a running instance).
- The free tier's 512 MB storage is why resumes stay on disk (spec 03).

## Release script (`deploy/backend/deploy.sh <sha> <tarball>`)
```bash
set -euo pipefail
REL=/opt/careers-api/releases/$1
PREV=$(readlink -f /opt/careers-api/current || true)
mkdir -p "$REL" && tar -xzf "$2" -C "$REL"
python3.12 -m venv "$REL/.venv"
"$REL/.venv/bin/pip" install --no-cache-dir -r "$REL/requirements.lock"
cd "$REL/backend"
set -a; . /etc/careers-api/env; set +a
"$REL/.venv/bin/python" manage.py check --deploy --fail-level ERROR
"$REL/.venv/bin/python" manage.py ensure_indexes
switch_to() { ln -sfn "$1" /opt/careers-api/current.new && mv -T /opt/careers-api/current.new /opt/careers-api/current; }
switch_to "$REL"
sudo systemctl restart careers-api
ok=0
for i in $(seq 1 15); do
  if curl -fsS -o /dev/null http://127.0.0.1:8000/api/health/; then ok=1; break; fi
  sleep 2
done
if [ "$ok" -ne 1 ]; then
  echo "health check failed; rolling back" >&2
  if [ -n "$PREV" ]; then switch_to "$PREV"; sudo systemctl restart careers-api; fi
  exit 1
fi
ls -1dt /opt/careers-api/releases/* | tail -n +4 | xargs -r rm -rf
```
`mv -T` makes the symlink switch atomic. The explicit `ok` flag matters: a shell `for` loop
that runs out of attempts still exits with status 0, so `for ...; done || rollback` would
never roll back. The deploy user needs passwordless sudo for
`systemctl restart careers-api` only (one sudoers line). Python: check the OS with
`cat /etc/os-release`; use 3.12 to match CI, or pin CI to whatever version the instance has.

## Workflow (`.github/workflows/deploy-backend.yml`)
- `on: push` to `main`, paths from Requirement 5.1.
- `concurrency: {group: deploy-backend, cancel-in-progress: false}`.
- Job `test`: same steps as `backend-ci.yml` (call it with `workflow_call` to avoid copying).
- Job `deploy` (`needs: test`): `git archive --format=tar.gz -o release.tgz HEAD`; set up SSH
  exactly like the frontend workflow; `scp release.tgz` to `/tmp`; `ssh ... /opt/careers-api/bin/deploy.sh $GITHUB_SHA /tmp/release.tgz`.
- Job `smoke` (`needs: deploy`): the three `curl` checks of Requirement 7 against
  `https://careers.myacademic.org` (or `http://` if HTTPS is not set up).

## One-time setup (manual, with Eshan)
1. `useradd --system careers`; create the folders above with the owners shown; make
   `/opt/careers-api` owned by the deploy user (`$EC2_USER`) and add that user to the
   `careers` group, so the deploy script can write releases and read `/etc/careers-api/env`.
2. Install Python and create `/etc/careers-api/env` from `deploy/backend/env.example`.
3. Install the systemd unit, `systemctl enable careers-api`.
4. Add the nginx include and reload nginx.
5. Add the sudoers line for the deploy user.
6. Check free memory; if there is no swap, add a 1 GB swap file (pip installs can spike memory).

## Not covered (raise with the team)
- Backups of `/var/lib/careers-api/resumes`: none on a single instance. The S3 option from
  spec 03 fixes this once Prof. Dhar approves a bucket.
- Monitoring and alerts: none beyond the smoke test.
