# Backup & Disaster Recovery

## Backup strategy

Production is PostgreSQL 16. Use physical or logical backups; logical
(`pg_dump`) is simplest and is what the daily script below uses.

Principles:
- Back up **daily** + before every schema migration.
- Store at least two generations off-box (object storage / NFS).
- Test restores quarterly; a backup that cannot be restored is not a backup.

## Daily backup script (`scripts/backup.sh`)

```sh
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
```

Remove back-ups older than 14 days:

```sh
find "$BACKUP_DIR" -name 'sahakari_*.dump' -mtime +14 -delete
```

Add a cron entry:

```cron
0 2 * * * /opt/sahakari/scripts/backup.sh && find /var/backups/sahakari -name 'sahakari_*.dump' -mtime +14 -delete
```

## Restore procedure

```sh
pg_restore --no-owner --no-privileges --dbname=sahakari /var/backups/sahakari/sahakari_<STAMP>.dump
```

For a full DR restore on a fresh host:
1. apply schema via migrations (`migrate --run-syncdb`), or
2. restore the dump which contains the whole schema and data.

After restore, run `python manage.py check --deploy` and confirm
`GET /api/health/` reports `database: ok`.

## RPO / RTO targets

- RPO: ≤ 1 day (daily backup + pre-migration backups)
- RTO: ≤ 2 hours with an automated restore playbook

Migrate to PITR (WAL archiving) if stricter RPO/RTO are required.