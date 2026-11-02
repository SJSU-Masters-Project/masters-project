#!/usr/bin/env bash
# Builds the backend's production .env from GitHub Actions variables and secrets, failing
# with a clear message when a required value is missing or unsafe. Never prints a value.
#
# Usage: build-env.sh <output-file>   (inputs come from the environment; see deploy-backend.yml)
set -euo pipefail

out=${1:?usage: build-env.sh <output-file>}

CAREERS_HOST=${CAREERS_HOST:-}
CLERK_ISSUER=${CLERK_ISSUER:-}
CLERK_AUTHORIZED_PARTIES=${CLERK_AUTHORIZED_PARTIES:-}
MONGODB_DATABASE=${MONGODB_DATABASE:-career_portal}
RESUME_STORAGE=${RESUME_STORAGE:-local}
RESUME_S3_BUCKET=${RESUME_S3_BUCKET:-}
RESUME_S3_REGION=${RESUME_S3_REGION:-us-west-2}
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-}
MONGODB_URI=${MONGODB_URI:-}
APP_VERSION=${APP_VERSION:-unknown}

errors=0
err() {
  echo "::error::$*"
  errors=$((errors + 1))
}

# --- Validate -------------------------------------------------------------------------------

if [[ -z $CAREERS_HOST ]]; then
  err "Set the CAREERS_HOST repository variable (e.g. careers.myacademic.org)."
elif [[ ! $CAREERS_HOST =~ ^[A-Za-z0-9.-]+$ ]]; then
  err "CAREERS_HOST must be a bare hostname such as careers.myacademic.org (no https://, path or port)."
fi

if [[ -z $DJANGO_SECRET_KEY ]]; then
  err "Set the DJANGO_SECRET_KEY repository secret."
elif ((${#DJANGO_SECRET_KEY} < 50)); then
  err "DJANGO_SECRET_KEY must be at least 50 characters (python3 -c 'import secrets; print(secrets.token_urlsafe(50))')."
fi

case $MONGODB_URI in
  mongodb://* | mongodb+srv://*) ;;
  "") err "Set the MONGODB_URI repository secret." ;;
  *) err "MONGODB_URI must start with mongodb:// or mongodb+srv://." ;;
esac

# The API checks the token's "iss" claim against CLERK_ISSUER character for character.
if [[ -z $CLERK_ISSUER ]]; then
  err "Set the CLERK_ISSUER repository variable to the Clerk production instance's Frontend API URL (e.g. https://clerk.careers.myacademic.org)."
elif [[ $CLERK_ISSUER != https://* ]]; then
  err "CLERK_ISSUER must start with https://."
elif [[ $CLERK_ISSUER == */ ]]; then
  err "CLERK_ISSUER must not end with a slash; the token's iss claim has none, so every sign-in would fail."
elif [[ $CLERK_ISSUER == *.clerk.accounts.dev* ]]; then
  err "CLERK_ISSUER points at a Clerk development instance (*.clerk.accounts.dev). Use the production instance's Frontend API URL."
fi

# Origins allowed in the token's "azp" claim. Defaults to the site itself.
if [[ -z $CLERK_AUTHORIZED_PARTIES && -n $CAREERS_HOST ]]; then
  CLERK_AUTHORIZED_PARTIES="https://$CAREERS_HOST"
fi
if [[ -n $CLERK_AUTHORIZED_PARTIES ]]; then
  IFS=',' read -r -a parties <<<"$CLERK_AUTHORIZED_PARTIES"
  for party in "${parties[@]}"; do
    party=${party//[[:space:]]/}
    if [[ $party != https://* || $party == */ ]]; then
      err "CLERK_AUTHORIZED_PARTIES entries must be origins like https://careers.myacademic.org (https, no trailing slash)."
      break
    fi
  done
fi

case $RESUME_STORAGE in
  local) ;;
  s3) [[ -n $RESUME_S3_BUCKET ]] || err "RESUME_STORAGE is s3, so set the RESUME_S3_BUCKET repository variable." ;;
  *) err "RESUME_STORAGE must be local or s3." ;;
esac

# --- Write ----------------------------------------------------------------------------------

umask 077
: >"$out"

# Values are single-quoted for python-dotenv. It still expands ${...} inside single quotes and
# decodes backslash escapes, so values containing those (or quotes and newlines) are refused.
put() {
  local key=$1 value=$2
  case $value in
    *"'"* | *\\* | *\$\{* | *$'\n'*)
      err "$key contains a quote, backslash, '\${' or newline, which the .env file can't hold safely."
      return
      ;;
  esac
  printf "%s='%s'\n" "$key" "$value" >>"$out"
}

put DJANGO_DEBUG false
put CAREERS_DEV_AUTH false
put DJANGO_SECRET_KEY "$DJANGO_SECRET_KEY"
put DJANGO_ALLOWED_HOSTS "$CAREERS_HOST"
put CORS_ALLOWED_ORIGINS "https://$CAREERS_HOST"
put APP_VERSION "${APP_VERSION:0:12}"
# CLERK_JWKS_URL is left out on purpose: the API derives it from CLERK_ISSUER.
put CLERK_ISSUER "$CLERK_ISSUER"
put CLERK_AUTHORIZED_PARTIES "$CLERK_AUTHORIZED_PARTIES"
put MONGODB_URI "$MONGODB_URI"
put MONGODB_DATABASE "$MONGODB_DATABASE"
put RESUME_STORAGE "$RESUME_STORAGE"
# Uploaded resumes live outside the code directory so redeploys never touch them.
put RESUME_LOCAL_ROOT /opt/careers/data/resumes
if [[ $RESUME_STORAGE == s3 ]]; then
  put RESUME_S3_BUCKET "$RESUME_S3_BUCKET"
  put RESUME_S3_REGION "$RESUME_S3_REGION"
fi

if ((errors > 0)); then
  rm -f "$out"
  echo "Production .env not built: $errors problem(s) above."
  exit 1
fi
echo "Production .env built."
