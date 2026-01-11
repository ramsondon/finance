from rest_framework.routers import SimpleRouter
from django.urls import path, include
from .views import UserProfileViewSet, AllowedGoogleUserViewSet, AuthStatusViewSet

router = SimpleRouter()
router.register(r"profiles", UserProfileViewSet, basename="profile")
router.register(r"allowlist", AllowedGoogleUserViewSet, basename="allowlist")
router.register(r"auth", AuthStatusViewSet, basename="auth-status")

urlpatterns = [
    path("", include(router.urls)),
]
