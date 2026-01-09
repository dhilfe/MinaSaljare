#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/backup.sql.gz.gpg" >&2
  exit 2
fi

backup_file="$1"

: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

: "${BACKUP_PASSPHRASE:?BACKUP_PASSPHRASE is required}"

export PGPASSWORD="$POSTGRES_PASSWORD"

# Decrypt -> gunzip -> restore via psql.
# Note: This overwrites data in the target DB based on the SQL content.

gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" -d "$backup_file" \
  | gunzip \
  | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "Restore completed from: $backup_file"