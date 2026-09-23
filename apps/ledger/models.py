import uuid

from django.db import models

from apps.core.models import TimestampedModel
from apps.core.money import MoneyField

entry_single_side = models.CheckConstraint(
    name='ledger_entry_single_side',
    condition=(
        models.Q(debit__gte=0, credit__gte=0)
        & (models.Q(debit__gt=0, credit=0) | models.Q(debit=0, credit__gt=0))
    ),
    violation_error_message='A ledger entry must debit or credit a single account.',
)

entry_non_negative = models.CheckConstraint(
    name='ledger_entry_non_negative',
    condition=models.Q(debit__gte=0, credit__gte=0),
    violation_error_message='Ledger amounts cannot be negative.',
)


class Journal(TimestampedModel):
    """An immutable double-entry batch; the book of record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_no = models.CharField(max_length=20, unique=True, blank=True)
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal',
    )
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.journal_no

    @property
    def totals(self):
        aggregates = self.entries.aggregate(
            debit_total=models.Sum('debit'), credit_total=models.Sum('credit')
        )
        return {
            'debit': aggregate_money(aggregates['debit_total']),
            'credit': aggregate_money(aggregates['credit_total']),
        }

    @property
    def is_balanced(self):
        totals = self.totals
        return totals['debit'] == totals['credit']


def aggregate_money(value):
    from decimal import Decimal

    return Decimal('0.00') if value is None else value


class LedgerEntry(models.Model):
    """A single double-entry line referencing one account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name='entries')
    account = models.ForeignKey(
        'accounts.Account', on_delete=models.PROTECT, related_name='ledger_entries', db_index=True
    )
    debit = MoneyField(default=0)
    credit = MoneyField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['journal__created_at', 'id']
        constraints = [entry_single_side, entry_non_negative]

    def __str__(self):
        return f'{self.journal.journal_no}: {self.debit} / {self.credit}'
