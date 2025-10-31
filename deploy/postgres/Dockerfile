FROM postgres:17.0-bookworm

COPY deploy/postgres/conf/postgresql.conf /etc/postgresql/postgresql.conf
COPY deploy/postgres/conf/pg_hba.conf /etc/postgresql/pg_hba.conf

COPY deploy/postgres/init/init-user-db.sh /docker-entrypoint-initdb.d/init-user-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-user-db.sh

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
