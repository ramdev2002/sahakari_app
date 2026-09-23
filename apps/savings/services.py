"""Savings account opening flow — bridges members, chart of accounts and the
transaction engine for the optional opening deposit.
"""

import uuid

from django.db import transaction as db_transaction

from apps.accounts.models import Account
from apps.accounts.services import ensure_balance, get_or_create_account_type
from apps.transactions.services import deposit

from .models import SavingsAccount


def generate_account_no():
    return f'SAV-{uuid.uuid4().hex[:12].upper()}'


def open_savings_account(
    *, member, product, branch=None, initial_deposit=0, requested_by=None, idempotency_key=None
):
    """Open a savings account (and its posting account) with optional deposit.

    Returns ``(savings_account, opening_transaction_or_None)``.
    """
    with db_transaction.atomic():
        account_type = get_or_create_account_type(
            code='SAVINGS', name='Member Savings', side='credit', category='savings', is_system=True
        )
        account = Account.objects.create(
            account_no=generate_account_no(),
            name=f'Savings {member.member_no}',
            account_type=account_type,
            member=member,
            branch=branch,
        )
        ensure_balance(account)
        savings = SavingsAccount.objects.create(
            account_no=account.account_no,
            member=member,
            product=product,
            account=account,
            branch=branch,
        )
    opening_tx = None
    if initial_deposit:
        opening_tx = deposit(
            account=account,
            amount=initial_deposit,
            branch=branch,
            requested_by=requested_by,
            idempotency_key=idempotency_key,
            memo=f'Savings account opening deposit for {member.member_no}',
        )
    return savings, opening_tx
