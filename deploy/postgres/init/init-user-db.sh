#!/bin/bash
set -e

echo "Initializing PostgreSQL users and database ..."

create_or_update_role() {
    local ROLE_NAME=$1
    local ROLE_PASSWORD=$2

    echo "Creating/checking role: '${ROLE_NAME}'..."

    psql -v ON_ERROR_STOP=1 --username postgres \
        -v role="$ROLE_NAME" \
        -v password="$ROLE_PASSWORD" <<-'EOSQL'
        SET password_encryption = 'scram-sha-256';

        SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role', :'password')
        WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'role')
        \gexec

        SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'role', :'password')
        WHERE EXISTS (SELECT FROM pg_roles WHERE rolname = :'role')
        \gexec
EOSQL
}

create_or_update_role "${DB_USER}" "${DB_USER_PASSWORD}"

create_or_update_role "${PGBOUNCER_ADMIN_USER}" "${PGBOUNCER_ADMIN_PASSWORD}"

create_or_update_role "${PGBOUNCER_MONITOR_USER}" "${PGBOUNCER_MONITOR_PASSWORD}"

echo "Creating/checking database: '${DB_NAME}'..."

DB_EXISTS=$(psql -U postgres -v dbname="$DB_NAME" -tA <<< "SELECT 1 FROM pg_database WHERE datname = :'dbname';")

if [ "$DB_EXISTS" != "1" ]; then
    createdb -U postgres -O "${DB_USER}" "${DB_NAME}"
    echo "Database '${DB_NAME}' created and owned by '${DB_USER}'"
else
    echo "Database '${DB_NAME}' already exists, skipping creation"
fi

psql -v ON_ERROR_STOP=1 --username postgres -d "${DB_NAME}" \
    -v db="$DB_NAME" \
    -v app_user="$DB_USER" \
    -v pgbouncer_admin="$PGBOUNCER_ADMIN_USER" <<-'EOSQL'
    GRANT CONNECT ON DATABASE :"db" TO :"app_user";
    GRANT CONNECT ON DATABASE :"db" TO :"pgbouncer_admin";

    GRANT TEMPORARY ON DATABASE :"db" TO :"app_user";

    GRANT CREATE, USAGE ON SCHEMA public TO :"app_user";

    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO :"app_user";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO :"app_user";

    ALTER DEFAULT PRIVILEGES FOR ROLE :"app_user" IN SCHEMA public
        GRANT ALL ON TABLES TO :"app_user";

    ALTER DEFAULT PRIVILEGES FOR ROLE :"app_user" IN SCHEMA public
        GRANT ALL ON SEQUENCES TO :"app_user";
EOSQL

psql -v ON_ERROR_STOP=1 --username postgres -d "${DB_NAME}" \
    -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

echo "PostgreSQL initialization successfully completed. Database ready for use."