#!/bin/sh
set -e

DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_USER_PASSWORD=${DB_USER_PASSWORD}
PGBOUNCER_POSTGRES_PORT=${PGBOUNCER_POSTGRES_PORT}
PGBOUNCER_ADMIN_USER=${PGBOUNCER_ADMIN_USER}
PGBOUNCER_MONITOR_USER=${PGBOUNCER_MONITOR_USER}

export DB_HOST DB_NAME DB_USER DB_USER_PASSWORD PGBOUNCER_POSTGRES_PORT PGBOUNCER_ADMIN_USER PGBOUNCER_MONITOR_USER

/usr/bin/envsubst </etc/pgbouncer/pgbouncer.ini.template >/etc/pgbouncer/pgbouncer.ini

chmod 600 /etc/pgbouncer/pgbouncer.ini

echo "PgBouncer configuration generated successfully ..."

echo "Starting PgBouncer ..."

exec su-exec pgbouncer pgbouncer /etc/pgbouncer/pgbouncer.ini
