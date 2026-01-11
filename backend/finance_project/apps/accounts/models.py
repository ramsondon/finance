from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    currency_preference = models.CharField(max_length=8, default="USD")
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Profile({self.user.username})"


class AllowedGoogleUser(models.Model):
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.email

