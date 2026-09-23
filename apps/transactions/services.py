"""The transaction engine.

Guarantees:
* every business event posts a balanced double-entry journal
* account balances are locked in order (``select_for_update``) so concurrent
  requests cannot overspend or double-post
* ``idempotency_key`` makes retries safe: re-submitting the same key returns
  the original completed transaction
* reversals post opposite legs rather than mutating history
"""

import uuid
from decimal import Decimal

from django.db import IntegrityError
from django.db import transaction as db_transaction

from apps.accounts.services import get_default_cash_account, lock_balances
from apps.core.money import MoneyValidationError, to_money
from apps.ledger.services import post_journal

from .models import Transaction

TRANSACTION_ERROR_MESSAGES = {
    'amount_required': 'A positive amount is required.',
    'distinct_accounts': 'From and to accounts must differ.',
    'not_completed': 'Only completed transactions can be reversed.',
    'already_reversed': 'This transaction has already been reversed.',
    'no_journal': 'Transaction has no posted journal.',
    'account_mismatch': 'Ledger legs must reference expected accounts.',
    'zero_amount': 'Amount cannot be zero.',
}


class TransactionError(ValueError):
    pass


def _to_positive_money(value):
    try:
        amount = to_money(value)
    except MoneyValidationError as exc:
        raise TransactionError(str(exc)) from exc
    if amount <= 0:
        raise TransactionError(TRANSACTION_ERROR_MESSAGES['amount_required'])
    return amount


def _generate_reference():
    return f'TXN-{uuid.uuid4().hex[:12].upper()}'


def _create_transaction(
    *, kind, idempotency_key, branch=None, requested_by=None, memo='', source_channel='api'
):
    try:
        with db_transaction.atomic():
            return Transaction.objects.create(
                reference=_generate_reference(),
                kind=kind,
                status='initiated',
                idempotency_key=idempotency_key or None,
                branch=branch,
                requested_by=requested_by,
                memo=memo,
                source_channel=source_channel,
            )
    except IntegrityError:
        if idempotency_key:
            existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
        raise


