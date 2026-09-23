"""Low-level double-entry posting services.

These functions are intentionally dumb: they take a validated set of
debit/credit legs and persist a balanced journal. Higher-level business
flows in ``apps.transactions`` own locking, idempotency and balance guards.
"""

import uuid
from decimal import Decimal

from django.db import transaction as db_transaction

from apps.core.money import MoneyValidationError, to_money

LEDGER_ERROR_MESSAGES = {
    'no_entries': 'A journal must contain at least one entry.',
    'unbalanced': 'Debits and credits must be equal.',
    'non_positive': 'Every leg must be a positive amount.',
}


class LedgerError(ValueError):
    pass


def _validate_legs(legs):
    if not legs:
        raise LedgerError(LEDGER_ERROR_MESSAGES['no_entries'])
    for leg in legs:
        account = leg.get('account')
        if account is None:
            raise LedgerError('Every leg must reference an account.')
        debit = to_money(leg.get('debit', 0))
        credit = to_money(leg.get('credit', 0))
        if debit < 0 or credit < 0:
            raise MoneyValidationError('Ledger amounts cannot be negative.')
        if (debit > 0) == (credit > 0):
            raise LedgerError(LEDGER_ERROR_MESSAGES['non_positive'])
        yield {'account': account, 'debit': debit, 'credit': credit, 'note': leg.get('note', '')}


def _generate_journal_no():
    return f'JRN-{uuid.uuid4().hex[:12].upper()}'


def post_journal(*, legs, description='', reference='', transaction=None):
    """Persist a balanced journal atomically.

    ``legs`` is an iterable of dicts: {account, debit, credit, note}.
    Returns the created ``Journal``.
    """
    from .models import Journal, LedgerEntry

    validated = list(_validate_legs(legs))
    total_debit = sum((leg['debit'] for leg in validated), Decimal('0.00'))
    total_credit = sum((leg['credit'] for leg in validated), Decimal('0.00'))
    if total_debit != total_credit:
        raise LedgerError(LEDGER_ERROR_MESSAGES['unbalanced'])

    with db_transaction.atomic():
        journal = Journal.objects.create(
            journal_no=_generate_journal_no(),
            description=description,
            reference=reference,
            transaction=transaction,
        )
        LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal, **leg) for leg in validated])
    return journal


def get_account_balance(account):
    """True book balance (debits - credits) for an account from the ledger."""
    from django.db.models import Sum

    aggregates = account.ledger_entries.aggregate(debit=Sum('debit'), credit=Sum('credit'))
    return (aggregates['debit'] or Decimal('0.00')) - (aggregates['credit'] or Decimal('0.00'))


def account_entries(account, *, reversed_order=False):
    """Ledger entries for an account, optionally newest-first for statements."""
    qs = account.ledger_entries.select_related('journal').order_by('journal__created_at')
    if reversed_order:
        qs = qs.reverse()
    return qs
