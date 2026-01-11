from rest_framework import serializers
from .models import UserProfile, AllowedGoogleUser


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "user", "currency_preference", "preferences"]
        read_only_fields = ["user"]


class AllowedGoogleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedGoogleUser
        fields = ["id", "email", "active"]

