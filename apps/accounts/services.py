"""Chart-of-accounts helpers, balance locking and nominal account seeding."""

import uuid
from decimal import Decimal

from apps.core.money import to_money

from .models import Account, AccountBalance, AccountType


def get_or_create_account_type(*, code, name, side, category='other', is_system=False):
    account_type, _ = AccountType.objects.get_or_create(
        code=code,
        defaults={'name': name, 'side': side, 'category': category, 'is_system': is_system},
    )
    return account_type


def get_or_create_nominal_account(*, account_no, name, account_type, branch=None):
    """Idempotent creation of a system / nominal posting account."""
    existing = Account.objects.all_with_deleted().filter(account_no=account_no).first()
    if existing:
        return existing
    account = Account.objects.create(
        account_no=account_no, name=name, account_type=account_type, branch=branch
    )
    ensure_balance(account)
    return account


def ensure_balance(account):
    """Create a zero balance row for the account if missing."""
    balance, _ = AccountBalance.objects.get_or_create(account=account)
    return balance


def lock_balances(accounts):
    """Lock balance rows in deterministic order for concurrency safety."""
    ordered = sorted(accounts, key=lambda account: str(account.pk))
    balances = [
        AccountBalance.objects.select_for_update().get_or_create(account=account)[0]
        for account in ordered
    ]
    return balances


def balances_by_account(balances):
    return {balance.account_id: balance for balance in balances}


def apply_balance_delta(balances, entries):
    """Synchronise cached balances from posted ledger legs.

    ``entries`` is a dict {account_id: {debit, credit}} as produced by callers.
    Direction handling: debit-normal accounts increase on debit, credit-normal
    (liability / income) accounts increase on credit.
    """
    result = {}
    for account_id, leg in entries.items():
        balance_map = balances_by_account(balances)
        balance = balance_map.get(account_id)
        if balance is None:
            raise ValueError(f'Balance row missing for account {account_id}')
        account = balance.account
        delta = Decimal(leg['debit']) - Decimal(leg['credit'])
        if account.account_type.side == 'debit':
            balance.current_balance = to_money(balance.current_balance + delta)
        else:
            balance.current_balance = to_money(balance.current_balance - delta)
        balance.available_balance = balance.current_balance
        balance.save(update_fields=['current_balance', 'available_balance', 'updated_at'])
        result[account_id] = balance
    return result


def assert_balance_sufficient(account, amount, *, allow_overdraft=None):
    """Raise ``ValueError`` if posting would take available balance negative."""
    balance = ensure_balance(account)
    overflow = balance.available_balance - to_money(amount)
    if overflow < 0 and not (allow_overdraft or account.allows_overdraft):
        raise ValueError(
            f'Insufficient available balance on {account.account_no} ({balance.available_balance}).'
        )
    return balance


def generate_account_no(prefix='ACC'):
    return f'{prefix}-{uuid.uuid4().hex[:12].upper()}'


SEED_ACCOUNT_TYPES = [
    {'code': 'CASH', 'name': 'Cash', 'side': 'debit', 'category': 'cash'},
    {'code': 'BANK', 'name': 'Bank', 'side': 'debit', 'category': 'bank'},
    {'code': 'SAVINGS', 'name': 'Member Savings', 'side': 'credit', 'category': 'savings'},
    {'code': 'LOAN_RECEIVABLE', 'name': 'Loan Receivable', 'side': 'debit', 'category': 'loan'},
    {'code': 'INTEREST_INCOME', 'name': 'Interest Income', 'side': 'credit', 'category': 'revenue'},
    {'code': 'FEE_INCOME', 'name': 'Fee Income', 'side': 'credit', 'category': 'revenue'},
    {
        'code': 'INTEREST_EXPENSE',
        'name': 'Interest Expense',
        'side': 'debit',
        'category': 'expense',
    },
    {'code': 'CAPITAL', 'name': 'Cooperative Capital', 'side': 'credit', 'category': 'capital'},
]


def ensure_seed_accounts(branch=None):
    """Create the standard chart-of-accounts types and system cash/bank posts.

    Idempotent; safe to call from bootstrap commands and tests.
    """
    cash = None
    bank = None
    capital = None
    for spec in SEED_ACCOUNT_TYPES:
        account_type = get_or_create_account_type(
            code=spec['code'],
            name=spec['name'],
            side=spec['side'],
            category=spec['category'],
            is_system=True,
        )
        if spec['code'] == 'CASH':
            cash = get_or_create_nominal_account(
                account_no='CASH-MAIN',
                name='Main Cash Tills',
                account_type=account_type,
                branch=branch,
            )
        if spec['code'] == 'BANK':
            bank = get_or_create_nominal_account(
                account_no='BANK-MAIN',
                name='Main Bank Account',
                account_type=account_type,
                branch=branch,
            )
        if spec['code'] == 'CAPITAL':
            capital = get_or_create_nominal_account(
                account_no='CAPITAL-1',
                name='Cooperative Capital',
                account_type=account_type,
                branch=branch,
            )
    return {'cash': cash, 'bank': bank, 'capital': capital}


def get_default_cash_account(branch=None):
    """Resolve the seeded cash account, creating seeds on demand."""
    accounts = ensure_seed_accounts(branch=branch)
    return accounts['cash']


def inject_capital(*, amount, cash_account=None, capital_account=None):
    """Inject seed capital into cash: debit cash / credit capital account.

    Used by bootstrap flows and tests to fund the till before disbursements.
    Returns the posted Journal.
    """
    from django.db import transaction as db_transaction

    from apps.ledger.services import post_journal

    accounts = ensure_seed_accounts()
    cash_account = cash_account or accounts['cash']
    capital_account = capital_account or accounts['capital']
    amount = to_money(amount)
    legs = [
        {
            'account': cash_account,
            'debit': amount,
            'credit': Decimal('0.00'),
            'note': 'Capital injection',
        },
        {
            'account': capital_account,
            'debit': Decimal('0.00'),
            'credit': amount,
            'note': 'Capital injection',
        },
    ]
    with db_transaction.atomic():
        journal = post_journal(legs=legs, description='Seed capital injection')
        balances = lock_balances([cash_account, capital_account])
        entries = {}
        for leg in legs:
            agg = entries.setdefault(
                leg['account'].pk, {'debit': Decimal('0.00'), 'credit': Decimal('0.00')}
            )
            agg['debit'] += leg['debit']
            agg['credit'] += leg['credit']
        apply_balance_delta(balances, entries)
    return journal
