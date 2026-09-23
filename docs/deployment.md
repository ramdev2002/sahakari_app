# Production Deployment

## Prerequisites

- PostgreSQL 16+ (managed or self-hosted)
- Linux VM / container platform
- HTTPS terminator (nginx, Caddy, or cloud LB)

## Configuration

Set the following environment variables (see `.env.example`):

| Variable               | Purpose                                    |
|------------------------|--------------------------------------------|
| `ENVIRONMENT`          | `production`                               |
| `DJANGO_SECRET_KEY`    | Long random secret (never commit)          |
| `ALLOWED_HOSTS`        | Comma-separated hostnames                  |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origin(s)                            |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s)                         |
| `DB_*`                 | PostgreSQL connection                      |
| `STATIC_ROOT`          | WhiteNoise static output dir               |

Production settings raise `ImproperlyConfigured` if `SECRET_KEY`/`ALLOWED_HOSTS` are missing, so a misconfiguration fails fast.

## Image build

```sh
docker build -t sahakari:latest .
```

The image runs `collectstatic` at build time and serves via gunicorn
(3 workers, worker recycling for memory hygiene).

## Deploy (docker compose)

Export the env vars above into the environment, then:

```sh
docker compose -f docker-compose.prod.yml up -d
```

Migrations are run manually or via a one-shot job:

```sh
docker compose run --rm web python manage.py migrate --noinput
docker compose run --rm web python manage.py ensure_default_roles
```

## Static files

Served by WhiteNoise from the app process (`CompressedManifestStaticFilesStorage`).
No separate static hosting required. Ensure `STATIC_ROOT` is writable.

## Restart policy & health

- gunicorn restarts workers after 1000 requests (`--max-requests`).
- Health probe: `GET /api/health/` returns 200 + `database: ok` when ready,
  503 when the DB is unreachable. Wire this into the LB/container healthcheck.

## Upgrading

1. `docker compose run --rm web python manage.py makemigrations --check --dry-run`
2. Backup DB (`docs/backup-and-dr.md`)
3. `docker compose run --rm web python manage.py migrate --noinput`
4. Deploy new image, then smoke-test `/api/health/`.

## Post-deploy checks

- `python manage.py check --deploy`
- Confirm HTTPS redirect, HSTS, and CORS origins.
- Verify `/api/docs/` (Swagger) and `/api/redoc/` load.