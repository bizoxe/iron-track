#!/bin/bash
set -e

VARS_TO_SUBST=$(printf '${%s} ' $(env | cut -d= -f1 | grep -E '^(SSL_|SERVER_|ALLOWED_)'))

if [ -z "${SERVER_NAME:-}" ]; then
    echo "ERROR: SERVER_NAME / ALLOWED_* / SSL_* are not set." >&2
    echo "Start the stack with: docker compose -f docker-compose.yaml --env-file .env.docker up -d" >&2
    exit 1
fi

echo "Preparing Angie configuration ..."
echo "Substituting variables: $VARS_TO_SUBST"

envsubst "$VARS_TO_SUBST" < /etc/angie/templates/angie.conf.template > /etc/angie/angie.conf
envsubst "$VARS_TO_SUBST" < /etc/angie/templates/default.conf.template > /etc/angie/conf.d/default.conf

echo "Configuration ready ..."

exec angie -g "daemon off;"