import uuid

from django.db import models

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, TimestampedModel, soft_delete_state_constraint


class Organization(SoftDeleteModel, TimestampedModel):
    """The cooperative itself (single tenancy stretched for multi-coop)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    registration_no = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['name']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return self.name


class Branch(SoftDeleteModel, TimestampedModel):
    """A cooperative branch; owns member/account/transaction context."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='branches',
        help_text='Owning cooperative.',
    )
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['code']
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return f'{self.code} — {self.name}'


class Department(SoftDeleteModel, TimestampedModel):
    """Internal department under a branch (loans, savings, accounts office)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', db_index=True
    )

    class Meta:
        ordering = ['code']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'code'], name='organization_department_branch_code_unique'
            ),
            soft_delete_state_constraint(),
        ]

    def __str__(self):
        return self.name
