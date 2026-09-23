from django.contrib import admin

from .models import ApprovalRequest, ApprovalRule


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'action',
        'entity_type',
        'entity_id',
        'status',
        'requested_by',
        'reviewed_by',
    )
    list_filter = ('status', 'action', 'created_at')
    search_fields = ('entity_id', 'action', 'note')


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ('action', 'role', 'is_active')
    list_filter = ('is_active',)
