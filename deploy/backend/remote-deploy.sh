#!/usr/bin/env bash
# Installs the careers API on the EC2 host and restarts it. Run as root by
# .github/workflows/deploy-backend.yml after it uploads the code to /tmp/careers-api and the
# production .env to /tmp/careers-api.env.
#
# Usage: sudo bash remote-deploy.sh <public-host>
#
# Nothing under /opt/careers/app changes until the new code passes Django's checks against the
# new .env, so a bad config or unreachable MongoDB leaves the running API untouched.
set -euo pipefail

PUBLIC_HOST=${1:?usage: remote-deploy.sh <public-host>}
STAGE=/tmp/careers-api
ENV_UPLOAD=/tmp/careers-api.env
ROOT=/opt/careers
APP=$ROOT/app
VENV=$ROOT/venv
DATA=$ROOT/data
SERVICE=careers-api
PYTHON=${PYTHON:-python3.12}

# The .env holds secrets; never leave a copy in /tmp, even when a step below fails.
trap 'rm -f "$ENV_UPLOAD" "$STAGE/.env"' EXIT

if ! command -v "$PYTHON" >/dev/null; then
  echo "$PYTHON is not installed on this host (Amazon Linux: sudo dnf install -y python3.12)." >&2
  exit 1
fi

# 1. Service account: reads the code and .env, owns uploaded resumes, nothing else.
if ! id careers >/dev/null 2>&1; then
  useradd --system --home-dir "$ROOT" --no-create-home --shell /sbin/nologin careers
fi
install -d -m 755 "$ROOT" "$APP"
install -d -m 750 -o careers -g careers "$DATA" "$DATA/resumes"

# 2. Dependencies (shared virtualenv, created on the first deploy).
if [[ ! -x $VENV/bin/python ]]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$STAGE/requirements.txt"

# 3. Check the new code against the new .env before touching the live copy. settings.py loads
#    the .env that sits next to backend/, so the staged copy is checked with the staged .env.
install -m 600 "$ENV_UPLOAD" "$STAGE/.env"
(
  cd "$STAGE/backend"
  "$VENV/bin/python" manage.py check --deploy
  "$VENV/bin/python" manage.py ensure_indexes
)

# 4. Swap in the new code and .env: root-owned, read-only to the service.
rsync -a --delete --exclude '__pycache__/' "$STAGE/" "$APP/"
chown -R root:root "$APP"
chmod -R go-w "$APP"
chown root:careers "$APP/.env"
chmod 640 "$APP/.env"
"$VENV/bin/python" -m compileall -q "$APP/backend"

# 5. (Re)install the systemd unit and restart.
install -m 644 "$APP/deploy/backend/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
systemctl daemon-reload
systemctl enable --quiet "$SERVICE"
systemctl restart "$SERVICE"

# 6. Wait for the API (and its MongoDB connection) to report healthy.
for _ in $(seq 1 20); do
  if body=$(curl -fsS --max-time 5 -H "Host: $PUBLIC_HOST" http://127.0.0.1:8000/api/health/); then
    echo "$SERVICE is healthy: $body"
    exit 0
  fi
  sleep 2
done
echo "$SERVICE did not become healthy. Recent logs:" >&2
journalctl -u "$SERVICE" -n 50 --no-pager >&2
exit 1
