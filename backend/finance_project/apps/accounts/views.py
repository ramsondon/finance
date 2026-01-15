from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from allauth.socialaccount.models import SocialAccount
from .models import UserProfile, AllowedGoogleUser
from .serializers import UserProfileSerializer, AllowedGoogleUserSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AllowedGoogleUserViewSet(viewsets.ModelViewSet):
    queryset = AllowedGoogleUser.objects.all()
    serializer_class = AllowedGoogleUserSerializer
    permission_classes = [IsStaffOrReadOnly]


class AuthStatusViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current authenticated user info"""
        social = SocialAccount.objects.filter(user=request.user, provider="google").first()
        data = {
            "username": request.user.username,
            "email": request.user.email,
            "google_connected": bool(social),
            "allowlist_enabled": getattr(settings, "ALLOWLIST_ENABLED", False),
            "is_authenticated": True,
        }
        return Response(data)

    @action(detail=False, methods=["get"], url_path="check", permission_classes=[permissions.AllowAny])
    def check(self, request):
        """Check if user is authenticated (public endpoint)"""
        if request.user.is_authenticated:
            social = SocialAccount.objects.filter(user=request.user, provider="google").first()
            data = {
                "username": request.user.username,
                "email": request.user.email,
                "google_connected": bool(social),
                "is_authenticated": True,
            }
            return Response(data)
        else:
            return Response({"is_authenticated": False})

    @action(detail=False, methods=["get", "post"], url_path="preferences", permission_classes=[permissions.IsAuthenticated])
    def preferences(self, request):
        """
        GET /api/accounts/auth/preferences/
            Get user's preferences from server (language, format settings, etc.)
            Returns: { "language": "de", "dateFormat": "DD.MM.YYYY", ... }

        POST /api/accounts/auth/preferences/
            Sync/update user's preferences on server
            Body: { "language": "de", "dateFormat": "DD.MM.YYYY", ... }
            Returns: Updated preferences
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        if request.method == 'GET':
            # Return current preferences
            return Response({
                "preferences": profile.preferences,
                "language": profile.get_language()
            })

        # POST: Update preferences
        data = request.data

        # Update individual preferences
        for key, value in data.items():
            profile.set_preference(key, value)

        return Response({
            "preferences": profile.preferences,
            "language": profile.get_language(),
            "message": "Preferences updated successfully"
        })

