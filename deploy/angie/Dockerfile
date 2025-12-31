FROM docker.angie.software/angie:1.11.0-debian

RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

RUN rm -f /etc/angie/conf.d/*.conf

RUN mkdir -p /etc/angie/templates /etc/angie/snippets /etc/angie/conf.d

COPY deploy/angie/snippets/ /etc/angie/snippets/

COPY deploy/angie/templates/ /etc/angie/templates/

COPY deploy/angie/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
