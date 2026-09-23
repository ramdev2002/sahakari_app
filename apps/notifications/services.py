"""Notification delivery services."""

from django.utils import timezone

from .models import Notification


def notify(*, user, notification_type='system', title, body=''):
    if user is None:
        return None
    try:
        return Notification.objects.create(
            user=user, notification_type=notification_type, title=title, body=body
        )
    except Exception:
        return None


def notify_staff(*, staff_users, notification_type='system', title, body=''):
    created = []
    for user in staff_users:
        item = notify(user=user, notification_type=notification_type, title=title, body=body)
        if item:
            created.append(item)
    return created


def mark_read(notification, user):
    if notification.user_id != user.pk:
        raise ValueError('Cannot mark another user notification as read.')
    notification.read_at = timezone.now()
    notification.save(update_fields=['read_at'])
    return notification


def mark_all_read(user):
    return user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
