from django.contrib.auth.models import UserManager


class SoftDeleteManager(UserManager):
    """
    Custom manager that automatically excludes soft-deleted users.

    All queries through this manager will only return active,
    non-deleted users. Use .all_with_deleted() to include them.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)


class CustomUserManager(SoftDeleteManager):
    """Manager that combines soft-delete filtering with email-based user creation."""

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('username', email)
        return super().create_user(
            username=extra_fields.pop('username'),
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('username', email)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(
            username=extra_fields.pop('username'),
            email=email,
            password=password,
            **extra_fields,
        )