def _run(*, transaction, legs, expected_accounts, memo='', guards=None):
    """Post legs, sync balances, finalise the transaction atomically.

    ``guards`` maps account pk -> amount that must remain within the account's
    available balance (enforced after row locks are taken).
    """
    guards = guards or {}
    with db_transaction.atomic():
        transaction.status = 'processing'
        transaction.save(update_fields=['status', 'updated_at'])

        accounts = [leg['account'] for leg in legs]
        if set(accounts) != set(expected_accounts):
            raise TransactionError(TRANSACTION_ERROR_MESSAGES['account_mismatch'])

        balances = lock_balances(accounts)
        for balance_row in balances:
            requested = guards.get(balance_row.account_id)
            if requested and balance_row.available_balance < to_money(requested):
                raise TransactionError(
                    f'Insufficient available balance on '
                    f'{balance_row.account.account_no} '
                    f'({balance_row.available_balance}).'
                )

        journal = post_journal(
            legs=legs,
            description=memo or transaction.get_kind_display(),
            reference=transaction.reference,
            transaction=transaction,
        )
        transaction.journal = journal

        from apps.accounts.services import apply_balance_delta

        entries = {}
        for leg in legs:
            agg = entries.setdefault(
                leg['account'].pk, {'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
            )
            agg['debit'] += leg['debit']
            agg['credit'] += leg['credit']
        apply_balance_delta(balances, entries)

        transaction.status = 'completed'
        transaction.save(update_fields=['status', 'updated_at'])
    return transaction


def deposit(
    *,
    account,
    amount,
    branch=None,
    requested_by=None,
    idempotency_key=None,
    memo='',
    source_channel='api',
    cash_account=None,
):
    amount = _to_positive_money(amount)
    cash_account = cash_account or get_default_cash_account(branch)
    tx = _create_transaction(
        kind='deposit',
        idempotency_key=idempotency_key,
        branch=branch,
        requested_by=requested_by,
        memo=memo,
        source_channel=source_channel,
    )
    if tx.status == 'completed':
        return tx
    legs = [
        {
            'account': cash_account,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': 'Cash in from deposit',
        },
        {'account': account, 'debit': Decimal('0.00'), 'credit': amount, 'note': 'Member deposit'},
    ]
    return _run(transaction=tx, legs=legs, expected_accounts=[cash_account, account], memo=memo)


def withdraw(
    *,
    account,
    amount,
    branch=None,
    requested_by=None,
    idempotency_key=None,
    memo='',
    source_channel='api',
    cash_account=None,
):
    amount = _to_positive_money(amount)
    cash_account = cash_account or get_default_cash_account(branch)
    tx = _create_transaction(
        kind='withdrawal',
        idempotency_key=idempotency_key,
        branch=branch,
        requested_by=requested_by,
        memo=memo,
        source_channel=source_channel,
    )
    if tx.status == 'completed':
        return tx
    legs = [
        {
            'account': cash_account,
            'debit': Decimal('0.00'),
            'credit': amount,
            'note': 'Cash paid out',
        },
        {
            'account': account,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': 'Member withdrawal',
        },
    ]
    return _run(
        transaction=tx,
        legs=legs,
        expected_accounts=[cash_account, account],
        memo=memo,
        guards={account.pk: amount},
    )


def transfer(
    *,
    from_account,
    to_account,
    amount,
    branch=None,
    requested_by=None,
    idempotency_key=None,
    memo='',
    source_channel='api',
):
    amount = _to_positive_money(amount)
    if from_account.pk == to_account.pk:
        raise TransactionError(TRANSACTION_ERROR_MESSAGES['distinct_accounts'])
    tx = _create_transaction(
        kind='transfer',
        idempotency_key=idempotency_key,
        branch=branch,
        requested_by=requested_by,
        memo=memo,
        source_channel=source_channel,
    )
    if tx.status == 'completed':
        return tx
    legs = [
        {
            'account': from_account,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': 'Transfer out',
        },
        {'account': to_account, 'debit': Decimal('0.00'), 'credit': amount, 'note': 'Transfer in'},
    ]
    return _run(
        transaction=tx,
        legs=legs,
        expected_accounts=[from_account, to_account],
        memo=memo,
        guards={from_account.pk: amount},
    )


def reverse(*, transaction, reason='', requested_by=None, idempotency_key=None):
    """Reverse a completed transaction by posting opposite legs."""
    if transaction.status != 'completed':
        raise TransactionError(TRANSACTION_ERROR_MESSAGES['not_completed'])
    journal = getattr(transaction, 'journal', None)
    if journal is None:
        raise TransactionError(TRANSACTION_ERROR_MESSAGES['no_journal'])
    original_entries = list(journal.entries.select_related('account'))

    reversal = _create_transaction(
        kind='reversal',
        idempotency_key=idempotency_key,
        branch=transaction.branch,
        requested_by=requested_by,
        memo=reason,
        source_channel=transaction.source_channel,
    )
    if reversal.status == 'completed':
        return reversal

    legs = [
        {
            'account': entry.account,
            'debit': entry.credit,
            'credit': entry.debit,
            'note': f'Reversal of {transaction.reference}',
        }
        for entry in original_entries
    ]
    with db_transaction.atomic():
        try:
            _run(
                transaction=reversal,
                legs=legs,
                expected_accounts=[entry.account for entry in original_entries],
                memo=reason or f'Reversal of {transaction.reference}',
            )
        except TransactionError:
            transaction.status = 'failed'
            transaction.error_message = 'Reversal failed'
            transaction.save(update_fields=['status', 'error_message', 'updated_at'])
            raise
        transaction.status = 'reversed'
        transaction.error_message = reason
        transaction.save(update_fields=['status', 'error_message', 'updated_at'])
    return reversal
