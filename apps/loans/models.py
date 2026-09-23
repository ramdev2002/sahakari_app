import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, TimestampedModel, soft_delete_state_constraint
from apps.core.money import MoneyField

LOAN_STATUSES = [
    ('requested', 'Requested'),
    ('approved', 'Approved'),
    ('disbursed', 'Disbursed'),
    ('active', 'Active'),
    ('closed', 'Closed'),
    ('written_off', 'Written Off'),
    ('cancelled', 'Cancelled'),
]


class LoanProduct(SoftDeleteModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    min_amount = MoneyField(default=0)
    max_amount = MoneyField(default=1000000)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10, help_text='Annual rate %'
    )
    default_tenure_months = models.PositiveSmallIntegerField(default=12)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['code']
        constraints = [
            models.CheckConstraint(
                name='loan_product_amount_range',
                condition=models.Q(max_amount__gte=models.F('min_amount')),
                violation_error_message='Max amount must be >= min amount.',
            ),
            soft_delete_state_constraint(),
        ]

    def __str__(self):
        return self.name


class Loan(SoftDeleteModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_no = models.CharField(max_length=32, unique=True)
    member = models.ForeignKey('members.Member', on_delete=models.PROTECT, related_name='loans')
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT, related_name='loans')
    savings_account = models.ForeignKey(
        'savings.SavingsAccount',
        on_delete=models.PROTECT,
        related_name='loans',
        help_text='Account used as repayment source.',
    )
    principal = MoneyField(default=0)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10, help_text='Annual rate %'
    )
    tenure_months = models.PositiveSmallIntegerField(default=12)
    status = models.CharField(
        max_length=20, choices=LOAN_STATUSES, default='requested', db_index=True
    )
    disbursed_at = models.DateTimeField(null=True, blank=True)
    principal_paid = MoneyField(default=0)
    interest_paid = MoneyField(default=0)
    requested_by = models.ForeignKey(
        'identity.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                name='loan_principal_positive',
                condition=models.Q(principal__gte=0),
                violation_error_message='Loan principal cannot be negative.',
            ),
            soft_delete_state_constraint(),
        ]

    def __str__(self):
        return f'{self.loan_no} — {self.member}'

    @property
    def outstanding_principal(self):
        return self.principal - self.principal_paid

    @property
    def outstanding_interest(self):
        return self.total_interest - self.interest_paid

    @property
    def total_interest(self):
        # Simple interest over tenure.
        from decimal import Decimal

        months = Decimal(self.tenure_months)
        rate = Decimal(self.interest_rate)
        return self.principal * (rate / Decimal('100')) * (months / Decimal('12'))

    def clean(self):
        if self.principal < self.product.min_amount or self.principal > self.product.max_amount:
            raise ValidationError(
                f'Principal must be between {self.product.min_amount} and '
                f'{self.product.max_amount} for {self.product.code}.'
            )
