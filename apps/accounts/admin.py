from django.contrib import admin

from .models import Account, AccountBalance, AccountType


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'side', 'category', 'is_system', 'status', 'is_deleted')
    list_filter = ('side', 'category', 'is_system', 'status', 'is_deleted')
    search_fields = ('code', 'name')


class AccountBalanceInline(admin.TabularInline):
    model = AccountBalance
    extra = 0
    can_delete = False
    readonly_fields = ('current_balance', 'available_balance')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_no',
        'name',
        'account_type',
        'member',
        'branch',
        'status',
        'is_deleted',
    )
    list_filter = ('account_type', 'status', 'is_deleted')
    search_fields = ('account_no', 'name')
    inlines = [AccountBalanceInline]


@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'current_balance', 'available_balance', 'updated_at')
    readonly_fields = ('current_balance', 'available_balance', 'updated_at')
