import uuid

from django.db import models
from django.utils import timezone

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, TimestampedModel, soft_delete_state_constraint

GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]


class Member(SoftDeleteModel, TimestampedModel):
    """Cooperative member KYC record. Table retained as ``identity_member``."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member_no = models.CharField(max_length=20, unique=True, blank=True)
    user = models.OneToOneField(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member',
        help_text='Optional login account linked to this member.',
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(
        max_length=15, blank=True, help_text='Contact phone number for the member.'
    )
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='members/', blank=True, null=True)
    join_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        db_table = 'identity_member'
        ordering = ['-join_date']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return self.member_no

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def save(self, *args, **kwargs):
        if not self.member_no:
            self.member_no = f'MEM-{uuid.uuid4().hex[:10].upper()}'
        self.first_name = (self.first_name or '').strip()
        self.last_name = (self.last_name or '').strip()
        super().save(*args, **kwargs)
