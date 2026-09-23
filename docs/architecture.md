# Sahakari — Phase 0: Architecture & Requirements

Status: **Baseline (Phase 0 complete)**
Repository: existing Django modular monolith at repo root (not a greenfield build).

---

## 1. Objective & Scope

Production-oriented cooperative financial management system ("Sahakari") built as a
**modular monolith**: a single Django project, but with hard module boundaries so any
module can later be extracted into a microservice without a rewrite.

- Money is never modelled as `account.balance += x`. All money movement flows
  `Transaction -> Journal -> LedgerEntries -> AccountBalance`.
- Every journal must be balanced (`SUM(debits) == SUM(credits)`), enforced at DB + app level.
- Financial operations are explicit application/service functions. Serializers, views,
  `model.save()`, and signals do not contain financial business logic.
- No premature microservices, no Kafka/RabbitMQ purely for appearance.

## 2. Current State vs Target

| Concern | Existing (ground truth) | Target decision |
|---|---|---|
| Project layout | `config/`, `apps/`, `manage.py` | Keep. Add `common/`-style shared code inside `apps/core` (already exists) instead of a duplicated `common/` package. |
| Settings | `base.py`, `local.py`, `production.py` | Rename/add `development.py` + `testing.py` as thin wrappers so CI and prod reads are explicit. `base.py` stays the source of truth. |
| Identity | `apps/identity` (User, Member) | User/Role/Permission/auth stay in `identity`. `Member` moves to `apps/members` in the membership phase (never accept a silent split now). |
| Members | Currently inside `identity` | New `apps/members` module owning `Member`, `MemberContact`, `MemberAddress`, `MemberDocument`. Phase 5 performs the migration. |
| Shared foundation | `apps/core`: soft-delete, permissions, constants, exceptions hook | `apps/core` is the shared/`common` module: base models, managers, query sets, permissions, constants, domain exceptions, utility services. |
| Auth | JWT (SimpleJWT) + Django Groups RBAC | Keep. Extend to role catalogue + service-level authorization. |

Decision: **`apps/core` is the `common/` layer.** Renaming a working, tested package for
aesthetic overlap with a spec costs more than it returns. Documented divergence.

## 3. Technology Baseline

- Python, Django, DRF, PostgreSQL (NUMERIC for money — never float).
- Redis + Celery in a later phase for async only (notifications, report generation).
- OpenAPI/Swagger (drf-spectacular) in the API-docs phase.
- Docker Compose (Django + PostgreSQL + Redis + Nginx) for dev; Gunicorn + Nginx in prod.
- pytest for tests (existing Django `TestCase` stays for auth-centric suites where appropriate).
- GitHub Actions CI/CD (lint -> format -> static -> unit -> integration -> security ->
  build -> migration validation -> deploy -> health -> rollback).

## 4. Guiding Financial Principle (non-negotiable)

```
Transaction (intent, state, idempotency)
    → Journal (balanced double-entry document)
    → LedgerEntry[] (one row per debit/credit; never both in one row)
    → AccountBalance (cached, derived from posted ledger)
```

Invariants (DB-level via check constraints, app-level via service guards):
1. A ledger entry carries either `debit > 0` XOR `credit > 0`, never both, never zero.
2. `SUM(debit) == SUM(credit)` for every journal.
3. Posted records are immutable. Corrections are reversal + re-posting, never UPDATE/DELETE.
4. Balance changes only inside an atomic block that locks the involved
   AccountBalance rows with `select_for_update()`.

## 5. Module Map & Data Ownership

Each module owns its models; cross-module reads go through that module's services only.

| Module (app) | Owns | Notes |
|---|---|---|
| `apps/core` | shared base models, managers, query sets, permissions, constants, exceptions | No business data; dependency-free leaf used by all. |
| `apps/organization` | Organization, Branch, Department, Employee | Tenant/org context. Phase 4. |
| `apps/identity` | User, Role (Django Group), Permission, auth, login lockout | AuthN/AuthZ. |
| `apps/members` | Member, MemberContact, MemberAddress, MemberDocument | KYC/identity-of-member. Phase 5 (extracted from identity). |
| `apps/accounts` | AccountType, Account, AccountBalance | Chart of accounts + balances. |
| `apps/savings` | SavingsProduct, SavingsAccount, interest config/calc | Uses accounts/ledger for posting. |
| `apps/transactions` | Transaction (state, type, channel, idempotency), deposit/withdraw/transfer/reversal services | The money engine. |
| `apps/ledger` | Journal, LedgerEntry, reconciliation | Double-entry book of record. |
| `apps/loans` | LoanProduct, LoanApplication, Loan, LoanSchedule, LoanRepayment | Uses members + ledger. |
| `apps/approvals` | Approval, workflow | AI for loans, disbursements, high-value ops. |
| `apps/audit` | AuditLog | Append-only. |
| `apps/notifications` | Notification, template, delivery status | Async later. |
| `apps/reports` | Report defs/views over other modules' services | Read-only. |

## 6. Dependency Rules (must stay acyclic)

```
core
  ↑
organization → identity → members
                    ↑
              accounts ← savings
                  ↑
            transactions ← ledger (writes ledger, never vice-versa)
                  ↑
               loans
              ↑   ↑
      approvals  notifications
              ↑
             audit (depends on nothing; others write to it via API)
              ↑
           reports
```

