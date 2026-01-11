from rest_framework import serializers


class OverviewResponseSerializer(serializers.Serializer):
    total_balance = serializers.FloatField()
    income_expense_breakdown = serializers.DictField(child=serializers.FloatField())
    monthly_trends = serializers.ListField(child=serializers.DictField(), default=list)

