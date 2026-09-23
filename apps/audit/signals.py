"""Signal wiring: every finalised transaction is mirrored into the audit trail."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.transactions.models import Transaction

from .models import record_audit


@receiver(post_save, sender=Transaction)
def audit_transaction(sender, instance, **kwargs):
    if kwargs.get('created'):
        # Creation records the 'initiated' state; finalisation is audited below.
        return
    if not instance.is_final:
        return
    if instance.status == 'reversed':
        record_audit(
            actor=instance.requested_by,
            action='reverse',
            entity_type='transaction',
            entity_id=instance.reference,
            summary=f'Transaction {instance.reference} reversed: {instance.error_message}',
        )
        return
    if instance.status == 'completed':
        record_audit(
            actor=instance.requested_by,
            action='post',
            entity_type='transaction',
            entity_id=instance.reference,
            summary=f'{instance.get_kind_display()} {instance.reference} {instance.status}',
            detail={'kind': instance.kind, 'status': instance.status},
        )
