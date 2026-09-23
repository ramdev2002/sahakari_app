import uuid

from django.db import models

APPROVAL_STATUSES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]


class ApprovalRequest(models.Model):
    """A queued decision on a business action (loan approval, write-off...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=50)
    requested_by = models.ForeignKey(
        'identity.User', on_delete=models.SET_NULL, null=True, related_name='approval_requests'
    )
    status = models.CharField(
        max_length=20, choices=APPROVAL_STATUSES, default='pending', db_index=True
    )
    reviewed_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    review_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['entity_type', 'entity_id', 'action', 'status'],
                condition=models.Q(status='pending'),
                name='approval_unique_pending_per_entity',
            )
        ]

    def __str__(self):
        return f'{self.action} {self.entity_type}:{self.entity_id} ({self.status})'


class ApprovalRule(models.Model):
    """Role(s) entitled to act on a given action."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['action']

    def __str__(self):
        return f'{self.action} -> {self.role}'
