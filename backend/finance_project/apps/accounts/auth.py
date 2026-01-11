from django.conf import settings
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseForbidden
from .models import AllowedGoogleUser


class AllowlistSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Enforce an optional allowlist for Google OAuth emails and customize user creation."""

    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        if getattr(settings, "ALLOWLIST_ENABLED", False):
            email = sociallogin.user.email
            if not AllowedGoogleUser.objects.filter(email__iexact=email, active=True).exists():
                raise ImmediateHttpResponse(HttpResponseForbidden("This Google account is not allowed."))
        return super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social account.
        Override to use email as username instead of first name.
        """
        user = super().populate_user(request, sociallogin, data)

        # Use email as username instead of first name
        if user.email:
            # Generate a username from email (before @ symbol)
            # Or use full email if you prefer
            user.username = user.email  # Use full email as username

            # Alternative: Use part before @ as username
            # user.username = user.email.split('@')[0]

        return user

