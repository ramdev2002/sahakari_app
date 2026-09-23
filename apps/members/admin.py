from django.contrib import admin

from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'member_no',
        'get_full_name',
        'gender',
        'phone',
        'join_date',
        'status',
        'is_deleted',
    )
    list_filter = ('status', 'gender', 'is_deleted')
    search_fields = ('member_no', 'first_name', 'last_name', 'phone', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['-join_date']

    fieldsets = (
        (None, {'fields': ('member_no', 'user')}),
        (
            'Personal Info',
            {'fields': ('first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'photo')},
        ),
        ('Address', {'fields': ('address',)}),
        ('Membership', {'fields': ('join_date', 'status')}),
        ('Soft Delete', {'fields': ('is_deleted', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
