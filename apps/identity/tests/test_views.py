from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants import GROUP_ADMINISTRATIVE_OFFICER
from apps.identity.models import User


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class UserCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123', first_name='Admin', last_name='User'
        )
        self.admin_tokens = get_tokens_for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.url = reverse('user-list')
        self.valid_data = {
            'first_name': 'Ramdev',
            'last_name': 'Tamang',
            'email': 'ramdev@example.com',
            'password': 'SecurePass123!',
        }

    def test_create_user_success(self):
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['email'], 'ramdev@example.com')
        self.assertNotIn('password', res.data)

    def test_create_user_duplicate_email(self):
        User.objects.create_user(
            email='ramdev@example.com', password='pass123', first_name='R', last_name='T'
        )
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_invalid_email(self):
        self.valid_data['email'] = 'not-an-email'
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_required_fields(self):
        res = self.client.post(self.url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_not_in_response(self):
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertNotIn('password', res.data)

    def test_create_user_password_hashed(self):
        self.client.post(self.url, self.valid_data, format='json')
        user = User.objects.get(email='ramdev@example.com')
        self.assertNotEqual(user.password, 'SecurePass123!')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_create_user_weak_password(self):
        self.valid_data['password'] = '123'
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_create_user_fails(self):
        self.client.credentials()
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_user_cannot_create_user(self):
        normal_user = User.objects.create_user(
            email='normal@example.com', password='pass123', first_name='Normal', last_name='User'
        )
        normal_tokens = get_tokens_for_user(normal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {normal_tokens["access"]}')
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrative_officer_can_create_user(self):
        officer = User.objects.create_user(
            email='officer@example.com', password='pass123', first_name='Officer', last_name='User'
        )
        admin_group, _ = Group.objects.get_or_create(name=GROUP_ADMINISTRATIVE_OFFICER)
        officer.groups.add(admin_group)
        officer_tokens = get_tokens_for_user(officer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {officer_tokens["access"]}')
        res = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_user_with_role_and_status(self):
        role = Group.objects.create(name='Manager')
        res = self.client.post(
            self.url,
            {
                'email': 'manager@example.com',
                'password': 'SecurePass123!',
                'first_name': 'Sam',
                'last_name': 'Sundar',
                'role_id': role.pk,
                'status': 'inactive',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['role_id'], role.pk)
        self.assertEqual(res.data['role'], 'Manager')
        self.assertEqual(res.data['status'], 'inactive')
        user = User.objects.get(email='manager@example.com')
        self.assertEqual(user.role, role)
        self.assertEqual(user.status, 'inactive')


class UserReadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )
        self.tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.user_url = reverse('user-detail', kwargs={'pk': self.user.pk})

    def test_list_users(self):
        res = self.client.get(reverse('user-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('results', res.data)

    def test_retrieve_user(self):
        res = self.client.get(self.user_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'test@example.com')
        self.assertEqual(res.data['first_name'], 'Test')
        self.assertEqual(res.data['last_name'], 'User')
        self.assertNotIn('password', res.data)

    def test_retrieve_nonexistent_user(self):
        res = self.client.get(
            reverse('user-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_list(self):
        self.client.credentials()
        res = self.client.get(reverse('user-list'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_users(self):
        res = self.client.get(reverse('user-list'), {'search': 'test'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_retrieve_user_role_and_status(self):
        role = Group.objects.create(name='Manager')
        self.user.role = role
        self.user.status = 'inactive'
        self.user.save()
        res = self.client.get(self.user_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['role_id'], role.pk)
        self.assertEqual(res.data['role'], 'Manager')
        self.assertEqual(res.data['status'], 'inactive')

    def test_ordering_users(self):
        res = self.client.get(reverse('user-list'), {'ordering': 'first_name'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me_endpoint(self):
        res = self.client.get(reverse('user-me'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'test@example.com')

    def test_me_unauthenticated(self):
        self.client.credentials()
        res = self.client.get(reverse('user-me'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class UserUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='Person',
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123', first_name='Admin', last_name='User'
        )
        self.tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.user_url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.other_url = reverse('user-detail', kwargs={'pk': self.other_user.pk})

    def test_patch_update_user(self):
        res = self.client.patch(self.user_url, {'first_name': 'Updated'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_put_update_user(self):
        data = {'first_name': 'Updated', 'last_name': 'Name'}
        res = self.client.put(self.user_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_cannot_update_other_user(self):
        res = self.client.patch(self.other_url, {'first_name': 'Hacked'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_other_user(self):
        admin_tokens = get_tokens_for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        res = self.client.patch(self.other_url, {'first_name': 'AdminUpdated'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_email_readonly(self):
        res = self.client.patch(self.user_url, {'email': 'new@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@example.com')


class PasswordUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )
        self.tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.user_url = reverse('user-detail', kwargs={'pk': self.user.pk})

    def test_password_update(self):
        res = self.client.patch(self.user_url, {'password': 'NewSecurePass456!'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass456!'))
        self.assertFalse(self.user.check_password('testpass123'))

    def test_password_not_returned_in_update_response(self):
        res = self.client.patch(self.user_url, {'password': 'NewSecurePass456!'}, format='json')
        self.assertNotIn('password', res.data)

    def test_weak_password_rejected(self):
        res = self.client.patch(self.user_url, {'password': '123'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class UserDeleteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123', first_name='Admin', last_name='User'
        )
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )
        self.admin_tokens = get_tokens_for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.user_url = reverse('user-detail', kwargs={'pk': self.user.pk})

    def test_delete_user(self):
        res = self.client.delete(self.user_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        deleted = User.objects.all_with_deleted().get(pk=self.user.pk)
        self.assertTrue(deleted.is_deleted)
        self.assertFalse(deleted.is_active)

    def test_deleted_user_not_in_list(self):
        self.client.delete(self.user_url)
        res = self.client.get(reverse('user-list'))
        ids = [u['id'] for u in res.data['results']]
        self.assertNotIn(str(self.user.pk), ids)

    def test_unauthorized_delete(self):
        normal_user = User.objects.create_user(
            email='normal@example.com', password='pass123', first_name='Normal', last_name='User'
        )
        normal_tokens = get_tokens_for_user(normal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {normal_tokens["access"]}')
        res = self.client.delete(self.user_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_delete(self):
        self.client.credentials()
        res = self.client.delete(self.user_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )

    def test_obtain_token(self):
        res = self.client.post(
            reverse('token_obtain_pair'),
            {'email': 'test@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_invalid_credentials(self):
        res = self.client.post(
            reverse('token_obtain_pair'),
            {'email': 'test@example.com', 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user(self):
        res = self.client.post(
            reverse('token_obtain_pair'),
            {'email': 'noone@example.com', 'password': 'pass'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        tokens = get_tokens_for_user(self.user)
        res = self.client.post(
            reverse('token_refresh'), {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_invalid_refresh_token(self):
        res = self.client.post(reverse('token_refresh'), {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_bearer_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        res = self.client.get(reverse('user-list'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
