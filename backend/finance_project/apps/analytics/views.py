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
        period = request.query_params.get('period', 'current_month')
        account_id = request.query_params.get('account_id')

        # Validate account_id if provided
        if account_id:
            try:
                account_id = int(account_id)
                # Verify user owns this account
                if not BankAccount.objects.filter(id=account_id, user=request.user).exists():
                    account_id = None
            except (ValueError, TypeError):
                account_id = None

        data = StatsService().overview(request.user.id, period=period, account_id=account_id)
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

        # Get optional date filters (support both parameter naming conventions)
        date_from = request.query_params.get('date__gte') or request.query_params.get('date_from')
        date_to = request.query_params.get('date__lte') or request.query_params.get('date_to')

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


class CategoryExpenseBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get period from query params, default to 'current_month'
        period = request.query_params.get('period', 'current_month')
        account_id = request.query_params.get('account_id')

        # Validate period is one of the allowed values
        allowed_periods = ['current_month', 'last_month', 'current_year', 'last_year', 'current_week', 'last_week', 'all_time']
        if period not in allowed_periods:
            period = 'current_month'

        # Validate account_id if provided
        if account_id:
            try:
                account_id = int(account_id)
                # Verify user owns this account
                if not BankAccount.objects.filter(id=account_id, user=request.user).exists():
                    account_id = None
            except (ValueError, TypeError):
                account_id = None

        data = StatsService().category_expense_breakdown(request.user.id, period=period, account_id=account_id)
        return Response(data)


class SpendingTrendView(APIView):
    """
    Get spending trend and forecast data.
    Endpoint: GET /api/analytics/spending-trend/

    Query params:
    - period: current_month, last_month, current_year, last_year, current_week, last_week, all_time
    - account_id: Optional account ID to filter by

    Returns:
    {
        "current_period_expense": 1500.00,
        "previous_period_expense": 1200.00,
        "trend_percent": 25.0,
        "daily_average": 50.00,
        "forecast_month_end": 1500.00,
        "days_in_period": 30,
        "days_elapsed": 15,
        "is_trending_up": true
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'current_month')
        account_id = request.query_params.get('account_id')

        # Validate period
        allowed_periods = ['current_month', 'last_month', 'current_year', 'last_year', 'current_week', 'last_week', 'all_time']
        if period not in allowed_periods:
            period = 'current_month'

        # Validate account_id if provided
        if account_id:
            try:
                account_id = int(account_id)
                if not BankAccount.objects.filter(id=account_id, user=request.user).exists():
                    account_id = None
            except (ValueError, TypeError):
                account_id = None

        data = StatsService().spending_trend(request.user.id, period=period, account_id=account_id)
        return Response(data)


class CashFlowView(APIView):
    """
    Get cash flow metrics for the period.
    Endpoint: GET /api/analytics/cash-flow/

    Query params:
    - period: current_month, last_month, current_year, last_year, current_week, last_week, all_time
    - account_id: Optional account ID to filter by

    Returns:
    {
        "income": 5000.00,
        "expense": 1500.00,
        "net_flow": 3500.00,
        "savings_rate": 70.0,
        "burn_rate": 1500.00,
        "balance_change": 3500.00
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'current_month')
        account_id = request.query_params.get('account_id')

        # Validate period
        allowed_periods = ['current_month', 'last_month', 'current_year', 'last_year', 'current_week', 'last_week', 'all_time']
        if period not in allowed_periods:
            period = 'current_month'

        # Validate account_id if provided
        if account_id:
            try:
                account_id = int(account_id)
                if not BankAccount.objects.filter(id=account_id, user=request.user).exists():
                    account_id = None
            except (ValueError, TypeError):
                account_id = None

        data = StatsService().cash_flow(request.user.id, period=period, account_id=account_id)
        return Response(data)

