"""Idempotent demo bootstrap for local development and QA.

Seeds the default roles, chart of accounts, seed capital, savings and loan
products, a demo user for every identity type (with fixed credentials for the
QA team), and (optionally) a demo member with a savings account and a requested
loan so the frontend has live data out of the box.

Usage::

    python manage.py seed_demo
    python manage.py seed_demo --no-demo        # skip demo users/member/savings/loan
"""

from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import AccountBalance
from apps.accounts.services import ensure_seed_accounts, inject_capital
from apps.core.constants import GROUP_ADMINISTRATIVE_OFFICER, ROLE_CHOICES, Role
from apps.core.money import to_money
from apps.identity.models import User
from apps.loans.models import LoanProduct
from apps.loans.services import create_loan
from apps.members.models import Member
from apps.savings.models import SavingsProduct
from apps.savings.services import open_savings_account

SAVINGS_PRODUCTS = [
    {
        'code': 'REGULAR',
        'name': 'Regular Savings',
        'interest_rate': Decimal('5.00'),
        'min_opening_balance': Decimal('500.00'),
    },
    {
        'code': 'CHILDREN',
        'name': 'Child Savings',
        'interest_rate': Decimal('6.00'),
        'min_opening_balance': Decimal('100.00'),
    },
]

LOAN_PRODUCTS = [
    {
        'code': 'GENERAL',
        'name': 'General Loan',
        'min_amount': Decimal('5000.00'),
        'max_amount': Decimal('1000000.00'),
        'interest_rate': Decimal('12.00'),
        'default_tenure_months': 24,
    },
    {
        'code': 'AGRI',
        'name': 'Agriculture Loan',
        'min_amount': Decimal('10000.00'),
        'max_amount': Decimal('500000.00'),
        'interest_rate': Decimal('10.00'),
        'default_tenure_months': 18,
    },
]

CAPITAL_AMOUNT = Decimal('1000000.00')

DEMO_USER_PASSWORD = 'Demo@12345'

# One demo user per identity type: (email, first_name, last_name, role group, is_superuser).
DEMO_USERS = [
    ('demo@jharlang.local', 'Demo', 'Admin', ROLE_CHOICES[Role.SYSTEM_ADMIN], True),
    ('admin.officer@jharlang.local', 'Admin', 'Officer', GROUP_ADMINISTRATIVE_OFFICER, False),
    (
        'branch.manager@jharlang.local',
        'Branch',
        'Manager',
        ROLE_CHOICES[Role.BRANCH_MANAGER],
        False,
    ),
    ('loan.officer@jharlang.local', 'Loan', 'Officer', ROLE_CHOICES[Role.LOAN_OFFICER], False),
    (
        'account.officer@jharlang.local',
        'Account',
        'Officer',
        ROLE_CHOICES[Role.ACCOUNT_OFFICER],
        False,
    ),
    ('cashier@jharlang.local', 'Cash', 'Teller', ROLE_CHOICES[Role.CASHIER], False),
    ('auditor@jharlang.local', 'Audit', 'Team', ROLE_CHOICES[Role.AUDITOR], False),
    ('member@jharlang.local', 'Demo', 'Member', ROLE_CHOICES[Role.MEMBER], False),
]


class Command(BaseCommand):
    help = 'Seed roles, chart of accounts, products and demo data for local dev.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-demo',
            action='store_true',
            dest='no_demo',
            help='Skip the demo users, member, savings account and loan records.',
        )

    def handle(self, *args, **options):
        call_command('ensure_default_roles')
        self.stdout.write('Roles: OK')

        accounts = ensure_seed_accounts()
        self.stdout.write('Chart of accounts: OK')

        shortfall = self._funding_shortfall(accounts['cash'])
        if shortfall > 0:
            inject_capital(amount=shortfall)
            self.stdout.write(f'Seed capital: injected {to_money(shortfall)}')
        else:
            self.stdout.write('Seed capital: adequately funded')

        for spec in SAVINGS_PRODUCTS:
            SavingsProduct.objects.get_or_create(code=spec['code'], defaults=spec)
        self.stdout.write(f'Savings products: {SavingsProduct.objects.count()}')

        for spec in LOAN_PRODUCTS:
            LoanProduct.objects.get_or_create(code=spec['code'], defaults=spec)
        self.stdout.write(f'Loan products: {LoanProduct.objects.count()}')

        if options['no_demo']:
            self.stdout.write('Demo member: skipped')
            self.stdout.write('Demo users: skipped')
            return

        demo_users = self._ensure_demo_users()
        self.stdout.write(f'Demo users: {len(demo_users)} (all roles)')

        member_user = demo_users.get(ROLE_CHOICES[Role.MEMBER])
        first = Member.objects.filter(first_name='Demo', last_name='Member').first()
        member = first or Member.objects.create(
            first_name='Demo', last_name='Member', phone='9800000000', address='Besi Sahar, Lamjung'
        )
        if member.user_id != getattr(member_user, 'pk', None):
            member.user = member_user
            member.save(update_fields=['user'])
        savings_product = SavingsProduct.objects.get(code='REGULAR')
        savings = member.savings_accounts.filter(product=savings_product).first()
        if savings is None:
            savings, _ = open_savings_account(
                member=member,
                product=savings_product,
                initial_deposit=Decimal('1000.00'),
                idempotency_key='seed-demo-savings-opening',
            )
        loan_product = LoanProduct.objects.get(code='GENERAL')
        if not member.loans.exists():
            create_loan(
                member=member,
                product=loan_product,
                savings_account=savings,
                principal=Decimal('50000.00'),
            )
        self.stdout.write(
            f'Demo member: {member.member_no} ({member.first_name} {member.last_name}'.strip() + ')'
        )
        self.stdout.write(f'  savings account: {savings.account_no}')
        self.stdout.write('  requested loan: GENERAL / 50000.00')
        self.stdout.write(self.style.SUCCESS('seed_demo complete.'))

    def _ensure_demo_users(self):
        """Create/refresh one login per identity type with fixed credentials."""
        users = {}
        for email, first_name, last_name, group_name, is_superuser in DEMO_USERS:
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                if is_superuser:
                    user = User.objects.create_superuser(
                        email=email,
                        password=DEMO_USER_PASSWORD,
                        first_name=first_name,
                        last_name=last_name,
                    )
                else:
                    user = User.objects.create_user(
                        email=email,
                        password=DEMO_USER_PASSWORD,
                        first_name=first_name,
                        last_name=last_name,
                    )
            user.set_password(DEMO_USER_PASSWORD)
            user.is_active = True
            user.status = 'active'
            role_group, _ = Group.objects.get_or_create(name=group_name)
            user.role = role_group
            user.groups.add(role_group)
            user.save()
            users[group_name] = user
        return users

    def _funding_shortfall(self, cash_account):
        """Amount needed to bring cash to the capital floor, or zero."""
        balance = AccountBalance.objects.filter(account=cash_account).first()
        current = balance.current_balance if balance else 0
        return max(CAPITAL_AMOUNT - current, 0)
