from django.contrib import admin

from .models import Branch, Department, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'registration_no', 'email', 'status', 'is_deleted')
    list_filter = ('status', 'is_deleted')
    search_fields = ('name', 'code', 'registration_no')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'organization', 'phone', 'status', 'is_deleted')
    list_filter = ('organization', 'status', 'is_deleted')
    search_fields = ('code', 'name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'branch', 'status', 'is_deleted')
    list_filter = ('branch', 'status', 'is_deleted')
    search_fields = ('code', 'name')
