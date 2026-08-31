from django.db.models import Q

from .models import User


class UserService:
    """
    Business logic for User operations.

    Keeps the view and serializer layers thin by handling queryset filtering,
    soft delete logic, and future business rules.
    """

    @staticmethod
    def get_active_users():
        """Return queryset of all non-deleted active users."""
        return User.objects.all()

    @staticmethod
    def get_user_by_id(user_id):
        """Return a single non-deleted user or None."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def delete_user(user):
        """
        Soft delete a user.

        Retains the record for audit trails and referential integrity
        while marking it as inactive and excluded from normal queries.
        """
        user.soft_delete()

    @staticmethod
    def email_exists(email, include_deleted=True):
        """Check if a user with the given email already exists."""
        if include_deleted:
            return User.objects.all_with_deleted().filter(email=email).exists()
        return User.objects.filter(email=email).exists()

    @staticmethod
    def search_users(query):
        """Search users by name or email."""
        return User.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query),
        )
