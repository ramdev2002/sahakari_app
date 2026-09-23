import uuid

from django.db import models


class AuditLog(models.Model):
    """Append-only trail of business-critical events."""

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('post', 'Post'),
        ('reverse', 'Reverse'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        'identity.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, blank=True, db_index=True)
    summary = models.TextField(blank=True)
    detail = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-occurred_at']
        indexes = [models.Index(fields=['entity_type', 'entity_id'])]

    def __str__(self):
        return f'{self.action} {self.entity_type} by {self.actor or "system"}'


def record_audit(*, actor=None, action, entity_type, entity_id='', summary='', detail=None):
    """Persist an audit entry (never raises — failures must not break flows)."""
    from django.db import IntegrityError

    try:
        AuditLog.objects.create(
            actor=actor if actor and actor.pk else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id or ''),
            summary=summary,
            detail=detail or {},
        )
    except IntegrityError:
        pass
