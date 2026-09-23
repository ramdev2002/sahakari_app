import uuid
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, TimestampedModel, soft_delete_state_constraint
from apps.core.money import MoneyField


class SavingsProduct(SoftDeleteModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text='Annual rate %'
    )
    min_opening_balance = MoneyField(default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['code']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return self.name


class SavingsAccount(SoftDeleteModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_no = models.CharField(max_length=32, unique=True)
    member = models.ForeignKey(
        'members.Member', on_delete=models.PROTECT, related_name='savings_accounts'
    )
    product = models.ForeignKey(
        SavingsProduct, on_delete=models.PROTECT, related_name='savings_accounts'
    )
    account = models.OneToOneField(
        'accounts.Account',
        on_delete=models.PROTECT,
        related_name='savings_account',
        help_text='Posting account behind this savings account.',
    )
    branch = models.ForeignKey(
        'organization.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='savings_accounts',
    )
    opened_on = models.DateField(default=date.today)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['-opened_on']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return f'{self.member} — {self.account_no}'

    def clean(self):
        if self.product and self.opened_on:
            min_opening = self.product.min_opening_balance
            balance = self.account.balance.current_balance
            if self.status == 'active' and min_opening > 0 and balance < min_opening:
                raise ValidationError(
                    f'Opening balance below minimum {min_opening} for product {self.product.code}.'
                )
