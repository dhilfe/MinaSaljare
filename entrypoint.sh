#!/usr/bin/env sh
set -eu

wait_for_tcp() {
  host="$1"
  port="$2"

  i=0
  while ! python -c "import socket; s=socket.socket(); s.settimeout(1.0); s.connect(('$host', int('$port'))); s.close()" >/dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge 60 ]; then
      echo "Timed out waiting for $host:$port" >&2
      exit 1
    fi
    sleep 1
  done
}

if [ -n "${POSTGRES_DB:-}" ]; then
  wait_for_tcp "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"
fi

python manage.py migrate --noinput

exec gunicorn salesapp.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${WEB_CONCURRENCY:-2} \
  --threads ${WEB_THREADS:-2} \
  --timeout ${WEB_TIMEOUT:-60}
