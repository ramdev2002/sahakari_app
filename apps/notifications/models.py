import uuid

from django.db import models

NOTIFICATION_TYPES = [
    ('transaction', 'Transaction'),
    ('approval', 'Approval'),
    ('member', 'Member'),
    ('loan', 'Loan'),
    ('system', 'System'),
]


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'identity.User', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default='system'
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.title}'

    @property
    def is_read(self):
        return self.read_at is not None
