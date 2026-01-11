from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator


def health(request):
    return JsonResponse({"status": "OK"})


# Decorate TemplateView to ensure CSRF cookie is set
class CSRFTemplateView(TemplateView):
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/accounts/", include("finance_project.apps.accounts.urls")),
    path("api/banking/", include("finance_project.apps.banking.urls")),
    path("api/analytics/", include("finance_project.apps.analytics.urls")),
    path("api/ai/", include("finance_project.apps.ai.urls")),
    path("accounts/", include("allauth.urls")),
    # React SPA routes - serve the React app template for all these paths with CSRF token
    path("", CSRFTemplateView.as_view(template_name="base.html"), name="home"),
    path("login", CSRFTemplateView.as_view(template_name="base.html"), name="login"),
    path("dashboard", CSRFTemplateView.as_view(template_name="base.html"), name="dashboard"),
    path("transactions", CSRFTemplateView.as_view(template_name="base.html"), name="transactions"),
    path("rules", CSRFTemplateView.as_view(template_name="base.html"), name="rules"),
    path("insights", CSRFTemplateView.as_view(template_name="base.html"), name="insights"),
]
