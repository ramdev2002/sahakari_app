from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Account, AccountBalance, AccountType
from apps.accounts.services import ensure_seed_accounts
from apps.core.money import to_money
from apps.ledger.models import Journal
from apps.transactions import services
from apps.transactions.models import Transaction


def current_balance(account):
    """Fresh read of the cached balance (avoids stale related-object caches)."""
    return AccountBalance.objects.get(account=account).current_balance


def make_savings_account(account_no='SAV-1', **kwargs):
    savings_type = AccountType.objects.get(code='SAVINGS')
    return Account.objects.create(
        account_no=account_no, name=f'Savings {account_no}', account_type=savings_type, **kwargs
    )


class DepositTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.cash = self.accounts['cash']
        self.savings = make_savings_account()

    def test_deposit_updates_balances_and_posts_journal(self):
        tx = services.deposit(account=self.savings, amount=Decimal('100.00'))
        self.assertEqual(tx.status, 'completed')
        self.assertEqual(tx.kind, 'deposit')
        self.assertEqual(current_balance(self.savings), to_money('100.00'))
        self.assertEqual(current_balance(self.cash), to_money('100.00'))
        journal = tx.journal
        self.assertTrue(journal.is_balanced)
        self.assertEqual(sum(e.credit for e in journal.entries.all()), to_money('100.00'))
        self.assertEqual(sum(e.debit for e in journal.entries.all()), to_money('100.00'))

    def test_zero_deposit_rejected(self):
        with self.assertRaises(ValueError):
            services.deposit(account=self.savings, amount=0)

    def test_negative_deposit_rejected(self):
        with self.assertRaises(ValueError):
            services.deposit(account=self.savings, amount=Decimal('-10'))

    def test_idempotency_key_returns_same_transaction(self):
        first = services.deposit(
            account=self.savings, amount=Decimal('50.00'), idempotency_key='dep-1'
        )
        second = services.deposit(
            account=self.savings, amount=Decimal('50.00'), idempotency_key='dep-1'
        )
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(current_balance(self.savings), to_money('50.00'))


class WithdrawTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.cash = self.accounts['cash']
        self.savings = make_savings_account()

    def test_withdraw_reduces_balances(self):
        services.deposit(account=self.savings, amount=Decimal('200.00'))
        tx = services.withdraw(account=self.savings, amount=Decimal('75.00'), memo='ATM')
        self.assertEqual(tx.status, 'completed')
        self.assertEqual(current_balance(self.savings), to_money('125.00'))
        self.assertEqual(current_balance(self.cash), to_money('125.00'))

    def test_insufficient_funds_rejected(self):
        services.deposit(account=self.savings, amount=Decimal('10.00'))
        with self.assertRaises(services.TransactionError):
            services.withdraw(account=self.savings, amount=Decimal('999.00'))

    def test_overdraft_disallowed_even_when_allowed_flag_off(self):
        self.savings.allows_overdraft = False
        self.savings.save()
        with self.assertRaises(services.TransactionError):
            services.withdraw(account=self.savings, amount=Decimal('1.00'))


class TransferTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.a = make_savings_account('SAV-A')
        self.b = make_savings_account('SAV-B')

    def test_transfer_moves_money(self):
        services.deposit(account=self.a, amount=Decimal('100.00'))
        services.transfer(from_account=self.a, to_account=self.b, amount=Decimal('40.00'))
        self.assertEqual(current_balance(self.a), to_money('60.00'))
        self.assertEqual(current_balance(self.b), to_money('40.00'))

    def test_transfer_to_same_account_rejected(self):
        with self.assertRaises(services.TransactionError):
            services.transfer(from_account=self.a, to_account=self.a, amount=Decimal('10.00'))

    def test_transfer_insufficient_funds_rejected(self):
        with self.assertRaises(services.TransactionError):
            services.transfer(from_account=self.a, to_account=self.b, amount=Decimal('10.00'))


class ReversalTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.cash = self.accounts['cash']
        self.savings = make_savings_account()

    def test_reverse_restores_balances(self):
        services.deposit(account=self.savings, amount=Decimal('100.00'))
        tx = Transaction.objects.get(kind='deposit', idempotency_key=None, status='completed')
        reversal = services.reverse(transaction=tx, reason='wrong amount')
        self.assertEqual(reversal.status, 'completed')
        self.assertEqual(reversal.kind, 'reversal')
        tx.refresh_from_db()
        self.assertEqual(tx.status, 'reversed')
        self.assertEqual(current_balance(self.savings), to_money(0))
        self.assertEqual(current_balance(self.cash), to_money(0))

    def test_reverse_only_completed(self):
        tx = Transaction.objects.create(reference='TXN-NOTDONE', kind='deposit', status='initiated')
        with self.assertRaises(services.TransactionError):
            services.reverse(transaction=tx, reason='nope')

    def test_ledger_reconciles_after_reversal(self):
        services.deposit(account=self.savings, amount=Decimal('100.00'))
        tx = Transaction.objects.first()
        services.reverse(transaction=tx, reason='void')
        total = sum((j.totals['debit'] - j.totals['credit']) for j in Journal.objects.all())
        self.assertEqual(total, 0)


class TransactionModelTests(TestCase):
    def test_unique_references(self):
        t1 = Transaction.objects.create(reference='TXN-AAA', kind='deposit')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Transaction.objects.create(reference='TXN-AAA', kind='deposit')
        self.assertEqual(Transaction.objects.get(pk=t1.pk).is_final, False)
