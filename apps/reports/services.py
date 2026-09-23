"""Read-model aggregates for reports. All functions are query-only."""

from decimal import Decimal

from django.db.models import Sum

from apps.accounts.models import Account, AccountBalance

_ZERO = Decimal('0.00')


def trial_balance():
    """Per-account debit/credit totals straight from the ledger."""
    rows = []
    for account in Account.objects.select_related('account_type').all():
        agg = account.ledger_entries.aggregate(debit=Sum('debit'), credit=Sum('credit'))
        balance = (agg['debit'] or _ZERO) - (agg['credit'] or _ZERO)
        rows.append(
            {
                'account_no': account.account_no,
                'name': account.name,
                'side': account.account_type.side,
                'debit_total': agg['debit'] or _ZERO,
                'credit_total': agg['credit'] or _ZERO,
                'balance': balance,
            }
        )
    total_debit = sum((row['debit_total'] for row in rows), _ZERO)
    total_credit = sum((row['credit_total'] for row in rows), _ZERO)
    return {
        'rows': sorted(rows, key=lambda row: row['account_no']),
        'total_debit': total_debit,
        'total_credit': total_credit,
        'balanced': total_debit == total_credit,
    }


def member_savings_balances(member_id=None):
    qs = AccountBalance.objects.filter(account__account_type__code='SAVINGS').select_related(
        'account__member'
    )
    if member_id:
        qs = qs.filter(account__member_id=member_id)
    rows = []
    for balance in qs:
        member = balance.account.member
        rows.append(
            {
                'member_no': member.member_no if member else None,
                'account_no': balance.account.account_no,
                'current_balance': balance.current_balance,
                'available_balance': balance.available_balance,
            }
        )
    return rows


def cash_position():
    """Cash & bank balance overview with member-account totals."""
    qs = AccountBalance.objects.filter(
        account__account_type__code__in=['CASH', 'BANK'], account__is_deleted=False
    ).select_related('account__account_type')
    summary = {}
    for balance in qs:
        code = balance.account.account_type.code
        summary[code] = summary.get(code, _ZERO) + balance.current_balance
    return {key: summary.get(key, _ZERO) for key in ('CASH', 'BANK')}


def loan_book(product_code=None):
    from apps.loans.models import Loan

    qs = Loan.objects.filter(status__in=['active', 'disbursed']).select_related('product')
    if product_code:
        qs = qs.filter(product__code=product_code)
    rows = []
    for loan in qs:
        rows.append(
            {
                'loan_no': loan.loan_no,
                'member_no': loan.member.member_no,
                'product': loan.product.code,
                'principal': loan.principal,
                'principal_paid': loan.principal_paid,
                'outstanding': loan.outstanding_principal,
            }
        )
    total_outstanding = sum((row['outstanding'] for row in rows), _ZERO)
    return {'rows': rows, 'total_outstanding': total_outstanding, 'count': len(rows)}
