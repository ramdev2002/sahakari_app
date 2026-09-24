from rest_framework.permissions import BasePermission

from .rbac import (
    APPROVE_LOANS,
    CANCEL_LOANS,
    CREATE_LOANS,
    DECIDE_APPROVALS,
    DEPOSIT,
    DISBURSE_LOANS,
    MANAGE_ACCOUNTS,
    MANAGE_APPROVALS,
    MANAGE_MEMBERS,
    MANAGE_ORGANIZATION,
    MANAGE_PRODUCTS,
    MANAGE_USERS,
    OPEN_SAVINGS,
    REPAY_LOANS,
    REVERSE,
    TRANSFER,
    VIEW_APPROVALS,
    VIEW_AUDIT_LOGS,
    VIEW_LEDGER,
    VIEW_LOANS,
    VIEW_MEMBERS,
    VIEW_OWN_LOANS,
    VIEW_OWN_MEMBERS,
    VIEW_OWN_SAVINGS,
    VIEW_REPORTS,
    VIEW_SAVINGS,
    VIEW_TRANSACTIONS,
    VIEW_USERS,
    WITHDRAW,
    has_capability,
)


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
    """Allow access to superusers and admin-level groups
    (System Administrator, Administrative Officer)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        from .rbac import ADMIN_GROUP_NAMES

        return bool(ADMIN_GROUP_NAMES & set(request.user.groups.values_list('name', flat=True)))


class IsSuperUserOrAdministrativeOfficer(IsAdministrativeOfficer):
    """Alias for IsAdministrativeOfficer (superuser or officer in admin-level group)."""


class IsOwnerOrSuperUser(BasePermission):
    """
    Object-level permission: allow the user themselves or a superuser.

    Used for retrieve/update/delete on individual objects.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.pk == request.user.pk


class HasCapability(BasePermission):
    """Allow if the user holds any of ``capabilities`` (superusers always allowed)."""

    capabilities = ()

    def has_permission(self, request, view):
        return bool(
            request.user and any(has_capability(request.user, cap) for cap in self.capabilities)
        )


class CanViewMembers(HasCapability):
    capabilities = (VIEW_MEMBERS, VIEW_OWN_MEMBERS)


class CanManageMembers(HasCapability):
    capabilities = (MANAGE_MEMBERS,)


class CanViewSavings(HasCapability):
    capabilities = (VIEW_SAVINGS, VIEW_OWN_SAVINGS)


class CanOpenSavings(HasCapability):
    capabilities = (OPEN_SAVINGS,)


class CanViewLoans(HasCapability):
    capabilities = (VIEW_LOANS, VIEW_OWN_LOANS)


class CanCreateLoans(HasCapability):
    capabilities = (CREATE_LOANS,)


class CanApproveLoans(HasCapability):
    capabilities = (APPROVE_LOANS,)


class CanDisburseLoans(HasCapability):
    capabilities = (DISBURSE_LOANS,)


class CanRepayLoans(HasCapability):
    capabilities = (REPAY_LOANS,)


class CanCancelLoans(HasCapability):
    capabilities = (CANCEL_LOANS,)


class CanViewTransactions(HasCapability):
    capabilities = (VIEW_TRANSACTIONS,)


class CanDeposit(HasCapability):
    capabilities = (DEPOSIT,)


class CanWithdraw(HasCapability):
    capabilities = (WITHDRAW,)


class CanTransfer(HasCapability):
    capabilities = (TRANSFER,)


class CanReverse(HasCapability):
    capabilities = (REVERSE,)


class CanViewUsers(HasCapability):
    capabilities = (VIEW_USERS,)


class CanManageUsers(HasCapability):
    capabilities = (MANAGE_USERS,)


class CanViewReports(HasCapability):
    capabilities = (VIEW_REPORTS,)


class CanViewApprovals(HasCapability):
    capabilities = (VIEW_APPROVALS,)


class CanDecideApprovals(HasCapability):
    capabilities = (DECIDE_APPROVALS,)


class CanManageApprovals(HasCapability):
    capabilities = (MANAGE_APPROVALS,)


class CanViewAuditLogs(HasCapability):
    capabilities = (VIEW_AUDIT_LOGS,)


class CanViewLedger(HasCapability):
    capabilities = (VIEW_LEDGER,)


class CanManageProducts(HasCapability):
    capabilities = (MANAGE_PRODUCTS,)


class CanManageAccounts(HasCapability):
    capabilities = (MANAGE_ACCOUNTS,)


class CanManageOrganization(HasCapability):
    capabilities = (MANAGE_ORGANIZATION,)


class CanViewOrSelfUser(HasCapability):
    """Authenticated users pass; object level additionally allows self."""

    capabilities = (VIEW_USERS,)

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return has_capability(request.user, VIEW_USERS) or obj.pk == request.user.pk


class CanManageOrOwnUser(HasCapability):
    """Authenticated users pass; object level allows managers and the user themselves."""

    capabilities = (MANAGE_USERS,)

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return has_capability(request.user, MANAGE_USERS) or obj.pk == request.user.pk
