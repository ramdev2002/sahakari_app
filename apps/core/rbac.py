"""Role-based access control policy for the cooperative application.

Identities (groups) are listed in ``Role``/``ROLE_CHOICES`` plus the legacy
``Administrative Officer`` group. Every group maps to a set of capabilities
that views enforce via the permission classes in ``apps.core.permissions``.
"""

from .constants import GROUP_ADMINISTRATIVE_OFFICER, ROLE_CHOICES, Role

# --- Capabilities -----------------------------------------------------------
VIEW_MEMBERS = 'members.view'
VIEW_OWN_MEMBERS = 'members.view_own'
MANAGE_MEMBERS = 'members.manage'

VIEW_SAVINGS = 'savings.view'
VIEW_OWN_SAVINGS = 'savings.view_own'
OPEN_SAVINGS = 'savings.open'

VIEW_LOANS = 'loans.view'
VIEW_OWN_LOANS = 'loans.view_own'
CREATE_LOANS = 'loans.create'
APPROVE_LOANS = 'loans.approve'
DISBURSE_LOANS = 'loans.disburse'
REPAY_LOANS = 'loans.repay'
CANCEL_LOANS = 'loans.cancel'

VIEW_TRANSACTIONS = 'transactions.view'
DEPOSIT = 'transactions.deposit'
WITHDRAW = 'transactions.withdraw'
TRANSFER = 'transactions.transfer'
REVERSE = 'transactions.reverse'

VIEW_USERS = 'users.view'
MANAGE_USERS = 'users.manage'

VIEW_REPORTS = 'reports.view'
VIEW_APPROVALS = 'approvals.view'
DECIDE_APPROVALS = 'approvals.decide'
MANAGE_APPROVALS = 'approvals.manage'

VIEW_AUDIT_LOGS = 'audit.view'
VIEW_LEDGER = 'ledger.view'

MANAGE_PRODUCTS = 'products.manage'
MANAGE_ACCOUNTS = 'accounts.manage'
MANAGE_ORGANIZATION = 'organization.manage'

_VIEW_CAPS = frozenset(
    [
        VIEW_MEMBERS,
        VIEW_SAVINGS,
        VIEW_LOANS,
        VIEW_REPORTS,
        VIEW_APPROVALS,
        VIEW_AUDIT_LOGS,
        VIEW_LEDGER,
        VIEW_USERS,
    ]
)

_LOAN_ACTIONS = frozenset([CREATE_LOANS, APPROVE_LOANS, DISBURSE_LOANS, REPAY_LOANS, CANCEL_LOANS])

_TRANSFER_ACTIONS = frozenset([DEPOSIT, WITHDRAW, TRANSFER, REVERSE])

_ALL_CAPABILITIES = (
    _VIEW_CAPS
    | _LOAN_ACTIONS
    | _TRANSFER_ACTIONS
    | frozenset(
        [
            VIEW_OWN_MEMBERS,
            VIEW_OWN_SAVINGS,
            VIEW_OWN_LOANS,
            MANAGE_MEMBERS,
            OPEN_SAVINGS,
            VIEW_TRANSACTIONS,
            MANAGE_USERS,
            DECIDE_APPROVALS,
            MANAGE_APPROVALS,
            MANAGE_PRODUCTS,
            MANAGE_ACCOUNTS,
            MANAGE_ORGANIZATION,
        ]
    )
)

# Roles that carry every capability (full administration).
ADMIN_GROUP_NAMES = frozenset([ROLE_CHOICES[Role.SYSTEM_ADMIN], GROUP_ADMINISTRATIVE_OFFICER])

# Role key -> role group name (identity types).
ROLE_GROUP_NAMES = {**ROLE_CHOICES}

# All seeded identity types (groups).
ALL_ROLE_GROUPS = frozenset(list(ROLE_CHOICES.values()) + [GROUP_ADMINISTRATIVE_OFFICER])

# Role key -> set of capabilities.
ROLE_CAPABILITIES = {
    Role.SYSTEM_ADMIN: _ALL_CAPABILITIES,
    Role.BRANCH_MANAGER: (
        _VIEW_CAPS
        | _LOAN_ACTIONS
        | _TRANSFER_ACTIONS
        | frozenset([VIEW_TRANSACTIONS, MANAGE_MEMBERS, OPEN_SAVINGS, DECIDE_APPROVALS])
    ),
    Role.LOAN_OFFICER: (
        frozenset(
            [VIEW_MEMBERS, VIEW_SAVINGS, VIEW_LOANS, VIEW_TRANSACTIONS, VIEW_USERS, VIEW_APPROVALS]
        )
        | _LOAN_ACTIONS
    ),
    Role.ACCOUNT_OFFICER: frozenset(
        [
            VIEW_MEMBERS,
            VIEW_SAVINGS,
            VIEW_LOANS,
            VIEW_TRANSACTIONS,
            VIEW_REPORTS,
            VIEW_USERS,
            MANAGE_MEMBERS,
            OPEN_SAVINGS,
            DEPOSIT,
            WITHDRAW,
            TRANSFER,
        ]
    ),
    Role.CASHIER: frozenset(
        [VIEW_MEMBERS, VIEW_SAVINGS, VIEW_LOANS, VIEW_TRANSACTIONS, DEPOSIT, WITHDRAW]
    ),
    Role.AUDITOR: frozenset(
        [VIEW_MEMBERS, VIEW_SAVINGS, VIEW_LOANS, VIEW_TRANSACTIONS, VIEW_REPORTS]
    )
    | _VIEW_CAPS,
    Role.MEMBER: frozenset([VIEW_OWN_MEMBERS, VIEW_OWN_SAVINGS, VIEW_OWN_LOANS]),
}


def role_group_names(user):
    """Return the set of group names the user belongs to (M2M groups + role FK)."""
    names = set(user.groups.values_list('name', flat=True))
    if user.role_id and user.role:
        names.add(user.role.name)
    return frozenset(name for name in names if name)


def capabilities_for(user):
    """Return the set of capabilities the user holds from its identity types."""
    if getattr(user, 'is_superuser', False):
        return set(_ALL_CAPABILITIES)
    caps = set()
    for group_name in role_group_names(user):
        if group_name in ADMIN_GROUP_NAMES:
            caps.update(_ALL_CAPABILITIES)
            continue
        role_key = next((key for key, name in ROLE_GROUP_NAMES.items() if name == group_name), None)
        if role_key and role_key in ROLE_CAPABILITIES:
            caps.update(ROLE_CAPABILITIES[role_key])
    return caps


def has_capability(user, capability):
    """True if the user holds the capability (superusers always do)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return capability in capabilities_for(user)
