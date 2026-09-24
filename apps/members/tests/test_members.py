from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.models import User
from apps.members.models import Member


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class MemberCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123'
        )
        self.tokens = get_tokens_for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.url = reverse('member-list')
        self.valid_data = {
            'first_name': 'Ram',
            'last_name': 'Tamang',
            'gender': 'male',
            'phone': '9800000000',
            'status': 'active',
        }

    def test_create_member_success(self):
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['full_name'], 'Ram Tamang')
        self.assertTrue(res.data['member_no'].startswith('MEM-'))
        self.assertEqual(res.data['status'], 'active')

    def test_create_member_auto_member_no(self):
        self.client.post(self.url, self.valid_data, format='json')
        member = Member.objects.get(first_name='Ram')
        self.assertTrue(member.member_no.startswith('MEM-'))

    def test_create_member_duplicate_member_no(self):
        Member.objects.create(member_no='MEM-1234567890', first_name='A')
        res = self.client.post(
            self.url, {**self.valid_data, 'member_no': 'MEM-1234567890'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_normal_user_cannot_create_member(self):
        normal = User.objects.create_user(email='normal@example.com', password='pass123')
        tokens = get_tokens_for_user(normal)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_create_member_fails(self):
        self.client.credentials()
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class MemberReadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='view@example.com', password='pass123')
        # Grant Account Officer role to allow member list/retrieve
        from django.contrib.auth.models import Group

        account_officer, _ = Group.objects.get_or_create(name='Account Officer')
        self.user.groups.add(account_officer)
        self.tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.member = Member.objects.create(first_name='Sita', last_name='Rai', phone='9811111111')
        self.member_url = reverse('member-detail', kwargs={'pk': self.member.pk})

    def test_list_members(self):
        res = self.client.get(reverse('member-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)

    def test_retrieve_member(self):
        res = self.client.get(self.member_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['full_name'], 'Sita Rai')

    def test_search_members(self):
        res = self.client.get(reverse('member-list'), {'search': 'Sita'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)


class MemberDeleteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123'
        )
        self.tokens = get_tokens_for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.member = Member.objects.create(first_name='Gopal', last_name='Gurung')
        self.member_url = reverse('member-detail', kwargs={'pk': self.member.pk})

    def test_soft_delete_member(self):
        res = self.client.delete(self.member_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        deleted = Member.objects.all_with_deleted().get(pk=self.member.pk)
        self.assertTrue(deleted.is_deleted)
        self.assertIsNotNone(deleted.deleted_at)

    def test_deleted_member_not_in_list(self):
        self.client.delete(self.member_url)
        res = self.client.get(reverse('member-list'))
        ids = [m['id'] for m in res.data['results']]
        self.assertNotIn(str(self.member.pk), ids)

    def test_reusable_soft_delete_manager_helpers(self):
        self.client.delete(self.member_url)
        self.assertEqual(Member.objects.all().count(), 0)
        self.assertEqual(Member.objects.all_with_deleted().count(), 1)
        self.assertEqual(Member.objects.deleted_only().count(), 1)

    def test_member_admin_update_via_disable(self):
        res = self.client.patch(
            self.member_url, {'status': 'inactive', 'phone': '9822222222'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertEqual(self.member.status, 'inactive')
        self.assertEqual(self.member.phone, '9822222222')
