import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.constants import STATUS_CHOICES
from apps.core.models import SoftDeleteModel, soft_delete_state_constraint

from .managers import CustomUserManager


class User(AbstractUser, SoftDeleteModel):
    """
    Custom User model for the Sahakari cooperative management system.

    Uses email as the login identifier. Role (RBAC) is a single Group lookup
    plus Django's built-in permissions. Supports soft delete for audit trails.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        null=False,
        blank=False,
        error_messages={'unique': 'A user with this email already exists.'},
    )
    role = models.ForeignKey(
        'auth.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='Role of the user for access control.',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text='Status of the user account.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        constraints = [soft_delete_state_constraint()]

    def __str__(self):
        return self.email

    def soft_delete(self):
        """Soft delete and deactivate the account (blocks future logins)."""
        super().soft_delete()
        self.is_active = False
        self.save(update_fields=['is_active'])
