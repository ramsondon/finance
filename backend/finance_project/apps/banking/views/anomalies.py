"""
ViewSets for anomaly management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Count
from datetime import datetime, timedelta

from ..models import Anomaly, UserAnomalyPreferences
from ..serializers.anomalies import (
    AnomalySerializer,
    AnomalyDetailSerializer,
    UserAnomalyPreferencesSerializer,
    AnomalyStatsSerializer,
)


class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for anomalies.

    Allows users to:
    - List and view anomalies
    - Filter by severity, type, date range
    - Dismiss anomalies
    - Provide feedback (false positive, confirmed)
    - View anomaly statistics
    """

    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['account_id', 'severity', 'anomaly_type', 'is_dismissed']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'anomaly_score', 'severity']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return anomalies for the current user."""
        return Anomaly.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions."""
        if self.action == 'retrieve':
            return AnomalyDetailSerializer
        return AnomalySerializer

    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss an anomaly."""
        anomaly = self.get_object()
        anomaly.is_dismissed = True
        anomaly.dismissed_by_user = True
        anomaly.dismissed_at = datetime.now()
        anomaly.save(update_fields=['is_dismissed', 'dismissed_by_user', 'dismissed_at'])

        return Response(
            AnomalySerializer(anomaly).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """
        Provide feedback on an anomaly.

        Body:
        {
            "feedback_type": "false_positive" | "confirmed" | "ignore_type",
            "reason": "explanation"
        }
        """
        anomaly = self.get_object()
        feedback_type = request.data.get('feedback_type')
        reason = request.data.get('reason', '')

        if feedback_type == 'false_positive':
            anomaly.is_false_positive = True
            anomaly.is_dismissed = True
        elif feedback_type == 'confirmed':
            anomaly.is_confirmed = True
        elif feedback_type == 'ignore_type':
            # Add to ignored types in preferences
            prefs = request.user.anomaly_preferences
            if anomaly.anomaly_type in prefs.enabled_types:
                prefs.enabled_types.remove(anomaly.anomaly_type)
                prefs.save(update_fields=['enabled_types'])

        anomaly.save()

        return Response(
            AnomalySerializer(anomaly).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get anomaly statistics for the user.

        Returns count by severity, type, and trend over time.
        """
        queryset = self.get_queryset()

        # Counts by severity
        critical_count = queryset.filter(severity='critical').count()
        warning_count = queryset.filter(severity='warning').count()
        info_count = queryset.filter(severity='info').count()
        dismissed_count = queryset.filter(is_dismissed=True).count()
        confirmed_count = queryset.filter(is_confirmed=True).count()
        false_positive_count = queryset.filter(is_false_positive=True).count()

        # Top types
        top_types = {}
        for type_choice in queryset.values('anomaly_type').annotate(count=Count('id')):
            top_types[type_choice['anomaly_type']] = type_choice['count']

        # Trend over last 7 days
        severity_trend = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            day_anomalies = queryset.filter(
                created_at__date=date
            ).values('severity').annotate(count=Count('id'))

            day_data = {
                'date': date.isoformat(),
                'critical': 0,
                'warning': 0,
                'info': 0,
            }

            for item in day_anomalies:
                day_data[item['severity']] = item['count']

            severity_trend.append(day_data)

        severity_trend.reverse()  # Oldest first

        stats_data = {
            'total_anomalies': queryset.count(),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'dismissed_count': dismissed_count,
            'confirmed_count': confirmed_count,
            'false_positive_count': false_positive_count,
            'top_types': top_types,
            'severity_trend': severity_trend,
        }

        serializer = AnomalyStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAnomalyPreferencesViewSet(viewsets.ViewSet):
    """
    ViewSet for user anomaly preferences.

    Allows users to configure anomaly detection settings.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's anomaly preferences."""
        preferences, _ = UserAnomalyPreferences.objects.get_or_create(user=request.user)
        serializer = UserAnomalyPreferencesSerializer(preferences)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def me(self, request):
        """Update current user's anomaly preferences."""
        preferences, _ = UserAnomalyPreferences.objects.get_or_create(user=request.user)

        # Update fields from request
        for field in ['anomaly_detection_enabled', 'notify_on_critical', 'notify_on_warning',
                      'notify_on_info', 'email_notifications', 'push_notifications',
                      'sensitivity', 'enabled_types', 'amount_deviation_percent',
                      'spending_spike_multiplier', 'days_before_inactive']:
            if field in request.data:
                setattr(preferences, field, request.data[field])

        preferences.save()
        serializer = UserAnomalyPreferencesSerializer(preferences)
        return Response(serializer.data)

    def get(self, request):
        """Get anomaly preferences."""
        preferences, _ = UserAnomalyPreferences.objects.get_or_create(user=request.user)
        serializer = UserAnomalyPreferencesSerializer(preferences)
        return Response(serializer.data)

    def put(self, request):
        """Update anomaly preferences."""
        preferences, _ = UserAnomalyPreferences.objects.get_or_create(user=request.user)

        for field in ['anomaly_detection_enabled', 'notify_on_critical', 'notify_on_warning',
                      'notify_on_info', 'email_notifications', 'push_notifications',
                      'sensitivity', 'enabled_types', 'amount_deviation_percent',
                      'spending_spike_multiplier', 'days_before_inactive']:
            if field in request.data:
                setattr(preferences, field, request.data[field])

        preferences.save()
        serializer = UserAnomalyPreferencesSerializer(preferences)
        return Response(serializer.data)

