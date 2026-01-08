import uuid

from django.conf import settings
from django.db import models


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


# Create your models here.
