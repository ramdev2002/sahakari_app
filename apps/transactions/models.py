import uuid

from django.db import models

TRANSACTION_KINDS = [
    ('deposit', 'Deposit'),
    ('withdrawal', 'Withdrawal'),
    ('transfer', 'Transfer'),
    ('reversal', 'Reversal'),
    ('disbursement', 'Loan Disbursement'),
    ('repayment', 'Loan Repayment'),
    ('fee', 'Fee'),
    ('interest', 'Interest Posting'),
]

TRANSACTION_STATUSES = [
    ('initiated', 'Initiated'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('cancelled', 'Cancelled'),
    ('reversed', 'Reversed'),
]

CHANNELS = [
    ('api', 'API'),
    ('web', 'Web Portal'),
    ('cashier', 'Cashier'),
    ('import', 'Bulk Import'),
    ('bank', 'Bank Transfer'),
]


class Transaction(models.Model):
    """Record of a user-originated financial event.

    Immutable once ``completed``; reversals are new transactions referencing
    the original journal.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=32, unique=True, blank=True)
    kind = models.CharField(max_length=20, choices=TRANSACTION_KINDS)
    status = models.CharField(
        max_length=20, choices=TRANSACTION_STATUSES, default='initiated', db_index=True
    )
    source_channel = models.CharField(max_length=20, choices=CHANNELS, default='api')
    idempotency_key = models.CharField(
        max_length=64, unique=True, null=True, blank=True, db_index=True
    )
    requested_by = models.ForeignKey(
        'identity.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    branch = models.ForeignKey(
        'organization.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
    )
    memo = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reference} ({self.kind})'

    @property
    def is_final(self):
        return self.status in ('completed', 'reversed', 'cancelled', 'failed')
