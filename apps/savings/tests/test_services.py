from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import AccountBalance
from apps.accounts.services import ensure_seed_accounts
from apps.core.money import to_money
from apps.members.models import Member
from apps.savings.models import SavingsAccount, SavingsProduct
from apps.savings.services import open_savings_account


class OpenSavingsAccountTests(TestCase):
    def setUp(self):
        ensure_seed_accounts()
        self.member = Member.objects.create(first_name='A', last_name='B')
        self.product = SavingsProduct.objects.create(code='REGULAR', name='Regular Savings')

    def test_open_without_deposit(self):
        savings, opening_tx = open_savings_account(member=self.member, product=self.product)
        self.assertIsNotNone(savings.pk)
        self.assertIsNone(opening_tx)
        self.assertEqual(savings.account.balance.current_balance, to_money(0))

    def test_open_with_initial_deposit(self):
        savings, opening_tx = open_savings_account(
            member=self.member,
            product=self.product,
            initial_deposit=Decimal('250.00'),
            idempotency_key='open-1',
        )
        self.assertIsNotNone(opening_tx)
        balance = AccountBalance.objects.get(account=savings.account_id)
        self.assertEqual(balance.current_balance, to_money('250.00'))
        self.assertEqual(SavingsAccount.objects.count(), 1)

    def test_account_no_unique(self):
        member_b = Member.objects.create(first_name='C', last_name='D')
        open_savings_account(member=self.member, product=self.product)
        savings_b, _ = open_savings_account(member=member_b, product=self.product)
        self.assertNotEqual(SavingsAccount.objects.first().account_no, savings_b.account_no)
