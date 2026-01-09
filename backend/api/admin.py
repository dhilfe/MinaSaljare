from django.contrib import admin

from .models import DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
	list_display = ('user', 'platform', 'provider', 'is_active', 'last_seen_at')
	list_filter = ('platform', 'provider', 'is_active')
	search_fields = ('token', 'user__email')
