FROM alpine:latest

RUN apk update && \
    apk add --no-cache pgbouncer postgresql-client su-exec gettext && \
    rm -rf /var/cache/apk/*

RUN adduser -D -h /etc/pgbouncer pgbouncer

WORKDIR /etc/pgbouncer

COPY deploy/pgbouncer/conf/userlist.txt /etc/pgbouncer/userlist.txt
COPY deploy/pgbouncer/conf/pgbouncer.ini.template /etc/pgbouncer/pgbouncer.ini.template

RUN chown -R pgbouncer:pgbouncer /etc/pgbouncer && \
    chmod 600 /etc/pgbouncer/pgbouncer.ini.template /etc/pgbouncer/userlist.txt

COPY deploy/pgbouncer/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD []