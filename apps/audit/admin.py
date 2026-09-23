from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'actor', 'action', 'entity_type', 'entity_id', 'summary')
    list_filter = ('action', 'entity_type', 'occurred_at')
    search_fields = ('entity_id', 'summary', 'actor__username')
    readonly_fields = (
        'actor',
        'action',
        'entity_type',
        'entity_id',
        'summary',
        'detail',
        'occurred_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
