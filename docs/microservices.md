# Microservice Strategy (future evolution)

The system is deliberately built as a **modular monolith**: a single deployable
with strict application boundaries (`apps.*`). This gives transaction safety,
simple ops, and low latency while keeping future extraction viable.

## Boundaries that already exist

- `apps.accounts` — chart of accounts and cached balances
- `apps.ledger` — the immutable double-entry book of record (`Journal`/`LedgerEntry`)
- `apps.transactions` — the posting engine (deposit/withdraw/transfer/reverse)
- `apps.savings`, `apps.loans` — products/lifecycles that *call* the engine
- `apps.audit`, `apps.notifications`, `apps.approvals` — cross-cutting concerns
- `apps.identity`, `apps.members`, `apps.organization` — identity & org data

Persistence is separate: `apps.members` already keeps its state in the
`identity_member` table, so table-level independence is retained even inside
one database.

## What makes a good extraction candidate

A service becomes a candidate when it has:
1. a stable public interface (our URLs/services already are),
2. its own data lifecycle,
3. no transactional dependency on the money engine.

`reports` and `notifications` are the strongest candidates: read-only
aggregates (query the DB, never drive money), and side-effect notifications
(already event-signal based). `audit` is a natural event stream.

## What must NEVER be separately deployed

The **posting engine** (`transactions` + `ledger` + `AccountBalance`) must
remain one deployment. Money postings require a single ACID boundary:
locks, idempotency, and balance updates are one transaction. Splitting them
introduces distributed-transaction hazard exactly where correctness matters.

## Extraction path (when needed)

1. Introduce an outbox table for `PostingEvent` created inside the posting
   transaction (atomic with the journal).
2. Emit events to a broker (Kafka/NATS) from the outbox; consumer keeps
   eventual-consistency for notifications/reports/audit-webhooks.
3. Lift `reports` (or `notifications`) onto its own process + schema, using
   account balances replicated via events.
4. Keep `members`/`identity` split until multi-tenant needs are proven.

## Rules to preserve

- Money amounts: always `to_money`/`MoneyField`; never float.
- All money writes stay inside a single `atomic()` with row locks.
- Idempotency keys travel with every business action.
- External calls out of the money service must be fire-and-forget (outbox),
  never part of the posting transaction.