from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from datetime import datetime
from .services.stats_service import StatsService
from ..banking.models import Transaction, BankAccount


class OverviewStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = StatsService().overview(request.user.id)
        return Response(data)


class AccountBalanceTimeseriesView(APIView):
    """
    Get balance timeseries for a bank account.
    Endpoint: GET /api/analytics/accounts/{account_id}/balance-timeseries/

    Query params:
    - date_from: YYYY-MM-DD (optional)
    - date_to: YYYY-MM-DD (optional)

    Returns:
    {
        "dates": ["2026-01-01", "2026-01-02", ...],
        "balances": [5000.00, 5050.00, ...],
        "opening_balance": 5000.00,
        "opening_balance_date": "2026-01-01"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id):
        try:
            # Verify user owns this account
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get optional date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Build queryset
        qs = Transaction.objects.filter(account=account).order_by('date')

        if date_from:
            try:
                qs = qs.filter(date__gte=datetime.fromisoformat(date_from).date())
            except (ValueError, TypeError):
                pass

        if date_to:
            try:
                qs = qs.filter(date__lte=datetime.fromisoformat(date_to).date())
            except (ValueError, TypeError):
                pass

        # Aggregate by date
        daily_totals = (
            qs.values('date')
            .annotate(daily_amount=Sum('amount'))
            .order_by('date')
        )

        # Build timeseries
        dates = []
        balances = []
        running_balance = float(account.opening_balance or 0)

        for entry in daily_totals:
            dates.append(str(entry['date']))
            running_balance += float(entry['daily_amount'] or 0)
            balances.append(round(running_balance, 2))

        return Response({
            'dates': dates,
            'balances': balances,
            'opening_balance': float(account.opening_balance or 0),
            'opening_balance_date': str(account.opening_balance_date) if account.opening_balance_date else None,
            'count': len(dates)
        })
