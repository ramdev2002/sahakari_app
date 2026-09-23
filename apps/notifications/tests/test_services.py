from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Account, AccountType
from apps.accounts.services import ensure_seed_accounts
from apps.notifications.models import Notification
from apps.notifications.services import mark_all_read, mark_read, notify
from apps.transactions import services

User = get_user_model()


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='x')

    def test_notify_creates_entry(self):
        item = notify(user=self.user, title='Hello', body='x')
        self.assertIsNotNone(item.pk)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertFalse(Notification.objects.first().is_read)

    def test_mark_read(self):
        item = notify(user=self.user, title='H')
        mark_read(item, self.user)
        item.refresh_from_db()
        self.assertTrue(item.is_read)

    def test_mark_all_read(self):
        notify(user=self.user, title='a')
        notify(user=self.user, title='b')
        count = mark_all_read(self.user)
        self.assertEqual(count, 2)
        self.assertEqual(self.user.notifications.filter(read_at__isnull=True).count(), 0)

    def test_cannot_mark_others_read(self):
        other = User.objects.create_user(email='o@example.com', password='x')
        item = notify(user=other, title='H')
        with self.assertRaises(ValueError):
            mark_read(item, self.user)


class TransactionNotificationTests(TestCase):
    def test_deposit_creates_notification(self):
        ensure_seed_accounts()
        user = User.objects.create_user(email='teller@example.com', password='x')
        sav = Account.objects.create(
            account_no='NTF-SAV', name='S', account_type=AccountType.objects.get(code='SAVINGS')
        )
        services.deposit(account=sav, amount=Decimal('10.00'), requested_by=user)
        self.assertTrue(
            Notification.objects.filter(user=user, notification_type='transaction').exists()
        )
