import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123', first_name='Test', last_name='User'
        )

    def test_create_user(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_user_uuid_pk(self):
        self.assertIsInstance(self.user.id, uuid.UUID)

    def test_user_str(self):
        self.assertEqual(str(self.user), 'test@example.com')

    def test_user_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'Test User')

    def test_password_hashed(self):
        self.assertNotEqual(self.user.password, 'testpass123')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com', password='adminpass123', first_name='Admin', last_name='User'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_duplicate_email_raises(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com', password='anotherpass', first_name='Dup', last_name='User'
            )

    def test_soft_delete(self):
        self.user.soft_delete()
        deleted = User.objects.all_with_deleted().get(pk=self.user.pk)
        self.assertTrue(deleted.is_deleted)
        self.assertIsNotNone(deleted.deleted_at)
        self.assertFalse(deleted.is_active)

    def test_soft_deleted_excluded_from_default_manager(self):
        self.user.soft_delete()
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_soft_deleted_accessible_via_all_with_deleted(self):
        self.user.soft_delete()
        self.assertTrue(User.objects.all_with_deleted().filter(pk=self.user.pk).exists())

    def test_soft_deleted_accessible_via_deleted_only(self):
        self.user.soft_delete()
        self.assertEqual(User.objects.deleted_only().count(), 1)
