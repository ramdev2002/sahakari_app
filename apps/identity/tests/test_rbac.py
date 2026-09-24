"""RBAC authorization test suite verifying each identity type has
the correct permissions across the cooperative API."""

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants import ROLE_CHOICES
from apps.core.rbac import Role
from apps.identity.models import User
from apps.members.models import Member


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def make_user(role_name=None):
    """Create a normal user, optionally assign a role group."""
    if role_name in ROLE_CHOICES:
        role_name = ROLE_CHOICES[role_name]
    user = User.objects.create_user(
        email=f'{role_name or "user"}@example.com',
        password='pass123',
        first_name=role_name or 'User',
        last_name='Test',
    )
    if role_name:
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
    return user


def client_for(user):
    client = APIClient()
    tokens = get_tokens_for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    return client


def member_payload():
    return {'first_name': 'Ram', 'last_name': 'Tamang', 'phone': '9800000000'}


def user_payload():
    return {
        'email': 'new@example.com',
        'password': 'SecurePass123!',
        'first_name': 'New',
        'last_name': 'User',
    }


class RBACBase(TestCase):
    """Shared helpers for RBAC authorization tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            email='sysadmin@example.com', password='adminpass123'
        )

    def assert_allowed(self, client, method, url, data=None):
        res = client.generic(method, url, data or {}, format='json')
        self.assertNotIn(
            res.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED),
            msg=f'Expected permission to be allowed for {method} {url}, got {res.status_code}',
        )

    def assert_denied(self, client, method, url, data=None):
        res = client.generic(method, url, data or {}, format='json')
        self.assertEqual(
            res.status_code,
            status.HTTP_403_FORBIDDEN,
            msg=f'Expected 403 for {method} {url}, got {res.status_code}',
        )


class SystemAdminTests(RBACBase):
    """System Administrator (superuser) has full access to everything."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(cls.admin)

    def test_can_create_user(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('user-list'), user_payload())

    def test_can_list_users(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('user-list'))

    def test_can_create_member(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('member-list'), member_payload())


class BranchManagerTests(RBACBase):
    """Branch Manager can operate records but cannot administer users or products."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user(Role.BRANCH_MANAGER))

    def test_can_create_member(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('member-list'), member_payload())

    def test_can_list_members(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('member-list'))

    def test_can_list_users(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('user-list'))

    def test_cannot_create_user(self):
        self.assert_denied(self.auth_client, 'POST', reverse('user-list'), user_payload())

    def test_cannot_manage_products(self):
        self.assert_denied(
            self.auth_client,
            'POST',
            reverse('loan-product-list'),
            {'name': 'Test Product', 'code': 'TP001'},
        )


class LoanOfficerTests(RBACBase):
    """Loan Officer can create/approve loans but cannot create members or accept deposits."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user(Role.LOAN_OFFICER))

    def test_can_list_members(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('member-list'))

    def test_can_create_loan(self):
        self.assert_allowed(
            self.auth_client,
            'POST',
            reverse('loan-create-loan'),
            {'member': 1, 'product': 1, 'savings_account': 1, 'principal': 50000},
        )

    def test_cannot_create_member(self):
        self.assert_denied(self.auth_client, 'POST', reverse('member-list'), member_payload())

    def test_cannot_deposit(self):
        self.assert_denied(
            self.auth_client, 'POST', reverse('transaction-deposit'), {'account': 1, 'amount': 1000}
        )


class AccountOfficerTests(RBACBase):
    """Account Officer can create members/savings/deposits but cannot approve loans."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user(Role.ACCOUNT_OFFICER))

    def test_can_create_member(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('member-list'), member_payload())

    def test_can_list_members(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('member-list'))

    def test_cannot_approve_loan(self):
        self.assert_denied(self.auth_client, 'POST', reverse('loan-approve', kwargs={'pk': 1}))

    def test_cannot_reverse_transaction(self):
        self.assert_denied(
            self.auth_client,
            'POST',
            reverse('transaction-reverse', kwargs={'pk': 1}),
            {'reason': 'test'},
        )


class CashierTests(RBACBase):
    """Cashier can accept deposits but cannot transfer, create loans, or create members."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user(Role.CASHIER))

    def test_can_deposit(self):
        self.assert_allowed(
            self.auth_client, 'POST', reverse('transaction-deposit'), {'account': 1, 'amount': 1000}
        )

    def test_cannot_transfer(self):
        self.assert_denied(
            self.auth_client,
            'POST',
            reverse('transaction-transfer'),
            {'from_account': 1, 'to_account': 2, 'amount': 500},
        )

    def test_cannot_create_loan(self):
        self.assert_denied(
            self.auth_client,
            'POST',
            reverse('loan-create-loan'),
            {'member': 1, 'product': 1, 'savings_account': 1, 'principal': 50000},
        )

    def test_cannot_create_member(self):
        self.assert_denied(self.auth_client, 'POST', reverse('member-list'), member_payload())


class AuditorTests(RBACBase):
    """Auditor has read-only access to reports and records but cannot mutate."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user(Role.AUDITOR))

    def test_can_list_members(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('member-list'))

    def test_can_view_reports(self):
        self.assert_allowed(self.auth_client, 'GET', reverse('report-trial-balance'))

    def test_cannot_create_member(self):
        self.assert_denied(self.auth_client, 'POST', reverse('member-list'), member_payload())


class MemberRoleTests(RBACBase):
    """Members can view only their own records and cannot manage anything."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.member_user = make_user(Role.MEMBER)
        cls.auth_client = client_for(cls.member_user)

    def test_member_sees_only_own_records(self):
        own = Member.objects.create(user=self.member_user, **member_payload())
        other = Member.objects.create(first_name='Sita', last_name='Rai', phone='9811111111')
        res = self.auth_client.get(reverse('member-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [m['id'] for m in res.data['results']]
        self.assertIn(str(own.pk), ids)
        self.assertNotIn(str(other.pk), ids)

    def test_cannot_create_member(self):
        self.assert_denied(self.auth_client, 'POST', reverse('member-list'), member_payload())

    def test_cannot_create_user(self):
        self.assert_denied(self.auth_client, 'POST', reverse('user-list'), user_payload())


class AdministrativeOfficerTests(RBACBase):
    """Administrative Officer carries full admin powers (can manage users)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client = client_for(make_user('Administrative Officer'))

    def test_can_create_user(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('user-list'), user_payload())

    def test_can_manage_members(self):
        self.assert_allowed(self.auth_client, 'POST', reverse('member-list'), member_payload())
