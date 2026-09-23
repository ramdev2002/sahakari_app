from .models import User


def get_active_users():
    """Return all non-deleted users with their role, newest first."""
    return User.objects.select_related('role').order_by('-date_joined')


def get_user_by_id(user_id):
    """Return a single non-deleted user with its role, or None."""
    return User.objects.select_related('role').filter(pk=user_id).first()


def delete_user(user):
    """Soft delete a user, retaining the record for audit trails."""
    user.soft_delete()


def email_exists(email, include_deleted=True):
    """Check if a user with the given email already exists."""
    qs = User.objects.all_with_deleted() if include_deleted else User.objects.all()
    return qs.filter(email__iexact=email.strip()).exists()
