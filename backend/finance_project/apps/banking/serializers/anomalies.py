"""
Serializers for anomaly detection data.
"""

from rest_framework import serializers
from ..models import Anomaly, AnomalyNotification, UserAnomalyPreferences


class AnomalySerializer(serializers.ModelSerializer):
    """Serializer for anomalies."""

    transaction_description = serializers.SerializerMethodField()
    recurring_display_name = serializers.SerializerMethodField()

    class Meta:
        model = Anomaly
        fields = [
            'id',
            'anomaly_type',
            'severity',
            'title',
            'description',
            'reason',
            'anomaly_score',
            'expected_value',
            'actual_value',
            'deviation_percent',
            'context_data',
            'transaction_id',
            'recurring_id',
            'transaction_description',
            'recurring_display_name',
            'is_dismissed',
            'is_false_positive',
            'is_confirmed',
            'dismissed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'anomaly_score',
            'expected_value',
            'actual_value',
            'deviation_percent',
            'context_data',
        ]

    def get_transaction_description(self, obj):
        """Get description of related transaction."""
        if obj.transaction:
            return obj.transaction.description or obj.transaction.reference
        return None

    def get_recurring_display_name(self, obj):
        """Get display name of related recurring transaction."""
        if obj.recurring:
            return obj.recurring.get_display_name()
        return None


class AnomalyDetailSerializer(AnomalySerializer):
    """Extended serializer with more detail."""

    transaction = serializers.SerializerMethodField()
    recurring = serializers.SerializerMethodField()

    class Meta(AnomalySerializer.Meta):
        fields = AnomalySerializer.Meta.fields + ['transaction', 'recurring']

    def get_transaction(self, obj):
        """Get full transaction data if related."""
        if obj.transaction:
            from . import TransactionSerializer
            return TransactionSerializer(obj.transaction).data
        return None

    def get_recurring(self, obj):
        """Get full recurring transaction data if related."""
        if obj.recurring:
            from .recurring import RecurringTransactionSerializer
            return RecurringTransactionSerializer(obj.recurring).data
        return None


class AnomalyNotificationSerializer(serializers.ModelSerializer):
    """Serializer for anomaly notifications."""

    anomaly = AnomalySerializer(read_only=True)

    class Meta:
        model = AnomalyNotification
        fields = [
            'id',
            'anomaly',
            'is_read',
            'is_notified_via_email',
            'is_notified_via_push',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'anomaly',
            'is_notified_via_email',
            'is_notified_via_push',
        ]


class UserAnomalyPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user anomaly preferences."""

    class Meta:
        model = UserAnomalyPreferences
        fields = [
            'id',
            'anomaly_detection_enabled',
            'notify_on_critical',
            'notify_on_warning',
            'notify_on_info',
            'email_notifications',
            'push_notifications',
            'sensitivity',
            'enabled_types',
            'amount_deviation_percent',
            'spending_spike_multiplier',
            'days_before_inactive',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnomalyStatsSerializer(serializers.Serializer):
    """Serializer for anomaly statistics."""

    total_anomalies = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()
    info_count = serializers.IntegerField()
    dismissed_count = serializers.IntegerField()
    confirmed_count = serializers.IntegerField()
    false_positive_count = serializers.IntegerField()
    top_types = serializers.DictField()
    severity_trend = serializers.ListField()

