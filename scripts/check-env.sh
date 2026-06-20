#!/usr/bin/env bash
# Validate that .env exists and required variables are present (non-empty, not placeholder).
set -euo pipefail
ENV_FILE="${1:-.env}"
REQUIRED=(POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD REDIS_URL JWT_SECRET NEXT_PUBLIC_API_URL)

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found. Run 'make env' to create it from .env.example."; exit 1
fi

# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

missing=0
for v in "${REQUIRED[@]}"; do
  val="${!v:-}"
  if [ -z "$val" ] || [ "$val" = "change_me" ]; then
    echo "  MISSING/PLACEHOLDER: $v"; missing=1
  fi
done

if [ "$missing" -eq 0 ]; then
  echo "Environment looks good."
else
  echo "Fill in the variables above in $ENV_FILE."; exit 1
fi
