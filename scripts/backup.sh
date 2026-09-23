#!/usr/bin/env sh
set -euo pipefail
PGHOST="${DB_HOST:-localhost}"
PGPORT="${DB_PORT:-5432}"
PGUSER="${DB_USER:-postgres}"
PGDATABASE="${DB_NAME:-sahakari}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/sahakari}"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
pg_dump --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" --dbname="$PGDATABASE" \
  --format=custom --file="$BACKUP_DIR/sahakari_$STAMP.dump"
echo "Backup written: $BACKUP_DIR/sahakari_$STAMP.dump"