"""
Serializers for recurring transaction data.
"""

from decimal import Decimal
from rest_framework import serializers
from ..models import RecurringTransaction


class RecurringTransactionSerializer(serializers.ModelSerializer):
    """Serializer for recurring transaction patterns."""

    monthly_cost = serializers.SerializerMethodField()
    yearly_cost = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    days_until_next = serializers.SerializerMethodField()

    class Meta:
        model = RecurringTransaction
        fields = [
            'id',
            'description',
            'merchant_name',
            'display_name',
            'amount',
            'frequency',
            'next_expected_date',
            'last_occurrence_date',
            'occurrence_count',
            'confidence_score',
            'is_active',
            'is_ignored',
            'user_notes',
            'similar_descriptions',
            'transaction_ids',
            'is_overdue',
            'days_until_next',
            'monthly_cost',
            'yearly_cost',
            'detected_at',
        ]
        read_only_fields = [
            'id',
            'description',
            'similar_descriptions',
            'transaction_ids',
            'detected_at',
        ]

    def get_display_name(self, obj):
        """Get the best display name for this recurring transaction."""
        return obj.get_display_name()

    def get_is_overdue(self, obj):
        """Check if this recurring transaction is overdue."""
        return obj.is_overdue()

    def get_days_until_next(self, obj):
        """Days until next expected occurrence."""
        return obj.days_until_next()

    def get_monthly_cost(self, obj):
        """Calculate monthly cost equivalent."""
        if obj.frequency == 'weekly':
            return float(obj.amount * Decimal('4.33'))
        elif obj.frequency == 'bi-weekly':
            return float(obj.amount * Decimal('2.17'))
        elif obj.frequency == 'monthly':
            return float(obj.amount)
        elif obj.frequency == 'quarterly':
            return float(obj.amount / Decimal('3'))
        elif obj.frequency == 'yearly':
            return float(obj.amount / Decimal('12'))
        return 0.0

    def get_yearly_cost(self, obj):
        """Calculate yearly cost equivalent."""
        if obj.frequency == 'weekly':
            return float(obj.amount * Decimal('52'))
        elif obj.frequency == 'bi-weekly':
            return float(obj.amount * Decimal('26'))
        elif obj.frequency == 'monthly':
            return float(obj.amount * Decimal('12'))
        elif obj.frequency == 'quarterly':
            return float(obj.amount * Decimal('4'))
        elif obj.frequency == 'yearly':
            return float(obj.amount)
        return 0.0


class RecurringTransactionSummarySerializer(serializers.Serializer):
    """Summary statistics for recurring transactions."""

    total_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    monthly_recurring_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    yearly_recurring_cost = serializers.DecimalField(max_digits=12, decimal_places=2)

    by_frequency = serializers.DictField(child=serializers.DictField())

    top_recurring = serializers.ListField(
        child=RecurringTransactionSerializer(),
        required=False
    )
    overdue_count = serializers.IntegerField()

