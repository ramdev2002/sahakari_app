GROUP_ADMINISTRATIVE_OFFICER = 'Administrative Officer'


class Role:
    SYSTEM_ADMIN = 'system_admin'
    BRANCH_MANAGER = 'branch_manager'
    LOAN_OFFICER = 'loan_officer'
    ACCOUNT_OFFICER = 'account_officer'
    CASHIER = 'cashier'
    AUDITOR = 'auditor'
    MEMBER = 'member'


ROLE_CHOICES = {
    Role.SYSTEM_ADMIN: 'System Administrator',
    Role.BRANCH_MANAGER: 'Branch Manager',
    Role.LOAN_OFFICER: 'Loan Officer',
    Role.ACCOUNT_OFFICER: 'Account Officer',
    Role.CASHIER: 'Cashier',
    Role.AUDITOR: 'Auditor',
    Role.MEMBER: 'Member',
}

# Staff-level roles that may operate cooperative accounts and records.
STAFF_ROLES = frozenset(
    [
        Role.SYSTEM_ADMIN,
        Role.BRANCH_MANAGER,
        Role.LOAN_OFFICER,
        Role.ACCOUNT_OFFICER,
        Role.CASHIER,
        Role.AUDITOR,
    ]
)

STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]
