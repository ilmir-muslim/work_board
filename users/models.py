from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    default_hourly_rate = models.FloatField(
        default=0.0, verbose_name="Ставка по умолчанию"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    telegram = models.CharField(max_length=20, blank=True, verbose_name="Telegram")

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"
