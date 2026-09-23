"""Approval workflow services."""

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.core.constants import ROLE_CHOICES

from .models import ApprovalRequest, ApprovalRule

APPROVAL_ERROR_MESSAGES = {
    'not_pending': 'Only pending requests can be decided.',
    'duplicate': 'A pending request already exists for this entity/action.',
}


def request_approval(*, entity_type, entity_id, action, requested_by=None, note=''):
    with db_transaction.atomic():
        existing = ApprovalRequest.objects.filter(
            entity_type=entity_type, entity_id=str(entity_id), action=action, status='pending'
        ).first()
        if existing:
            return existing, False
        approval = ApprovalRequest.objects.create(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            requested_by=requested_by,
            note=note,
        )
    return approval, True


def _can_review(user, approval):
    if user.is_superuser:
        return True
    rule = ApprovalRule.objects.filter(action=approval.action, is_active=True).first()
    if rule is None:
        return True  # no rule configured: superuser-level decision allowed
    return (
        user.groups.filter(name=rule.role).exists()
        or user.groups.filter(name__in=ROLE_CHOICES.values()).filter(name=rule.role).exists()
    )


def decide(approval, *, decision, reviewer, comment=''):
    if approval.status != 'pending':
        raise ValueError(APPROVAL_ERROR_MESSAGES['not_pending'])
    if not _can_review(reviewer, approval):
        raise PermissionError('Reviewer lacks the role for this action.')
    approval.status = decision
    approval.reviewed_by = reviewer
    approval.reviewed_at = timezone.now()
    approval.review_comment = comment
    approval.save(
        update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment', 'updated_at']
    )
    return approval


def cancel(approval, reviewer, comment=''):
    if approval.status != 'pending':
        raise ValueError(APPROVAL_ERROR_MESSAGES['not_pending'])
    approval.status = 'cancelled'
    approval.reviewed_by = reviewer
    approval.reviewed_at = timezone.now()
    approval.review_comment = comment
    approval.save(
        update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment', 'updated_at']
    )
    return approval
