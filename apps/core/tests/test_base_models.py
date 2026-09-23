from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.models import soft_delete_state_constraint
from apps.identity.models import User
from apps.members.models import Member


class SoftDeleteStateConstraintTests(TestCase):
    def test_constraint_declared_on_member_and_user(self):
        names = {
            constraint.name for constraint in Member._meta.constraints + User._meta.constraints
        }
        self.assertIn('members_member_soft_delete_state', names)
        self.assertIn('identity_user_soft_delete_state', names)

    def test_factory_uses_app_and_class_interpolation(self):
        constraint = soft_delete_state_constraint()
        self.assertEqual(constraint.name, '%(app_label)s_%(class)s_soft_delete_state')

    def test_consistent_alive_row_is_allowed(self):
        Member.objects.create(first_name='A', last_name='B')
        self.assertEqual(Member.objects.all_with_deleted().count(), 1)

    def test_consistent_deleted_row_is_allowed(self):
        member = Member.objects.create(first_name='A', last_name='B')
        member.soft_delete()
        self.assertTrue(Member.objects.all_with_deleted().get(pk=member.pk).is_deleted)

    def test_deleted_flag_without_timestamp_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Member.objects.all_with_deleted().create(
                    first_name='A', last_name='B', is_deleted=True, deleted_at=None
                )

    def test_alive_flag_with_timestamp_rejected(self):
        from django.utils import timezone

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Member.objects.all_with_deleted().create(
                    first_name='A', last_name='B', is_deleted=False, deleted_at=timezone.now()
                )


class TimestampedModelTests(TestCase):
    def test_timestamps_populated_on_create(self):
        member = Member.objects.create(first_name='A', last_name='B')
        member.refresh_from_db()
        self.assertIsNotNone(member.created_at)
        self.assertIsNotNone(member.updated_at)

    def test_updated_at_changes_on_save(self):
        member = Member.objects.create(first_name='A', last_name='B')
        original_updated = member.updated_at
        Member.objects.filter(pk=member.pk).update(last_name='C')
        member.refresh_from_db()
        self.assertGreaterEqual(member.updated_at, original_updated)
