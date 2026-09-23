from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import Account, AccountType
from apps.accounts.services import ensure_seed_accounts
from apps.audit.models import AuditLog, record_audit
from apps.transactions import services


class AuditLogTests(TestCase):
    def test_record_audit_creates_entry(self):
        record_audit(
            action='post',
            entity_type='transaction',
            entity_id='TXN-1',
            summary='posted',
            detail={'kind': 'deposit'},
        )
        self.assertEqual(AuditLog.objects.count(), 1)
        entry = AuditLog.objects.first()
        self.assertEqual(entry.action, 'post')
        self.assertEqual(entry.entity_id, 'TXN-1')

    def test_transaction_signalled_into_audit(self):
        ensure_seed_accounts()
        sav = Account.objects.create(
            account_no='AUD-SAV', name='S', account_type=AccountType.objects.get(code='SAVINGS')
        )
        services.deposit(account=sav, amount=Decimal('50.00'))
        self.assertTrue(AuditLog.objects.filter(entity_type='transaction', action='post').exists())

    def test_final_transaction_reverse_audited(self):
        ensure_seed_accounts()
        sav = Account.objects.create(
            account_no='AUD-SAV2', name='S', account_type=AccountType.objects.get(code='SAVINGS')
        )
        tx = services.deposit(account=sav, amount=Decimal('25.00'))
        services.reverse(transaction=tx, reason='void')
        self.assertTrue(
            AuditLog.objects.filter(entity_type='transaction', action='reverse').exists()
        )
