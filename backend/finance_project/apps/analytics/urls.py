from django.urls import path
from .views import OverviewStatsView, AccountBalanceTimeseriesView, CategoryExpenseBreakdownView

urlpatterns = [
    path("overview", OverviewStatsView.as_view(), name="overview-stats"),
    path("accounts/<int:account_id>/balance-timeseries/", AccountBalanceTimeseriesView.as_view(), name="account-balance-timeseries"),
    path("category-expense/", CategoryExpenseBreakdownView.as_view(), name="category-expense-breakdown"),
]
