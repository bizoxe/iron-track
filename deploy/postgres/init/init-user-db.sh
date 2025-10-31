#!/bin/bash
set -e

echo "Initializing PostgreSQL users and database ..."

create_or_update_role() {
	local ROLE_NAME=$1
	local ROLE_PASSWORD=$2

	echo "Creating/checking role: '${ROLE_NAME}'..."

	psql -v ON_ERROR_STOP=1 --username postgres <<-EOSQL
		DO
		\$\$
		BEGIN
		    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${ROLE_NAME}') THEN
		        CREATE ROLE ${ROLE_NAME} WITH LOGIN PASSWORD '${ROLE_PASSWORD}';
		        RAISE NOTICE 'Role ${ROLE_NAME} created.';
		    ELSE
		        ALTER ROLE ${ROLE_NAME} WITH PASSWORD '${ROLE_PASSWORD}';
		        RAISE NOTICE 'Role ${ROLE_NAME} already exists. Password updated.';
		    END IF;
		END
		\$\$;
	EOSQL
}

create_or_update_role "${DB_USER}" "${DB_USER_PASSWORD}"

create_or_update_role "${PGBOUNCER_ADMIN_USER}" "${PGBOUNCER_ADMIN_PASSWORD}"

create_or_update_role "${PGBOUNCER_MONITOR_USER}" "${PGBOUNCER_MONITOR_PASSWORD}"

echo "Creating/checking database: '${DB_NAME}'..."

DB_EXISTS=$(psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")

if [ "$DB_EXISTS" != "1" ]; then
	createdb -U postgres -O "${DB_USER}" "${DB_NAME}"
	echo "Database '${DB_NAME}' created and owned by '${DB_USER}'"
else
	echo "Database '${DB_NAME}' already exists, skipping creation"
fi

psql -v ON_ERROR_STOP=1 --username postgres -d "${DB_NAME}" <<-EOSQL
	    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER};
	    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${PGBOUNCER_ADMIN_USER};
	    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${PGBOUNCER_MONITOR_USER};

	    GRANT TEMPORARY ON DATABASE ${DB_NAME} TO ${DB_USER};

	    GRANT CREATE, USAGE ON SCHEMA public TO ${DB_USER};

	    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
	    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};

	    ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_USER} IN SCHEMA public
	        GRANT ALL ON TABLES TO ${DB_USER};

	    ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_USER} IN SCHEMA public
	        GRANT ALL ON SEQUENCES TO ${DB_USER};
EOSQL

echo "PostgreSQL users and database initialization successfully completed ..."
