from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import AccountBalance
from apps.accounts.services import ensure_seed_accounts, inject_capital
from apps.core import rbac
from apps.core.money import to_money
from apps.identity.models import User
from apps.loans.models import LoanProduct
from apps.members.models import Member
from apps.savings.models import SavingsProduct


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_seeds_products_and_capital(self):
        call_command('seed_demo', no_demo=True)

        self.assertEqual(SavingsProduct.objects.filter(code='REGULAR').count(), 1)
        self.assertEqual(SavingsProduct.objects.filter(code='CHILDREN').count(), 1)
        self.assertEqual(LoanProduct.objects.filter(code='GENERAL').count(), 1)
        self.assertEqual(LoanProduct.objects.filter(code='AGRI').count(), 1)

        accounts = ensure_seed_accounts()
        cash = AccountBalance.objects.get(account=accounts['cash'])
        self.assertEqual(cash.current_balance, to_money('1000000.00'))

        self.assertEqual(User.objects.count(), 0)

    def test_seed_demo_is_idempotent(self):
        call_command('seed_demo', no_demo=True)
        call_command('seed_demo', no_demo=True)

        self.assertEqual(SavingsProduct.objects.count(), 2)
        self.assertEqual(LoanProduct.objects.count(), 2)
        accounts = ensure_seed_accounts()
        cash = AccountBalance.objects.get(account=accounts['cash'])
        self.assertEqual(cash.current_balance, to_money('1000000.00'))

    def test_seed_demo_tops_up_short_capital(self):
        accounts = ensure_seed_accounts()
        inject_capital(amount=Decimal('100.00'))
        call_command('seed_demo', no_demo=True)

        cash = AccountBalance.objects.get(account=accounts['cash'])
        self.assertEqual(cash.current_balance, to_money('1000000.00'))

    def test_seed_demo_seeds_a_user_per_identity(self):
        call_command('seed_demo', no_demo=True)
        # Without --no-demo, one login per identity type is created.
        call_command('seed_demo')

        self.assertEqual(User.objects.count(), len(rbac.ALL_ROLE_GROUPS))
        for email in [
            'demo@jharlang.local',
            'admin.officer@jharlang.local',
            'branch.manager@jharlang.local',
            'loan.officer@jharlang.local',
            'account.officer@jharlang.local',
            'cashier@jharlang.local',
            'auditor@jharlang.local',
            'member@jharlang.local',
        ]:
            user = User.objects.get(email=email)
            self.assertTrue(user.check_password('Demo@12345'))
            self.assertTrue(user.is_active)
            self.assertIsNotNone(user.role)

    def test_seed_demo_creates_demo_member_when_empty(self):
        call_command('seed_demo')

        member = Member.objects.filter(first_name='Demo', last_name='Member').get()
        self.assertEqual(member.user.email, 'member@jharlang.local')
        savings_total = member.savings_accounts.count()
        self.assertEqual(savings_total, 1)
        self.assertEqual(member.loans.count(), 1)

        accounts = ensure_seed_accounts()
        cash = AccountBalance.objects.get(account=accounts['cash'])
        self.assertEqual(cash.current_balance, to_money('1001000.00'))
