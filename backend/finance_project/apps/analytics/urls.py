from django.urls import path
from .views import OverviewStatsView, AccountBalanceTimeseriesView

urlpatterns = [
    path("overview", OverviewStatsView.as_view(), name="overview-stats"),
    path("accounts/<int:account_id>/balance-timeseries/", AccountBalanceTimeseriesView.as_view(), name="account-balance-timeseries"),
]

