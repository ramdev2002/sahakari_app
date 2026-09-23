# Database Foundations (Phase 2)

Decision record for the reusable storage/representation primitives that every
Sahakari financial module builds on.

## Money representation

- **Type:** one `MoneyField(models.DecimalField)` defined in `apps/core/money.py`.
  All money columns across the app use it — `NUMERIC(20, 2)` (`MONEY_MAX_DIGITS=20`,
  `MONEY_DECIMAL_PLACES=2`).
- **Never float.** Integer, string, and `Decimal` inputs are accepted; floats are
  converted via `str(value)` (never `Decimal(float)`), which avoids binary
  floating-point artifacts.
- **Rounding:** values are quantized to 2 decimals with `ROUND_HALF_UP`
  (`MONEY_ROUNDING`) at the conversion boundary via `to_money()`. Everything
  downstream is pre-rounded, so aggregation can never fabricate fractions of a
  cent.
- **Validation:** NaN/Infinity and non-numeric input raise `MoneyValidationError`
  (a `ValueError` subclass) at the boundary — bad money never enters the ledger.
  `to_money(x, allow_none=True)` supports nullable columns.

## Timestamps

- `TimestampedModel` (abstract, `apps/core/models.py`) provides `created_at`
  (`auto_now_add`) and `updated_at` (`auto_now`), stored as UTC-aware
  `timestamptz` under Django's `USE_TZ=True`.
- Applied to `Member` in this phase (`identity` migration `0004`).

## Soft-delete integrity (DB-enforced)

- `SoftDeleteModel` keeps `is_deleted` + `deleted_at`. Every soft-deletable
  table also carries the CHECK constraint `%(app_label)s_%(class)s_soft_delete_state`:

  ```
  (is_deleted = false AND deleted_at IS NULL) OR (is_deleted = true AND deleted_at IS NOT NULL)
  ```

- The constraint is created through the `soft_delete_state_constraint()` factory
  and declared explicitly on each concrete model. This is required because Django
  does **not** propagate `Meta.constraints` from abstract base classes to
  descendants (verified against Django 6.1 — child `_meta.constraints` stays
  empty). Constraint names use `%(app_label)s`/`%(class)s` so they are unique per
  app/model (Django `models.E032`).
- Added to `identity_user` and `identity_member` this phase (migration `0004`).

## Indexes

- `status` columns on `User` and `Member` are `db_index=True` — these are the
  dominant lookup/filter keys for identity records and the default manager
  already hides deleted rows.

## Concurrency (preview; fully built in the transaction phase)

- All money mutations will run inside `transaction.atomic()` using
  `select_for_update()` on the balances being changed, plus idempotency keys on
  writes. Optimistic concurrency via a `version` column is reserved for later
  phases if API-level conflicts justify it; this phase only standardizes
  timestamps and the money type.

## Migration workflow

- Migrations are hand-ordered to keep columns human-readable; never regenerate
  pre-existing migration files wholesale.
- CI enforces `makemigrations --check --dry-run`, so model drift is a CI failure.

## Tests

- `apps/core/tests/test_money.py` — conversion, rounding, quantization, and
  rejection of NaN/inf/None/non-numeric input; `MoneyField` precision/scale.
- `apps/core/tests/test_base_models.py` — constraint presence on `User`/`Member`,
  DB-level rejection of inconsistent soft-delete states, and timestamp behavior.