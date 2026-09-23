# Performance

## Database

Money is `NUMERIC(20,2)` — exact decimal arithmetic, no float drift and no
rounding inconsistencies between reads and posts.

Hot paths carry indexes:
- `Transaction.status`, `Transaction.kind` (filtered lists) and
  `Transaction.idempotency_key` (idempotency lookups, unique).
- `AccountBalance.account` (unique, one row per account).
- `LedgerEntry.account` + `LedgerEntry.journal` for statement and trial-balance
  aggregation.
- `AuditLog(entity_type, entity_id)` composite index + `occurred_at`.
- `Member.status`, `User.status` for active-row filtering.

## Concurrency

Account balances are locked with `SELECT ... FOR UPDATE` in deterministic
(primary-key sorted) order inside the posting transaction. This prevents
deadlocks and makes concurrent deposit/withdraw/transfer safe. Idempotency
keys make client retries side-effect free.

## Query patterns

Viewsets use `select_related`/`prefetch_related` on expected N+1 hot spots:
`Transaction`, `SavingsAccount`, `Loan`, `AuditLog`. `reports` use the cached
`AccountBalance` table instead of scanning the ledger per request (the ledger
is only aggregated for the trial balance report).

## Caching

Currently the app avoids a cache layer by design: `AccountBalance` is the
cached aggregate and is updated transactionally with each journal. If reports
grow further, cache report JSON in Redis with a short TTL and a versioned
invalidation on posting.

## Bulk flows

`ensure_seed_accounts`, role seeding and the approval/notification signals are
idempotent, so cron-driven bulk import can run them repeatedly without
side effects. Bulk member/transaction import should reuse the same services
with unique idempotency keys.

## Scaling notes

- Read scaling: point replicas read `reports` traffic at the DB (read-only,
  small query surface).
- Write scaling: the modular-monolith keeps money writes single-node; splitting
  transaction domains is discussed in `docs/microservices.md`. Keep all money
  mutations inside one transactional boundary — never optimistic-update
  a balance across service boundaries.