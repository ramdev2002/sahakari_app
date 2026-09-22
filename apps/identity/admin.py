from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = [
        'email', 'role', 'status', 'first_name', 'last_name',
        'is_active', 'is_staff', 'is_superuser', 'is_deleted',
    ]
    list_filter = ['status', 'role', 'is_active', 'is_staff', 'is_superuser', 'is_deleted']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role & Status', {'fields': ('role', 'status')}),
        (
            'Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('Soft Delete', {'fields': ('is_deleted', 'deleted_at')}),
    )
