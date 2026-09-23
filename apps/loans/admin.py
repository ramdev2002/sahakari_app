from django.contrib import admin

from .models import Loan, LoanProduct


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'min_amount',
        'max_amount',
        'interest_rate',
        'status',
        'is_deleted',
    )
    list_filter = ('status', 'is_deleted')
    search_fields = ('code', 'name')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'loan_no',
        'member',
        'product',
        'principal',
        'balance',
        'status',
        'disbursed_at',
        'created_at',
    )
    list_filter = ('status', 'product')
    search_fields = ('loan_no', 'member__member_no')

    def balance(self, obj):
        return obj.outstanding_principal
