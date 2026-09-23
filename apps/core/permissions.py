from rest_framework.permissions import BasePermission

from .constants import GROUP_ADMINISTRATIVE_OFFICER


def _is_in_group(user, group_name):
    """Check if a user belongs to the given group."""
    return user.groups.filter(name=group_name).exists()


class IsSuperUser(BasePermission):
    """Allow access only to superusers (Django's is_superuser flag)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsStaffUser(BasePermission):
    """Allow access to any authenticated staff user (is_staff)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdministrativeOfficer(BasePermission):
    """Allow access to superusers and Administrative Officer group members."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.is_superuser or _is_in_group(request.user, GROUP_ADMINISTRATIVE_OFFICER)


class IsSuperUserOrAdministrativeOfficer(IsAdministrativeOfficer):
    """Alias for IsAdministrativeOfficer (superuser or officer in group)."""


class IsOwnerOrSuperUser(BasePermission):
    """
    Object-level permission: allow the user themselves or a superuser.

    Used for retrieve/update/delete on individual objects.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.pk == request.user.pk
