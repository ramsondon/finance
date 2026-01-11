from django.contrib import admin
from .models import UserProfile, AllowedGoogleUser


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "currency_preference")


@admin.register(AllowedGoogleUser)
class AllowedGoogleUserAdmin(admin.ModelAdmin):
    list_display = ("email", "active")
    list_filter = ("active",)
    search_fields = ("email",)

