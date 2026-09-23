"""Loan lifecycle services — disbursement & repayment posting via the engine."""

import uuid
from decimal import Decimal

from django.db import transaction as db_transaction

from apps.accounts.services import get_or_create_account_type, get_or_create_nominal_account
from apps.core.money import to_money
from apps.transactions.services import TransactionError, _create_transaction, _run

from .models import Loan

LOAN_ERROR_MESSAGES = {
    'not_requested': 'Only requested loans can be approved.',
    'not_approved': 'Only approved loans can be disbursed.',
    'not_disbursed': 'Only disbursed loans can be repaid.',
    'overpay': 'Repayment exceeds outstanding balance.',
}


def generate_loan_no():
    return f'LOAN-{uuid.uuid4().hex[:10].upper()}'


def create_loan(
    *,
    member,
    product,
    savings_account,
    principal,
    interest_rate=None,
    tenure_months=None,
    requested_by=None,
):
    with db_transaction.atomic():
        principal = to_money(principal)
        loan = Loan.objects.create(
            loan_no=generate_loan_no(),
            member=member,
            product=product,
            savings_account=savings_account,
            principal=principal,
            interest_rate=interest_rate if interest_rate is not None else product.interest_rate,
            tenure_months=tenure_months or product.default_tenure_months,
            requested_by=requested_by,
        )
        loan.clean()
    return loan


def approve(loan, requested_by=None):
    if loan.status != 'requested':
        raise TransactionError(LOAN_ERROR_MESSAGES['not_requested'])
    loan.status = 'approved'
    loan.save(update_fields=['status', 'updated_at'])
    return loan


def disburse(*, loan, requested_by=None, idempotency_key=None, cash_account=None):
    """Credit cash, debit loan receivable; loan becomes active."""
    if loan.status != 'approved':
        raise TransactionError(LOAN_ERROR_MESSAGES['not_approved'])
    from apps.accounts.services import (
        get_default_cash_account,
        get_or_create_account_type,
        get_or_create_nominal_account,
    )

    account_type = get_or_create_account_type(
        code='LOAN_RECEIVABLE',
        name='Loan Receivable',
        side='debit',
        category='loan',
        is_system=True,
    )
    receivable = get_or_create_nominal_account(
        account_no='LOAN-RECV-1', name='Loan Receivable Portfolio', account_type=account_type
    )
    cash_account = cash_account or get_default_cash_account(loan.savings_account.branch)

    tx = _create_transaction(
        kind='disbursement',
        idempotency_key=idempotency_key,
        branch=loan.savings_account.branch,
        requested_by=requested_by,
        memo=f'Disbursement {loan.loan_no}',
    )
    if tx.status == 'completed':
        return tx

    amount = to_money(loan.principal)
    legs = [
        {
            'account': receivable,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': f'Loan {loan.loan_no} issued',
        },
        {
            'account': cash_account,
            'debit': Decimal('0.00'),
            'credit': amount,
            'note': f'Cash out for {loan.loan_no}',
        },
    ]
    with db_transaction.atomic():
        _run(
            transaction=tx,
            legs=legs,
            expected_accounts=[receivable, cash_account],
            memo=f'Disbursement {loan.loan_no}',
        )
        loan.disbursed_at = tx.created_at
        loan.status = 'active'
        loan.save(update_fields=['disbursed_at', 'status', 'updated_at'])
    return tx


def repay(*, loan, amount, requested_by=None, idempotency_key=None):
    """Repay from the loan's savings account; splits interest then principal.

    Entries: debit member savings (credit-side decreases), credit loan-
    receivable (asset decreases) and credit interest income (income increases).
    """
    if loan.status not in ('disbursed', 'active'):
        raise TransactionError(LOAN_ERROR_MESSAGES['not_disbursed'])
    amount = to_money(amount)
    if amount <= 0:
        raise TransactionError('Repayment amount must be positive.')
    total_outstanding = loan.outstanding_principal + loan.outstanding_interest
    if amount > total_outstanding:
        raise TransactionError(LOAN_ERROR_MESSAGES['overpay'])

    interest_portion = min(amount, loan.outstanding_interest)
    principal_portion = amount - interest_portion

    interest_account_type = get_or_create_account_type(
        code='INTEREST_INCOME',
        name='Interest Income',
        side='credit',
        category='revenue',
        is_system=True,
    )
    interest_income = get_or_create_nominal_account(
        account_no='INT-INCOME-1', name='Interest Income', account_type=interest_account_type
    )
    receivable_type = get_or_create_account_type(
        code='LOAN_RECEIVABLE',
        name='Loan Receivable',
        side='debit',
        category='loan',
        is_system=True,
    )
    receivable = get_or_create_nominal_account(
        account_no='LOAN-RECV-1', name='Loan Receivable Portfolio', account_type=receivable_type
    )

    source = loan.savings_account.account
    tx = _create_transaction(
        kind='repayment',
        idempotency_key=idempotency_key,
        branch=loan.savings_account.branch,
        requested_by=requested_by,
        memo=f'Repayment {loan.loan_no}',
    )
    if tx.status == 'completed':
        return tx

    legs = [
        {
            'account': source,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': f'Repayment source {loan.loan_no}',
        },
        {
            'account': receivable,
            'debit': Decimal('0.00'),
            'credit': principal_portion,
            'note': f'Principal {loan.loan_no}',
        },
        {
            'account': interest_income,
            'debit': Decimal('0.00'),
            'credit': interest_portion,
            'note': f'Interest {loan.loan_no}',
        },
    ]
    legs = [leg for leg in legs if leg['debit'] or leg['credit']]
    expected_accounts = [leg['account'] for leg in legs]
    with db_transaction.atomic():
        _run(
            transaction=tx,
            legs=legs,
            expected_accounts=expected_accounts,
            memo=f'Repayment {loan.loan_no}',
            guards={source.pk: amount},
        )
        loan.principal_paid = to_money(loan.principal_paid + principal_portion)
        loan.interest_paid = to_money(loan.interest_paid + interest_portion)
        if loan.outstanding_principal <= 0 and loan.outstanding_interest <= 0:
            loan.status = 'closed'
        loan.save(update_fields=['principal_paid', 'interest_paid', 'status', 'updated_at'])
    return tx


def cancel(loan, requested_by=None, reason=''):
    if loan.status not in ('requested', 'approved'):
        raise TransactionError('Only requested or approved loans can be cancelled.')
    loan.status = 'cancelled'
    loan.save(update_fields=['status', 'updated_at'])
    return loan
