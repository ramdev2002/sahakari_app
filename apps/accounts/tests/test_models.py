from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Account, AccountBalance, AccountType
from apps.accounts.services import ensure_balance, ensure_seed_accounts, get_or_create_account_type
from apps.core.money import to_money


class SeedAccountsTests(TestCase):
    def test_seed_accounts_are_idempotent(self):
        first = ensure_seed_accounts()
        second = ensure_seed_accounts()
        self.assertIsNotNone(first['cash'])
        self.assertEqual(AccountType.objects.get(code='CASH').is_system, True)
        self.assertEqual(Account.objects.filter(account_no='CASH-MAIN').count(), 1)
        self.assertEqual(first['cash'].pk, second['cash'].pk)

    def test_savings_account_type_is_credit_side(self):
        ensure_seed_accounts()
        self.assertEqual(AccountType.objects.get(code='SAVINGS').side, 'credit')


class AccountTypeTests(TestCase):
    def test_get_or_create_creates_once(self):
        atype = get_or_create_account_type(code='X1', name='X', side='debit', is_system=True)
        atype2 = get_or_create_account_type(code='X1', name='X', side='debit', is_system=True)
        self.assertEqual(atype.pk, atype2.pk)
        self.assertEqual(AccountType.objects.count(), 1)


class BalanceTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.cash = self.accounts['cash']

    def test_ensure_balance_gives_zero_row(self):
        balance = ensure_balance(self.cash)
        self.assertEqual(balance.current_balance, to_money(0))
        self.assertEqual(balance.available_balance, to_money(0))

    def test_balance_constraint_rejects_negative_current(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AccountBalance.objects.create(
                    account=self.cash, current_balance=-1, available_balance=0
                )

    def test_balance_constraint_rejects_available_greater_than_current(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AccountBalance.objects.create(
                    account=self.cash, current_balance=10, available_balance=20
                )
