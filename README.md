# Sahakari — Cooperative Financial Management System

Modular Django monolith for cooperative/banking operations. API-first, PostgreSQL-backed,
double-entry accounting. Build phases are tracked in `docs/architecture.md`.

## Features

- **Identity & roles** — JWT auth, RBAC role catalogue, staff/officer permissions
- **Members** — member lifecycle with soft delete & status constraints
- **Organization** — cooperative, branches, departments
- **Money engine** — exact `NUMERIC(20,2)` arithmetic, transactional posting
- **Transactions** — deposit / withdrawal / transfer / reversal with idempotency,
  deterministic row locking against overspend and duplicate posting
- **Ledger** — immutable double-entry `Journal`/`LedgerEntry`, always balanced
- **Savings** — products and member savings accounts (incl. opening deposit)
- **Loans** — products, request → approve → disburse → repay lifecycle with
  interest-first repayment accounted in the ledger
- **Approvals** — role-gated approval workflow
- **Notifications** — per-user inbox fed by transaction signals
- **Audit** — append-only audit trail of money events
- **Reports** — trial balance, cash position, member savings, loan book
- **API docs** — Swagger UI + ReDoc via OpenAPI (drf-spectacular)

## Quick start (development)

```bash
# 1. Environment
cp .env.example .env           # then edit DB_* / DJANGO_SECRET_KEY as needed

# 2. Dependencies
python -m venv .venv
.venv\Scripts\activate         # Windows (POSIX: source .venv/bin/activate)
pip install -r requirements/development.txt

# 3. Database + migrations
python manage.py migrate
python manage.py ensure_default_roles   # create role groups
python manage.py createsuperuser

# 4. Run
python manage.py runserver
```

Or use Docker:

```bash
docker compose up --build        # web on :8000, PostgreSQL attached
```

## APIs

```text
POST /api/auth/token/                    # JWT access + refresh
POST /api/auth/token/refresh/            # rotate access token
GET  /api/health/                        # liveness probe (no auth)
GET  /api/docs/                          # Swagger UI
GET  /api/redoc/                         # ReDoc
GET  /api/schema/                        # OpenAPI schema (JSON/YAML)

/api/users/               identity        /api/loans/{id}/repay/
/api/members/             members         /api/loans/{id}/disburse/
/api/organizations/       organization    /api/savings-accounts/open/
/api/branches/            organization    /api/savings-accounts/
/api/departments/         organization    /api/account-balances/
/api/accounts/            accounts        /api/account-types/
/api/transactions/        transactions    /api/transactions/deposit/
/api/transactions/withdraw/               /api/transactions/transfer/
/api/transactions/{id}/reverse/           /api/journals/
/api/ledger-entries/      ledger          /api/audit-logs/
/api/approvals/           approvals       /api/approval-rules/
/api/notifications/       notifications   /api/notifications/read_all/
/api/loan-products/       loans           /api/loans/
/api/savings-products/    savings
/api/reports/trial-balance/   /api/reports/cash-position/
/api/reports/member-savings/  /api/reports/loan-book/
```

All money transactions accept an optional `idempotency_key`; re-submitting the
same key returns the original transaction without double-posting.

## Settings

Selected via `ENVIRONMENT` (or `DJANGO_ENVIRONMENT`):

| ENVIRONMENT | Settings module | Use |
|---|---|---|
| `development` (default) | `config.settings.development` | local dev |
| `testing` | `config.settings.testing` | tests / CI |
| `production` | `config.settings.production` | deployment |

Run tests with pytest (`config.settings.testing` is applied automatically):

```bash
pytest
```

Quality gates (also enforced in CI):

```bash
python -m ruff check .
python -m ruff format --check .
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate --file /tmp/schema.yml
```

## Deploying

See `docs/deployment.md` (Docker image, env requirements, migration, health
probes) and `docs/backup-and-dr.md`, `docs/monitoring.md`, `docs/performance.md`,
`docs/microservices.md` for production operations and future evolution.

## Project structure

See `docs/architecture.md` (Phase 0) for module boundaries, data ownership, the
double-entry ledger rule, and the phase plan.