from django.contrib import admin

from .models import Journal, LedgerEntry


class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 0
    can_delete = False
    readonly_fields = ('account', 'debit', 'credit', 'note')


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('journal_no', 'transaction', 'description', 'posted_at', 'is_balanced')
    search_fields = ('journal_no', 'description', 'reference')
    readonly_fields = ('journal_no', 'created_at', 'updated_at', 'is_balanced')
    inlines = [LedgerEntryInline]

    def posted_at(self, obj):
        return obj.created_at


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('journal', 'account', 'debit', 'credit', 'note')
    list_filter = ('account',)
    search_fields = ('account__account_no', 'note')
