from .models import Member


def get_active_members():
    """Return all non-deleted members with their linked account, newest first."""
    return Member.objects.select_related('user').order_by('-join_date')


def get_member_by_id(member_id):
    """Return a single non-deleted member with its linked account, or None."""
    return Member.objects.select_related('user').filter(pk=member_id).first()


def get_linked_user(member):
    """Return the authenticated user bound to this member, if any."""
    return getattr(member, 'user', None)


def delete_member(member):
    """Soft delete a member, retaining the record for audit trails."""
    member.soft_delete()


def member_no_exists(member_no):
    """Check if the given member number is already in use (including deleted)."""
    return Member.objects.all_with_deleted().filter(member_no__iexact=member_no.strip()).exists()
