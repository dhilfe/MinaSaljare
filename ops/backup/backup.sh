#!/usr/bin/env sh
set -eu

: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

: "${BACKUP_DIR:=/backups}"
: "${BACKUP_PASSPHRASE:?BACKUP_PASSPHRASE is required}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out_file="$BACKUP_DIR/${POSTGRES_DB}_${timestamp}.sql.gz.gpg"

mkdir -p "$BACKUP_DIR"

# Create SQL dump, gzip, then encrypt with gpg (symmetric).
# Using env var to avoid interactive prompt.
export PGPASSWORD="$POSTGRES_PASSWORD"

tmp_sql_gz="$BACKUP_DIR/.tmp_${POSTGRES_DB}_${timestamp}.sql.gz"

pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  --no-owner \
  --no-acl \
  "$POSTGRES_DB" \
  | gzip -c > "$tmp_sql_gz"

# Encrypt.
# shellcheck disable=SC2002
cat "$tmp_sql_gz" | gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" -c -o "$out_file"

rm -f "$tmp_sql_gz"

echo "Backup written: $out_file"