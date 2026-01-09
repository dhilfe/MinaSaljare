FROM alpine:3.20

RUN apk add --no-cache \
    postgresql16-client \
    gnupg \
    gzip \
    tzdata

WORKDIR /app

COPY ops/backup/backup.sh /app/backup.sh
COPY ops/backup/restore.sh /app/restore.sh
COPY ops/backup/crontab /etc/crontabs/root

RUN chmod +x /app/backup.sh /app/restore.sh

VOLUME ["/backups"]

CMD ["crond", "-f", "-l", "8"]
