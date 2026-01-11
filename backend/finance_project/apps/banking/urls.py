from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import BankAccountViewSet, TransactionViewSet, CategoryViewSet, RuleViewSet, currencies_view, available_fields_view

router = SimpleRouter()
router.register(r"accounts", BankAccountViewSet, basename="bankaccount")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"rules", RuleViewSet, basename="rule")

urlpatterns = [
    path("", include(router.urls)),
    path("currencies", currencies_view, name="currencies"),
    path("available-fields", available_fields_view, name="available-fields"),
]
