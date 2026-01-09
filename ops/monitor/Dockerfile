FROM alpine:3.20

RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata

WORKDIR /app

COPY ops/monitor/monitor.sh /app/monitor.sh
COPY ops/monitor/crontab /etc/crontabs/root

RUN chmod +x /app/monitor.sh

CMD ["crond", "-f", "-l", "8"]
