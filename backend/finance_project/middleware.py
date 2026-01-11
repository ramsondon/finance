"""
Middleware to allow specific paths to be embedded in iframes while maintaining security
"""
import logging

log = logging.getLogger(__name__)


class AllowIframeForOAuthMiddleware:
    """
    Allows specific views (like OAuth login) to be embedded in iframes
    while keeping DENY for other sensitive views.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that are allowed to be embedded in iframes
        self.allowed_iframe_paths = [
            '/',
            '/accounts/google/login/',
            '/accounts/login/',
        ]

    def __call__(self, request):
        response = self.get_response(request)

        # Check if current path is allowed to be in iframe
        path = request.path
        is_allowed = any(path.startswith(allowed) for allowed in self.allowed_iframe_paths)
        log.debug(f"AllowIframeForOAuthMiddleware: path={path}, is_allowed={is_allowed}")
        if is_allowed:
            # Allow embedding in iframes for OAuth pages
            response['X-Frame-Options'] = 'SAMEORIGIN'
        else:
            # Keep DENY for all other pages (default Django security)
            response['X-Frame-Options'] = 'DENY'

        return response
