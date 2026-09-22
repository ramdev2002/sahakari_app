import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class User(AbstractUser):
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
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active',
        help_text='Status of the user account.',
    )
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


    def __str__(self):
        return self.email

    def soft_delete(self):
        """Mark user as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])
