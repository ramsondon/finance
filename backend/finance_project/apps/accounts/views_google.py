"""
View to redirect directly to Google OAuth without showing an intermediate page
"""
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def google_oauth_redirect(request):
    """
    Redirects directly to the allauth Google login endpoint.
    This bypasses our login page and goes straight to Google OAuth.
    """
    # Simply redirect to allauth's Google login handler
    # The ?process=login parameter tells allauth to initiate OAuth
    return redirect('/accounts/google/login/?process=login')

