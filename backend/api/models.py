from django.conf import settings
from django.db import models
from django.utils import timezone


class DeviceToken(models.Model):
	class Provider(models.TextChoices):
		FCM = 'fcm', 'Firebase Cloud Messaging'

	class Platform(models.TextChoices):
		IOS = 'ios', 'iOS'
		ANDROID = 'android', 'Android'
		WEB = 'web', 'Web'

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='device_tokens',
	)
	token = models.CharField(max_length=512, unique=True)
	provider = models.CharField(
		max_length=32,
		choices=Provider.choices,
		default=Provider.FCM,
	)
	platform = models.CharField(max_length=32, choices=Platform.choices)
	is_active = models.BooleanField(default=True)
	last_seen_at = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f'{self.platform}:{self.provider}:{self.user_id}'
