from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Account, AccountType
from apps.accounts.services import ensure_seed_accounts
from apps.ledger.models import Journal, LedgerEntry
from apps.ledger.services import LedgerError, get_account_balance, post_journal


class PostJournalTests(TestCase):
    def setUp(self):
        self.accounts = ensure_seed_accounts()
        self.cash = self.accounts['cash']

    def test_balanced_journal_creates_entries(self):
        journal = post_journal(
            legs=[
                {'account': self.cash, 'debit': Decimal('100.00'), 'credit': 0},
                {
                    'account': Account.objects.create(
                        account_no='T1',
                        name='Test',
                        account_type=AccountType.objects.get(code='SAVINGS'),
                    ),
                    'debit': 0,
                    'credit': Decimal('100.00'),
                },
            ],
            description='opening',
        )
        self.assertEqual(Journal.objects.count(), 1)
        self.assertEqual(journal.entries.count(), 2)
        self.assertTrue(journal.is_balanced)

    def test_unbalanced_journal_rejected(self):
        with self.assertRaises(LedgerError):
            post_journal(legs=[{'account': self.cash, 'debit': Decimal('10.00')}])

    def test_no_entries_rejected(self):
        with self.assertRaises(LedgerError):
            post_journal(legs=[])

    def test_both_sides_rejected(self):
        with self.assertRaises(LedgerError):
            post_journal(legs=[{'account': self.cash, 'debit': 1, 'credit': 1}])

    def test_invalid_money_rejected(self):
        with self.assertRaises(ValueError):
            post_journal(
                legs=[{'account': self.cash, 'debit': 1}, {'account': self.cash, 'credit': 'abc'}]
            )

    def test_single_side_db_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                journal = Journal.objects.create(journal_no='X')
                LedgerEntry.objects.create(journal=journal, account=self.cash, debit=1, credit=1)

    def test_get_account_balance_aggregates(self):
        savings = Account.objects.create(
            account_no='B1', name='B', account_type=AccountType.objects.get(code='SAVINGS')
        )
        post_journal(
            legs=[
                {'account': self.cash, 'debit': Decimal('10.00')},
                {'account': savings, 'credit': Decimal('10.00')},
            ]
        )
        post_journal(
            legs=[
                {'account': self.cash, 'debit': Decimal('5.00')},
                {'account': savings, 'credit': Decimal('5.00')},
            ]
        )
        self.assertEqual(get_account_balance(savings), Decimal('-15.00'))
        self.assertEqual(get_account_balance(self.cash), Decimal('15.00'))
