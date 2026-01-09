import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Team(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	name = models.CharField(max_length=255)
	club_name = models.CharField(max_length=255, blank=True)

	coach = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='coached_teams',
	)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class Campaign(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	team = models.ForeignKey(
		Team,
		on_delete=models.PROTECT,
		related_name='campaigns',
	)

	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)

	start_date = models.DateField()
	end_date = models.DateField()

	default_target_units_per_child = models.PositiveIntegerField(default=0)
	buyout_amount_per_child = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	currency = models.CharField(max_length=10, default='SEK')

	is_active = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class Child(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	team = models.ForeignKey(
		Team,
		on_delete=models.PROTECT,
		related_name='children',
	)

	first_name = models.CharField(max_length=255)
	last_initial = models.CharField(max_length=10, blank=True)
	shirt_number = models.CharField(max_length=50, blank=True)

	is_active = models.BooleanField(default=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.first_name


class GuardianChildLink(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	guardian = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='child_links',
	)
	child = models.ForeignKey(
		Child,
		on_delete=models.PROTECT,
		related_name='guardian_links',
	)
	relationship = models.CharField(max_length=255, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['guardian', 'child'], name='uniq_guardian_child'),
		]


class ChildCampaignTarget(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	child = models.ForeignKey(
		Child,
		on_delete=models.PROTECT,
		related_name='campaign_targets',
	)
	campaign = models.ForeignKey(
		Campaign,
		on_delete=models.PROTECT,
		related_name='child_targets',
	)

	target_units = models.PositiveIntegerField(null=True, blank=True)
	buyout_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	has_paid_buyout = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['child', 'campaign'], name='uniq_child_campaign_target'),
		]


class Product(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	campaign = models.ForeignKey(
		Campaign,
		on_delete=models.PROTECT,
		related_name='products',
	)

	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)

	unit_price = models.DecimalField(max_digits=12, decimal_places=2)
	profit_per_unit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

	is_active = models.BooleanField(default=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class Sale(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	campaign = models.ForeignKey(
		Campaign,
		on_delete=models.PROTECT,
		related_name='sales',
	)
	child = models.ForeignKey(
		Child,
		on_delete=models.PROTECT,
		related_name='sales',
	)
	product = models.ForeignKey(
		Product,
		on_delete=models.PROTECT,
		related_name='sales',
	)

	quantity = models.PositiveIntegerField()
	total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

	buyer_name = models.CharField(max_length=255, blank=True)
	is_paid = models.BooleanField(default=False)
	is_delivered = models.BooleanField(default=False)

	recorded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='recorded_sales',
	)
	recorded_at = models.DateTimeField(default=timezone.now)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		if self.product_id and self.quantity is not None:
			unit_price = self.product.unit_price
			if not isinstance(unit_price, Decimal):
				unit_price = Decimal(str(unit_price))
			self.total_price = unit_price * Decimal(self.quantity)
		super().save(*args, **kwargs)


# Create your models here.
