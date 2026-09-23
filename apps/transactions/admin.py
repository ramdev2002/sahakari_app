from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'reference',
        'kind',
        'status',
        'source_channel',
        'branch',
        'requested_by',
        'created_at',
    )
    list_filter = ('kind', 'status', 'source_channel')
    search_fields = ('reference', 'idempotency_key', 'memo')
    readonly_fields = (
        'reference',
        'kind',
        'status',
        'idempotency_key',
        'requested_by',
        'branch',
        'source_channel',
        'created_at',
        'updated_at',
    )
