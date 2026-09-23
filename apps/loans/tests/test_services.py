from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import AccountBalance
from apps.accounts.services import ensure_seed_accounts, inject_capital
from apps.core.money import to_money
from apps.loans import services
from apps.loans.models import LoanProduct
from apps.members.models import Member
from apps.savings.models import SavingsProduct
from apps.savings.services import open_savings_account
from apps.transactions.services import deposit


class LoanLifecycleTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.member = Member.objects.create(first_name='A', last_name='B')
        self.product = LoanProduct.objects.create(
            code='PLAN', name='Plan Loan', max_amount=Decimal('500000')
        )
        self.cash = self.accounts['cash']
        inject_capital(amount=Decimal('500000.00'))
        savings_product = SavingsProduct.objects.create(code='REG', name='R')
        self.savings, _ = open_savings_account(
            member=self.member, product=savings_product, initial_deposit=Decimal('1000.00')
        )

    def test_full_lifecycle(self):
        loan = services.create_loan(
            member=self.member,
            product=self.product,
            savings_account=self.savings,
            principal=Decimal('10000.00'),
        )
        self.assertEqual(loan.status, 'requested')
        services.approve(loan)
        self.assertEqual(loan.status, 'approved')
        tx = services.disburse(loan=loan)
        self.assertEqual(tx.kind, 'disbursement')
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'active')
        self.assertIsNotNone(loan.disbursed_at)
        # cash went down by principal (500000 capital + 1000 opening - 10000 loan)
        self.assertEqual(
            AccountBalance.objects.get(account=self.cash).current_balance, to_money('491000.00')
        )
        return loan

    def test_repayment_reduces_loan(self):
        loan = self.test_full_lifecycle()
        # deposit enough to service the loan
        deposit(account=self.savings.account, amount=Decimal('2000.00'), idempotency_key='topup')
        repay_tx = services.repay(loan=loan, amount=Decimal('1000.00'))
        self.assertEqual(repay_tx.kind, 'repayment')
        loan.refresh_from_db()
        self.assertEqual(loan.interest_paid, to_money('1000.00'))
        self.assertEqual(loan.principal_paid, to_money('0.00'))
        self.assertEqual(loan.status, 'active')

    def test_full_repayment_closes_loan(self):
        loan = self.test_full_lifecycle()
        total = loan.outstanding_principal + loan.outstanding_interest
        deposit(account=self.savings.account, amount=total, idempotency_key='settle')
        services.repay(loan=loan, amount=total)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'closed')
        self.assertEqual(loan.outstanding_principal, 0)
        self.assertEqual(loan.outstanding_interest, 0)

    def test_repayment_rejected_when_overpaying(self):
        loan = self.test_full_lifecycle()
        with self.assertRaises(services.TransactionError):
            services.repay(
                loan=loan,
                amount=loan.outstanding_principal + loan.outstanding_interest + Decimal('1.00'),
            )

    def test_disburse_requires_approval(self):
        loan = services.create_loan(
            member=self.member,
            product=self.product,
            savings_account=self.savings,
            principal=Decimal('5000.00'),
        )
        with self.assertRaises(services.TransactionError):
            services.disburse(loan=loan)

    def test_cancel_only_when_not_active(self):
        loan = services.create_loan(
            member=self.member,
            product=self.product,
            savings_account=self.savings,
            principal=Decimal('5000.00'),
        )
        services.cancel(loan)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'cancelled')
