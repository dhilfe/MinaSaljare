from django.contrib import admin

from .models import (
		Campaign,
		Child,
		ChildCampaignTarget,
		GuardianChildLink,
		Product,
		Sale,
		Team,
)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
		list_display = ('name', 'club_name', 'coach', 'created_at', 'updated_at')
		list_filter = ('club_name',)
		search_fields = ('name', 'club_name', 'coach__email', 'coach__first_name', 'coach__last_name')
		autocomplete_fields = ('coach',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
		list_display = ('name', 'team', 'start_date', 'end_date', 'is_active', 'updated_at')
		list_filter = ('team', 'is_active', 'start_date', 'end_date')
		search_fields = ('name', 'team__name')
		autocomplete_fields = ('team',)


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
		list_display = ('first_name', 'last_initial', 'team', 'shirt_number', 'is_active', 'updated_at')
		list_filter = ('team', 'is_active')
		search_fields = ('first_name', 'last_initial', 'shirt_number', 'team__name')
		autocomplete_fields = ('team',)


@admin.register(GuardianChildLink)
class GuardianChildLinkAdmin(admin.ModelAdmin):
		list_display = ('guardian', 'child', 'relationship', 'created_at')
		list_filter = ('child__team',)
		search_fields = (
				'guardian__email',
				'guardian__first_name',
				'guardian__last_name',
				'child__first_name',
				'child__last_initial',
				'child__team__name',
		)
		autocomplete_fields = ('guardian', 'child')


@admin.register(ChildCampaignTarget)
class ChildCampaignTargetAdmin(admin.ModelAdmin):
		list_display = ('child', 'campaign', 'target_units', 'has_paid_buyout', 'updated_at')
		list_filter = ('campaign', 'child__team', 'has_paid_buyout')
		search_fields = ('child__first_name', 'child__last_initial', 'campaign__name', 'child__team__name')
		autocomplete_fields = ('child', 'campaign')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
		list_display = ('name', 'campaign', 'unit_price', 'profit_per_unit', 'is_active', 'updated_at')
		list_filter = ('campaign', 'campaign__team', 'is_active')
		search_fields = ('name', 'campaign__name', 'campaign__team__name')
		autocomplete_fields = ('campaign',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
		list_display = (
				'campaign',
				'child',
				'product',
				'quantity',
				'total_price',
				'is_paid',
				'is_delivered',
				'recorded_by',
				'recorded_at',
		)
		list_filter = ('campaign', 'campaign__team', 'product', 'is_paid', 'is_delivered', 'recorded_at')
		search_fields = (
				'child__first_name',
				'child__last_initial',
				'product__name',
				'buyer_name',
				'recorded_by__email',
		)
		date_hierarchy = 'recorded_at'
		autocomplete_fields = ('campaign', 'child', 'product', 'recorded_by')
