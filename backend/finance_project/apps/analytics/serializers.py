from rest_framework import serializers


class OverviewResponseSerializer(serializers.Serializer):
    total_balance = serializers.FloatField()
    total_balance_currency = serializers.CharField(default="USD")
    income_expense_breakdown = serializers.DictField(child=serializers.FloatField())
    income_change_percent = serializers.FloatField(allow_null=True)
    expense_change_percent = serializers.FloatField(allow_null=True)
    monthly_trends = serializers.ListField(child=serializers.DictField(), default=list)


class SpendingTrendResponseSerializer(serializers.Serializer):
    """Response for spending trends and forecast endpoint."""
    current_period_expense = serializers.FloatField()
    previous_period_expense = serializers.FloatField()
    trend_percent = serializers.FloatField()
    daily_average = serializers.FloatField()
    forecast_month_end = serializers.FloatField()
    days_in_period = serializers.IntegerField()
    days_elapsed = serializers.IntegerField()
    is_trending_up = serializers.BooleanField()


class CashFlowResponseSerializer(serializers.Serializer):
    """Response for cash flow visualization endpoint."""
    income = serializers.FloatField()
    expense = serializers.FloatField()
    net_flow = serializers.FloatField()
    savings_rate = serializers.FloatField()  # percentage
    burn_rate = serializers.FloatField()  # monthly expense rate
    balance_change = serializers.FloatField()  # change from period start to end


class DashboardWidgetResponseSerializer(serializers.Serializer):
    """Response for comprehensive dashboard widget data."""
    overview = OverviewResponseSerializer()
    spending_trend = SpendingTrendResponseSerializer()
    cash_flow = CashFlowResponseSerializer()
    timestamp = serializers.DateTimeField()


