from django.contrib.auth.models import UserManager

from apps.core.models import SoftDeleteManager


class CustomUserManager(SoftDeleteManager, UserManager):
    """Email-based user creation combined with soft-delete filtering."""

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('username', email)
        return super().create_user(
            username=extra_fields.pop('username'), email=email, password=password, **extra_fields
        )

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('username', email)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(
            username=extra_fields.pop('username'), email=email, password=password, **extra_fields
        )
