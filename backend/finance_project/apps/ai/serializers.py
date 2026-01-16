from rest_framework import serializers


class InsightsRequestSerializer(serializers.Serializer):
    timeframe = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    account_id = serializers.IntegerField(required=False, allow_null=True)  # Optional specific account


class InsightsResponseSerializer(serializers.Serializer):
    suggestions = serializers.ListField(child=serializers.CharField())
    analysis = serializers.CharField()

