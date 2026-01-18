from django.urls import path
from .views import OverviewStatsView, AccountBalanceTimeseriesView, CategoryExpenseBreakdownView, SpendingTrendView, CashFlowView, MonthlyIncomeExpenseView

urlpatterns = [
    path("overview", OverviewStatsView.as_view(), name="overview-stats"),
    path("accounts/<int:account_id>/balance-timeseries/", AccountBalanceTimeseriesView.as_view(), name="account-balance-timeseries"),
    path("category-expense/", CategoryExpenseBreakdownView.as_view(), name="category-expense-breakdown"),
    path("spending-trend/", SpendingTrendView.as_view(), name="spending-trend"),
    path("cash-flow/", CashFlowView.as_view(), name="cash-flow"),
    path("monthly-income-expense/", MonthlyIncomeExpenseView.as_view(), name="monthly-income-expense"),
]
