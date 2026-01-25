"""
Anomaly detection service for financial data.

Detects various types of anomalies including:
- Unusual transaction amounts
- Spending spikes in categories
- Missing recurring payments
- New merchants
- Account inactivity
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Q, Avg, Max, Min, Count
from typing import List, Dict, Tuple, Optional
import statistics

from ..models import (
    Anomaly, AnomalyType, AnomalySeverity, UserAnomalyPreferences,
    Transaction, Category, BankAccount, RecurringTransaction, AnomalyNotification
)


class AnomalyDetectionService:
    """Service for detecting financial anomalies."""

    def __init__(self, user, account: Optional[BankAccount] = None):
        """Initialize the anomaly detection service."""
        self.user = user
        self.account = account
        self.preferences = self._get_or_create_preferences()
        self.lookback_days = 180  # 6 months for baseline

    def _get_or_create_preferences(self) -> UserAnomalyPreferences:
        """Get or create user anomaly preferences with defaults."""
        preferences, created = UserAnomalyPreferences.objects.get_or_create(user=self.user)

        # If newly created, set default enabled types (all types)
        if created and not preferences.enabled_types:
            preferences.enabled_types = [
                'unusual_amount',
                'unusual_timing',
                'duplicate_pattern',
                'missing_recurring',
                'changed_recurring',
                'spending_spike',
                'new_merchant',
                'account_inactive',
                'multiple_failures',
            ]
            preferences.save()

        return preferences

    def detect_all_anomalies_for_transaction(self, transaction: Transaction) -> List[Anomaly]:
        """Detect all anomalies for a new transaction."""
        if not self.preferences.anomaly_detection_enabled:
            return []

        self.account = transaction.account
        anomalies = []

        # Ensure enabled_types is a list
        enabled_types = self.preferences.enabled_types or []

        # Simple amount-based detection: flag large expenses
        if 'unusual_amount' in enabled_types or AnomalyType.UNUSUAL_AMOUNT in enabled_types:
            # Flag expenses over 500 or incomes over 1000 as potential anomalies
            amount = abs(float(transaction.amount))
            if (transaction.type == Transaction.EXPENSE and amount > 500) or \
               (transaction.type != Transaction.EXPENSE and amount > 1000):
                anomaly = Anomaly(
                    user=self.user,
                    account=self.account,
                    transaction=transaction,
                    anomaly_type=AnomalyType.UNUSUAL_AMOUNT,
                    severity=AnomalySeverity.INFO,
                    title=f"Large transaction detected",
                    description=f"Transaction of {transaction.amount} is notably large",
                    reason=f"Amount exceeds typical range for this type",
                    anomaly_score=Decimal('60'),
                    expected_value=Decimal('500'),
                    actual_value=transaction.amount,
                    context_data={
                        "amount": float(transaction.amount),
                        "type": transaction.type,
                    }
                )
                anomalies.append(anomaly)

        # Transaction-level detection - duplicate pattern
        if 'duplicate_pattern' in enabled_types or AnomalyType.DUPLICATE_PATTERN in enabled_types:
            anomaly = self._detect_duplicate_pattern(transaction)
            if anomaly:
                anomalies.append(anomaly)

        # Transaction-level detection - new merchant
        if 'new_merchant' in enabled_types or AnomalyType.NEW_MERCHANT in enabled_types:
            anomaly = self._detect_new_merchant(transaction)
            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    def _detect_unusual_amount(self, transaction: Transaction) -> Optional[Anomaly]:
        """
        Detect if transaction amount is unusual compared to historical data.

        Uses Z-score method: amount outside ±2.5 standard deviations is anomalous.
        Works with merchant_name, category, or description.
        """
        # Try to group by merchant, category, or description
        groupby_field = None
        groupby_value = None

        if transaction.merchant_name:
            groupby_field = 'merchant_name'
            groupby_value = transaction.merchant_name
        elif transaction.category:
            groupby_field = 'category'
            groupby_value = transaction.category
        elif transaction.description:
            groupby_field = 'description'
            groupby_value = transaction.description[:50]  # Use first 50 chars
        else:
            # No grouping data, skip
            return None

        # Get historical transactions for this group
        if groupby_field == 'merchant_name':
            historical = Transaction.objects.filter(
                account=self.account,
                merchant_name=groupby_value,
                type=transaction.type,
                date__gte=datetime.now().date() - timedelta(days=self.lookback_days)
            ).exclude(id=transaction.id)
        elif groupby_field == 'category':
            historical = Transaction.objects.filter(
                account=self.account,
                category=groupby_value,
                type=transaction.type,
                date__gte=datetime.now().date() - timedelta(days=self.lookback_days)
            ).exclude(id=transaction.id)
        else:  # description
            historical = Transaction.objects.filter(
                account=self.account,
                description__istartswith=groupby_value[:20],
                type=transaction.type,
                date__gte=datetime.now().date() - timedelta(days=self.lookback_days)
            ).exclude(id=transaction.id)

        if historical.count() < 2:
            # Need at least 2 data points (reduced from 3)
            return None

        amounts = [float(t.amount) for t in historical]
        current_amount = float(transaction.amount)

        try:
            mean = statistics.mean(amounts)

            # Only calculate stdev if we have more than 1 value
            if len(amounts) < 2:
                return None

            stdev = statistics.stdev(amounts)

            if stdev == 0:
                # All values are the same, check if current is significantly different
                if abs(current_amount - mean) > abs(mean) * 0.5:
                    confidence = 60.0
                    deviation_percent = ((current_amount - mean) / mean * 100) if mean != 0 else 0
                    return Anomaly(
                        user=self.user,
                        account=self.account,
                        transaction=transaction,
                        anomaly_type=AnomalyType.UNUSUAL_AMOUNT,
                        severity=AnomalySeverity.WARNING,
                        title=f"Unusual transaction amount",
                        description=f"Transaction amount of {transaction.amount} differs from typical amount of {mean:.2f}",
                        reason=f"All recent transactions are {mean:.2f}, but this is {current_amount:.2f}",
                        anomaly_score=Decimal(str(confidence)),
                        expected_value=Decimal(str(mean)),
                        actual_value=transaction.amount,
                        deviation_percent=Decimal(str(deviation_percent)),
                        context_data={
                            "historical_count": historical.count(),
                            "historical_amounts": [float(a) for a in amounts[:10]],
                        }
                    )
                return None

            # Calculate Z-score
            z_score = abs((current_amount - mean) / stdev)

            # Threshold: 2.0 standard deviations (lowered from 2.5 for sensitivity)
            if z_score > 2.0:
                min_score = self.preferences.get_minimum_score_for_severity()
                confidence = min(100, 50 + (z_score * 10))  # 0-100 score

                if confidence < min_score:
                    return None

                # Calculate deviation
                deviation_percent = ((current_amount - mean) / mean * 100) if mean != 0 else 0

                return Anomaly(
                    user=self.user,
                    account=self.account,
                    transaction=transaction,
                    anomaly_type=AnomalyType.UNUSUAL_AMOUNT,
                    severity=AnomalySeverity.WARNING if confidence < 90 else AnomalySeverity.CRITICAL,
                    title=f"Unusual transaction amount",
                    description=f"Transaction amount of {transaction.amount} is unusually {'high' if current_amount > mean else 'low'}",
                    reason=f"Amount is {z_score:.1f}σ away from average of {mean:.2f}",
                    anomaly_score=Decimal(str(confidence)),
                    expected_value=Decimal(str(mean)),
                    actual_value=transaction.amount,
                    deviation_percent=Decimal(str(deviation_percent)),
                    context_data={
                        "z_score": z_score,
                        "historical_count": historical.count(),
                        "historical_mean": mean,
                        "historical_stdev": stdev,
                        "historical_amounts": [float(a) for a in amounts[:10]],
                        "groupby_field": groupby_field,
                        "groupby_value": str(groupby_value),
                    }
                )
        except Exception as e:
            # Log but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error in unusual amount detection: {e}")
            return None

        return None

    def _detect_duplicate_pattern(self, transaction: Transaction) -> Optional[Anomaly]:
        """Detect if transaction is similar to a recent one (potential duplicate)."""
        # Look for transactions in the last 7 days with SAME amount
        recent = Transaction.objects.filter(
            account=self.account,
            date__gte=datetime.now().date() - timedelta(days=7),
            date__lt=transaction.date,
            amount=transaction.amount,
            type=transaction.type,
        ).exclude(id=transaction.id)

        if recent.exists():
            similar = recent.first()
            return Anomaly(
                user=self.user,
                account=self.account,
                transaction=transaction,
                anomaly_type=AnomalyType.DUPLICATE_PATTERN,
                severity=AnomalySeverity.WARNING,
                title="Potential duplicate transaction",
                description=f"Identical transaction found on {similar.date}: {similar.description}",
                reason=f"Same amount ({transaction.amount}) and type within 7 days",
                anomaly_score=Decimal('75'),
                expected_value=None,
                actual_value=transaction.amount,
                context_data={
                    'similar_transaction_id': similar.id,
                    'similar_date': similar.date.isoformat(),
                    'days_apart': (transaction.date - similar.date).days,
                }
            )

        return None

    def _detect_new_merchant(self, transaction: Transaction) -> Optional[Anomaly]:
        """Detect if transaction is from a new merchant (not seen before)."""
        if not transaction.merchant_name:
            return None

        # Check if this merchant exists in historical data
        previous = Transaction.objects.filter(
            account=self.account,
            merchant_name=transaction.merchant_name,
        ).exclude(id=transaction.id).exists()

        if not previous:
            return Anomaly(
                user=self.user,
                account=self.account,
                transaction=transaction,
                anomaly_type=AnomalyType.NEW_MERCHANT,
                severity=AnomalySeverity.INFO,
                title=f"New merchant: {transaction.merchant_name}",
                description=f"First transaction with {transaction.merchant_name}",
                reason="This merchant has not been seen before in your transaction history",
                anomaly_score=Decimal('50'),
                context_data={}
            )

        return None

    def detect_spending_spike(self, category: Optional[Category] = None) -> Optional[Anomaly]:
        """Detect spending spikes in a category for current month."""
        if not category:
            return None

        now = datetime.now().date()
        month_start = now.replace(day=1)

        # Current month spending
        current_spending = Transaction.objects.filter(
            account=self.account,
            category=category,
            date__gte=month_start,
            type=Transaction.EXPENSE,
        ).aggregate(total=Count('amount'))['total'] or 0

        # Historical monthly average (last 6 months, excluding current)
        six_months_ago = now - timedelta(days=180)
        historical = Transaction.objects.filter(
            account=self.account,
            category=category,
            type=Transaction.EXPENSE,
            date__gte=six_months_ago,
            date__lt=month_start,
        ).values('date__month').annotate(total=Count('amount'))

        if not historical:
            return None

        avg_monthly = sum(h['total'] for h in historical) / len(historical)

        if current_spending > avg_monthly * float(self.preferences.spending_spike_multiplier):
            multiplier = current_spending / avg_monthly if avg_monthly > 0 else 0
            return Anomaly(
                user=self.user,
                account=self.account,
                anomaly_type=AnomalyType.SPENDING_SPIKE,
                severity=AnomalySeverity.WARNING,
                title=f"Spending spike in {category.name}",
                description=f"You've spent {multiplier:.1f}x your average on {category.name} this month",
                reason=f"Current: {current_spending}, Average: {avg_monthly:.0f}",
                anomaly_score=Decimal(str(min(100, 50 + (multiplier * 20)))),
                expected_value=Decimal(str(avg_monthly)),
                actual_value=Decimal(str(current_spending)),
                context_data={
                    'category_id': category.id,
                    'multiplier': float(multiplier),
                }
            )

        return None

    def detect_missing_recurring(self, recurring: RecurringTransaction) -> Optional[Anomaly]:
        """Detect if a recurring transaction is overdue."""
        if recurring.is_ignored or not recurring.is_active:
            return None

        now = datetime.now().date()

        if now > recurring.next_expected_date:
            days_overdue = (now - recurring.next_expected_date).days

            return Anomaly(
                user=self.user,
                account=self.account,
                recurring=recurring,
                anomaly_type=AnomalyType.MISSING_RECURRING,
                severity=AnomalySeverity.CRITICAL if days_overdue > 7 else AnomalySeverity.WARNING,
                title=f"Missing recurring payment: {recurring.get_display_name()}",
                description=f"{recurring.get_display_name()} was expected {days_overdue} days ago",
                reason=f"Expected on {recurring.next_expected_date}, but not found",
                anomaly_score=Decimal(str(min(100, 60 + (days_overdue * 2)))),
                expected_value=recurring.amount,
                context_data={
                    'expected_date': recurring.next_expected_date.isoformat(),
                    'days_overdue': days_overdue,
                    'frequency': recurring.frequency,
                }
            )

        return None

    def detect_changed_recurring(self, recurring: RecurringTransaction) -> Optional[Anomaly]:
        """Detect if a recurring transaction amount or frequency has changed."""
        # Get last few occurrences
        recent_transactions = Transaction.objects.filter(
            account=self.account,
            merchant_name=recurring.merchant_name,
            type=Transaction.EXPENSE,
            date__gte=datetime.now().date() - timedelta(days=90),
        ).order_by('-date')[:5]

        if len(recent_transactions) < 2:
            return None

        amounts = [float(t.amount) for t in recent_transactions]
        expected_amount = float(recurring.amount)

        # Check if amounts vary significantly
        if max(amounts) != min(amounts):
            return Anomaly(
                user=self.user,
                account=self.account,
                recurring=recurring,
                anomaly_type=AnomalyType.CHANGED_RECURRING,
                severity=AnomalySeverity.WARNING,
                title=f"Changed amount: {recurring.get_display_name()}",
                description=f"Amount varies: {min(amounts)} - {max(amounts)}",
                reason=f"Recent amounts differ from recorded {expected_amount}",
                anomaly_score=Decimal('75'),
                expected_value=recurring.amount,
                actual_value=Decimal(str(max(amounts))),
                context_data={
                    'recent_amounts': amounts,
                    'min_amount': min(amounts),
                    'max_amount': max(amounts),
                }
            )

        return None

    def detect_account_inactive(self) -> Optional[Anomaly]:
        """Detect if account has no recent transactions."""
        now = datetime.now().date()
        threshold = now - timedelta(days=self.preferences.days_before_inactive)

        last_transaction = Transaction.objects.filter(
            account=self.account,
        ).order_by('-date').first()

        if not last_transaction:
            return None

        if last_transaction.date < threshold:
            days_inactive = (now - last_transaction.date).days

            return Anomaly(
                user=self.user,
                account=self.account,
                anomaly_type=AnomalyType.ACCOUNT_INACTIVE,
                severity=AnomalySeverity.INFO,
                title=f"{self.account.name} is inactive",
                description=f"No transactions in {days_inactive} days",
                reason=f"Last transaction: {last_transaction.date}",
                anomaly_score=Decimal('50'),
                context_data={
                    'last_transaction_date': last_transaction.date.isoformat(),
                    'days_inactive': days_inactive,
                }
            )

        return None


def create_anomaly_if_new(anomaly: Anomaly) -> Optional[Anomaly]:
    """
    Create an anomaly if it doesn't already exist.

    Checks for recent similar anomalies to avoid duplicates.
    Also creates AnomalyNotification record if anomaly is created.
    """
    # Check for duplicate anomalies within last 24 hours
    existing = Anomaly.objects.filter(
        user=anomaly.user,
        account=anomaly.account,
        anomaly_type=anomaly.anomaly_type,
        created_at__gte=datetime.now() - timedelta(hours=24),
    ).first()

    if existing:
        # Don't create duplicate
        return None

    anomaly.save()

    # Create notification for the anomaly
    notification, _ = AnomalyNotification.objects.get_or_create(
        user=anomaly.user,
        anomaly=anomaly,
        defaults={
            'is_read': False,
            'is_notified_via_email': anomaly.user.anomaly_preferences.email_notifications,
            'is_notified_via_push': anomaly.user.anomaly_preferences.push_notifications,
        }
    )

    return anomaly

