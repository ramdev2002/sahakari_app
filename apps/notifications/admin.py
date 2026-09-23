from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'notification_type', 'title', 'is_read')
    list_filter = ('notification_type', 'created_at')
    search_fields = ('title', 'body', 'user__username')