- `apps/ledger` never imports `apps/transactions`. Transactions call ledger services.
- `apps/members` never imports `apps/identity` models directly for writes; it may reference
  a `user` FK for authentication linkage via identity services.
- Enforcement will be a CI lint rule (import linter) once the module set is stable.

## 7. Financial Engine Design (preview; detailed in Phases 6–8)

- **Money type:** `Decimal`, DB `NUMERIC(20,2)` (configurable scale), validation helper
  rejects floats and rounds half-up.
- **Transaction states** (valid transitions only, service-enforced + DB check):
  `INITIATED → PENDING → AUTHORIZED → PROCESSING → POSTED`; failure → `FAILED`;
  explicit `CANCELLED`; posted corrections created as `REVERSED` parent + new transaction.
- **Idempotency:** `IdempotencyKey (varchar, unique per transaction classify)` +
  `(client_key, idempotency_key)` DB-unique; stored request hash + stored response;
  retry returns stored result. Implemented from Phase 7.
- **Concurrency:** money ops open `transaction.atomic()`, lock all affected `AccountBalance`
  rows with `select_for_update()` in deterministic order (sorted sort key) to avoid deadlock,
  validate sufficiency, post ledger, update balances, commit. Race-safe by construction.
- **AccountBalance** is a cached aggregate; its `available_balance` may carry a
  `CHECK (available_balance >= 0)` where product policy forbids negative balances.

## 8. Authorization Model

- **RBAC** via Django Groups as roles. Catalogue (Django Permission records), e.g.
  super_admin, admin, branch_manager, loan_officer, account_officer, cashier, auditor, member.
- DRF default `IsAuthenticated`; sensitive endpoints use object-level + service-level checks.
- Permissions are checked on the backend only; UI state is never trusted.

## 9. Audit & Observability

- `AuditLog` in `apps/audit`: actor, action, entity/entity_id, old/new value, IP, request id,
  timestamp. Append-only: no update/delete for normal users; DB trigger or app-level guard.
- Request-ID middleware on all endpoints; structured JSON logging; health/readiness endpoints
  (DB + Redis) in the observability phase; Prometheus/Grafana/Sentry-ready shape.

## 10. Events (synchronous today)

Domain action boundaries defined so later a broker can subscribe without redesign:
`MemberCreated`, `AccountOpened`, `DepositCompleted`, `WithdrawalCompleted`,
`TransferCompleted`, `LoanApproved`, `LoanDisbursed`, `LoanRepaymentCompleted`.

## 11. Future Service Extraction Candidates

| Candidate service | Owns | Publishes | Depends on |
|---|---|---|---|
| Identity | users, roles, auth | user events | — |
| Member | member/contact/address/doc | MemberCreated | identity (weak) |
| Account/Savings | accounts, balances, products | AccountOpened | member, ledger |
| Transaction/Ledger | transactions, journals, entries, balances | money-moved | accounts |
| Loan | loans, schedules, repayments | loan events | member, ledger |
| Notification | templates, delivery | — | any |
| Reporting | derived reads | — | all (read-only) |

Extraction only if load/metrics justify it. Balances must not be split across services
while consistency guarantees (ledger balance = source of truth) hold.

## 12. Phase Plan (mapped to phases 1–24 in the specification)

| Phase | Deliverable |
|---|---|
| 0 | **This document (done)** |
| 1 | Project bootstrap & settings split (development/testing), `.env.example`, CI skeleton |
| 2 | PostgreSQL foundations: Decimal money type, constraints, indexes, migrations hygiene — **done (Phase 2), see `docs/database.md`** |
| 3 | Identity & auth hardening (identity app + JWT config + role catalogue) |
| 4 | Organization & branches |
| 5 | Members extraction into `apps/members` + KYC documents |
| 6 | Accounts & savings (AccountType/Account/Balance, SavingsProduct) |
| 7 | Transaction engine (states, idempotency, deposit/withdraw/transfer/reversal) |
| 8 | Double-entry ledger (Journal/LedgerEntry + invariants + reconciliation) |
| 9 | Audit system (`apps/audit` + middleware + service hook) |
| 10 | Loan management (products, application, schedule, repayment) |
| 11 | Approval workflow (`apps/approvals`) |
| 12 | Notifications (synchronous now, Celery later) |
| 13 | Reporting |
| 14 | API documentation (drf-spectacular/OpenAPI) |
| 15 | Testing & quality hardening (concurrency, invariance, idempotency test suites) |
| 16 | Security hardening (headers, rate limits, lockout, upload validation) |
| 17 | Dockerization (Dockerfile, compose, Nginx) |
| 18 | CI/CD (GitHub Actions stages) |
| 19 | Production deployment strategy |
| 20 | Monitoring & observability |
| 21 | Backup & disaster recovery |
| 22 | Performance & scalability |
| 23 | Microservice extraction strategy |

## 13. Acceptance Criteria for Phase 0

- [x] Module map + data ownership defined.
- [x] Dependency graph defined and acyclic.
- [x] Shared "common" location decided (`apps/core`).
- [x] Money/ledger invariants documented (enforcement details in Phases 6–8).
- [x] Divergences from the requested structure are explicit and justified.
- [x] Phase plan committed to `docs/architecture.md`.