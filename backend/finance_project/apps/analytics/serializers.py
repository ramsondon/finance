from rest_framework import serializers


class OverviewResponseSerializer(serializers.Serializer):
    total_balance = serializers.FloatField()
    total_balance_currency = serializers.CharField(default="USD")
    income_expense_breakdown = serializers.DictField(child=serializers.FloatField())
    income_change_percent = serializers.FloatField(allow_null=True)
    expense_change_percent = serializers.FloatField(allow_null=True)
    monthly_trends = serializers.ListField(child=serializers.DictField(), default=list)

