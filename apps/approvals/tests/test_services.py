from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.approvals.models import ApprovalRequest, ApprovalRule
from apps.approvals.services import decide, request_approval

User = get_user_model()


class ApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.requester = User.objects.create_user(email='requester@example.com', password='x')
        self.reviewer = User.objects.create_superuser(email='boss@example.com', password='x')

    def test_request_approval_creates_pending(self):
        approval, created = request_approval(
            entity_type='loan', entity_id='LOAN-1', action='write_off', requested_by=self.requester
        )
        self.assertTrue(created)
        self.assertEqual(approval.status, 'pending')
        self.assertEqual(ApprovalRequest.objects.count(), 1)

    def test_duplicate_pending_is_ignored(self):
        request_approval(entity_type='loan', entity_id='LOAN-1', action='write_off')
        _, created = request_approval(entity_type='loan', entity_id='LOAN-1', action='write_off')
        self.assertFalse(created)
        self.assertEqual(ApprovalRequest.objects.count(), 1)

    def test_approve_sets_reviewer(self):
        approval, _ = request_approval(entity_type='loan', entity_id='LOAN-1', action='write_off')
        decide(approval, decision='approved', reviewer=self.reviewer, comment='ok')
        approval.refresh_from_db()
        self.assertEqual(approval.status, 'approved')
        self.assertEqual(approval.reviewed_by, self.reviewer)
        self.assertIsNotNone(approval.reviewed_at)

    def test_decide_rejects_already_decided(self):
        approval, _ = request_approval(entity_type='loan', entity_id='LOAN-1', action='write_off')
        decide(approval, decision='rejected', reviewer=self.reviewer)
        with self.assertRaises(ValueError):
            decide(approval, decision='approved', reviewer=self.reviewer)

    def test_non_reviewer_is_denied(self):
        ApprovalRule.objects.create(action='write_off', role='ADMIN')
        approval, _ = request_approval(entity_type='loan', entity_id='LOAN-1', action='write_off')
        with self.assertRaises(PermissionError):
            decide(approval, decision='approved', reviewer=self.requester)
