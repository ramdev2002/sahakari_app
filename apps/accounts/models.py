import uuid

from django.db import models

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, TimestampedModel, soft_delete_state_constraint
from apps.core.money import MoneyField

ACCOUNT_SIDES = [
    ('debit', 'Debit (assets & expenses increase on debit)'),
    ('credit', 'Credit (liabilities, equity & income increase on credit)'),
]

BALANCE_DIRECTION = {
    'debit': 1,  # balance = debits - credits
    'credit': -1,  # balance = credits - debits
}

ACCOUNT_CATEGORIES = [
    ('cash', 'Cash'),
    ('bank', 'Bank'),
    ('savings', 'Savings'),
    ('loan', 'Loan'),
    ('receivable', 'Receivable'),
    ('payable', 'Payable'),
    ('capital', 'Capital'),
    ('revenue', 'Revenue'),
    ('expense', 'Expense'),
    ('other', 'Other'),
]


class AccountType(SoftDeleteModel, TimestampedModel):
    """Classification of accounts dictating sign conventions & behaviour."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    side = models.CharField(max_length=10, choices=ACCOUNT_SIDES)
    category = models.CharField(max_length=20, choices=ACCOUNT_CATEGORIES, default='other')
    is_system = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['code']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return f'{self.code} — {self.name}'


class Account(SoftDeleteModel, TimestampedModel):
    """A single posting account (member savings, cash, income...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_no = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=150)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name='accounts')
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts',
        help_text='Set for member-facing accounts.',
    )
    branch = models.ForeignKey(
        'organization.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts',
        help_text='Null for system / nominal accounts.',
    )
    allows_overdraft = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['account_no']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return f'{self.account_no} — {self.name}'

    @property
    def balance_direction(self):
        return BALANCE_DIRECTION[self.account_type.side]

    @property
    def is_debit_normal(self):
        return self.account_type.side == 'debit'


class AccountBalance(models.Model):
    """Cached posting balance, updated synchronously with transactions."""

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='balance')
    current_balance = MoneyField(default=0)
    available_balance = MoneyField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='account_balance_non_negative',
                condition=(
                    models.Q(current_balance__gte=0)
                    & models.Q(available_balance__gte=0)
                    & models.Q(available_balance__lte=models.F('current_balance'))
                ),
                violation_error_message=(
                    'Balances must be non-negative with available balance '
                    'not exceeding current balance.'
                ),
            )
        ]

    def __str__(self):
        return f'{self.account} = {self.current_balance}'
