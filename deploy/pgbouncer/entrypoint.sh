#!/bin/sh
set -e

export DB_HOST DB_NAME DB_USER DB_USER_PASSWORD PGBOUNCER_POSTGRES_PORT PGBOUNCER_ADMIN_USER PGBOUNCER_MONITOR_USER

/usr/bin/envsubst < /etc/pgbouncer/pgbouncer.ini.template > /var/lib/pgbouncer/pgbouncer.ini

chown pgbouncer:pgbouncer /var/lib/pgbouncer/pgbouncer.ini
chmod 600 /var/lib/pgbouncer/pgbouncer.ini

if [ ! -f /etc/pgbouncer/userlist.txt ]; then
    echo "ERROR: /etc/pgbouncer/userlist.txt not found!"
    exit 1
fi

echo "PgBouncer configuration generated successfully ..."

echo "Starting PgBouncer ..."

exec su-exec pgbouncer pgbouncer /var/lib/pgbouncer/pgbouncer.ini
