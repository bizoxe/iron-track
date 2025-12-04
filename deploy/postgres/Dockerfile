FROM postgres:18-bookworm

COPY deploy/postgres/conf/postgresql.conf /tmp/conf/postgresql.conf
COPY deploy/postgres/conf/pg_hba.conf /tmp/conf/pg_hba.conf

COPY deploy/postgres/init/init-user-db.sh /docker-entrypoint-initdb.d/init-user-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-user-db.sh