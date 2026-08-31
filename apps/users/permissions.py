from rest_framework.permissions import BasePermission


GROUP_ADMINISTRATIVE_OFFICER = 'Administrative Officer'


class IsSuperUser(BasePermission):
    """Allow access only to superusers (Django's is_superuser flag)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsAdministrativeOfficer(BasePermission):
    """
    Allow access to users in the Administrative Officer group.

    Role is managed via Django's Group model, not a field on User.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.groups.filter(name=GROUP_ADMINISTRATIVE_OFFICER).exists()


class IsSuperUserOrAdministrativeOfficer(BasePermission):
    """
    Allow access to superusers and administrative officers.

    Used for user management operations (create, update, delete).
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            request.user.is_superuser
            or request.user.groups.filter(name=GROUP_ADMINISTRATIVE_OFFICER).exists()
        )


class IsOwnerOrSuperUser(BasePermission):
    """
    Object-level permission: allow the user themselves or a superuser.

    Used for retrieve/update/delete on individual user objects.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.pk == request.user.pk
