from django.contrib import admin

from .models import SavingsAccount, SavingsProduct


@admin.register(SavingsProduct)
class SavingsProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'interest_rate', 'min_opening_balance', 'status', 'is_deleted')
    list_filter = ('status', 'is_deleted')
    search_fields = ('code', 'name')


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_no',
        'member',
        'product',
        'branch',
        'opened_on',
        'status',
        'is_deleted',
    )
    list_filter = ('product', 'status', 'is_deleted')
    search_fields = ('account_no', 'member__member_no')
