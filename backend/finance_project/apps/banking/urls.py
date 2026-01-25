from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import BankAccountViewSet, TransactionViewSet, CategoryViewSet, RuleViewSet, currencies_view, available_fields_view, GenerateRulesView
from .views.recurring import RecurringTransactionViewSet
from .views.anomalies import AnomalyViewSet, UserAnomalyPreferencesViewSet

router = SimpleRouter()
router.register(r"accounts", BankAccountViewSet, basename="bankaccount")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"rules", RuleViewSet, basename="rule")
router.register(r"recurring", RecurringTransactionViewSet, basename="recurring")
router.register(r"anomalies", AnomalyViewSet, basename="anomaly")
router.register(r"anomaly-preferences", UserAnomalyPreferencesViewSet, basename="anomaly-preferences")

urlpatterns = [
    path("rules/generate/", GenerateRulesView.as_view(), name="generate-rules"),
    path("", include(router.urls)),
    path("currencies", currencies_view, name="currencies"),
    path("available-fields", available_fields_view, name="available-fields"),
]
