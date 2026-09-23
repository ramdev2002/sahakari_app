"""Signal wiring: statuses users care about become notifications."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.transactions.models import Transaction

from .services import notify


@receiver(post_save, sender=Transaction)
def notify_on_transaction(sender, instance, **kwargs):
    if not instance.is_final or kwargs.get('created'):
        return
    user = instance.requested_by
    if user is None or instance.status not in ('completed', 'failed', 'reversed'):
        return
    state = instance.status
    notify(
        user=user,
        notification_type='transaction',
        title=f'Transaction {instance.reference} {state}',
        body=f'{instance.get_kind_display()} {instance.reference} is now {state}.',
    )
