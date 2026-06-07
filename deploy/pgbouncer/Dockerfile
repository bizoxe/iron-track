FROM alpine:3.21.5

RUN apk update && \
    apk add --no-cache pgbouncer postgresql-client su-exec gettext && \
    rm -rf /var/cache/apk/* && \
    adduser -D -h /etc/pgbouncer pgbouncer && \
    mkdir -p /var/lib/pgbouncer && \
    chown pgbouncer:pgbouncer /var/lib/pgbouncer

WORKDIR /etc/pgbouncer

COPY deploy/pgbouncer/conf/pgbouncer.ini.template ./pgbouncer.ini.template
COPY deploy/pgbouncer/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]