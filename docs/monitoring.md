# Monitoring & Observability

## Health probe

`GET /api/health/` (no auth) returns:

```json
{"status": "ok", "database": "ok", "environment": "production"}
```

200 when the database is reachable, 503 otherwise. Use this for:
- container/LB readiness & liveness checks
- uptime monitors

## Logging

`config/exceptions.custom_exception_handler` logs every unhandled exception
with the full traceback to the `apps` logger. Configure log sinks via the
standard Django `LOGGING` in the deployment layer (e.g. JSON to stdout for
CloudWatch/Stackdriver, or syslog). Never leak internals to clients: responses
always return a generic `Internal server error.` (full detail only when DEBUG).

## Audit trail

Monetarily relevant events are mirrored into `apps.audit.AuditLog`:
- every finalised transaction (posted / reversed)
- reviewable via `GET /api/audit-logs/` (staff only)

Use AuditLog as the source of truth for compliance questions; it is append-only.

## Metrics to watch

| Metric                  | Source                                |
|-------------------------|---------------------------------------|
| Unsuccessful auth       | token endpoint 401s                   |
| Reversal rate           | `AuditLog` action=reverse             |
| Posting failures        | `Transaction.status=failed`           |
| Journal imbalance       | `docs/database.md` reconciliation job |
| Loan arrears            | `GET /api/reports/loan-book/`         |

## Suggested alerts

- Health check failing for > 2 minutes.
- > 5% of transactions reversed in a day.
- `Transaction.status=failed` count spike.
- `AccountBalance.updated_at` older than expected for active accounts
  (indicates the posting pipeline stalled).