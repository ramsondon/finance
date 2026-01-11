from rest_framework import serializers


class InsightsRequestSerializer(serializers.Serializer):
    timeframe = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False)


class InsightsResponseSerializer(serializers.Serializer):
    suggestions = serializers.ListField(child=serializers.CharField())
    analysis = serializers.CharField()

