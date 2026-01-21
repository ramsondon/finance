"""
ViewSets for recurring transaction management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Sum, Q
from decimal import Decimal

from ..models import RecurringTransaction, BankAccount, Transaction
from ..serializers.recurring import RecurringTransactionSerializer
from ..serializers import TransactionSerializer
from ..tasks import detect_recurring_transactions_task


class RecurringTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing recurring transaction patterns.

    Allows users to:
    - View detected recurring transactions
    - Mark transactions as ignored
    - Add notes to transactions
    - View summary statistics
    - Manually trigger recurring detection
    """

    serializer_class = RecurringTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['account_id', 'frequency', 'is_active', 'is_ignored']
    search_fields = ['description', 'display_name', 'merchant_name']
    ordering_fields = ['confidence_score', 'amount', 'next_expected_date', 'occurrence_count']
    ordering = ['-confidence_score', '-occurrence_count']

    def get_queryset(self):
        """Return recurring transactions for the current user with custom filtering."""
        queryset = RecurringTransaction.objects.filter(user=self.request.user)

        # Custom status filter: 'active' means is_active=True AND is_ignored=False
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True, is_ignored=False)
        elif status_filter == 'ignored':
            queryset = queryset.filter(is_ignored=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary statistics for recurring transactions.

        Returns:
        - Total count of recurring patterns
        - Active count
        - Monthly/yearly recurring costs
        - Breakdown by frequency
        - Top recurring transactions
        - Overdue transactions count
        """
        user = request.user
        queryset = self.get_queryset()

        # Filter by account if specified
        account_id = request.query_params.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)

        # Calculate totals
        total_count = queryset.count()
        active_count = queryset.filter(is_active=True).count()

        # Calculate costs
        monthly_recurring = Decimal('0')
        yearly_recurring = Decimal('0')

        for recurring in queryset.filter(is_active=True):
            if recurring.frequency == 'weekly':
                monthly_recurring += recurring.amount * Decimal('4.33')
                yearly_recurring += recurring.amount * Decimal('52')
            elif recurring.frequency == 'bi-weekly':
                monthly_recurring += recurring.amount * Decimal('2.17')
                yearly_recurring += recurring.amount * Decimal('26')
            elif recurring.frequency == 'monthly':
                monthly_recurring += recurring.amount
                yearly_recurring += recurring.amount * Decimal('12')
            elif recurring.frequency == 'quarterly':
                monthly_recurring += recurring.amount / Decimal('3')
                yearly_recurring += recurring.amount * Decimal('4')
            elif recurring.frequency == 'yearly':
                monthly_recurring += recurring.amount / Decimal('12')
                yearly_recurring += recurring.amount

        # Breakdown by frequency
        by_frequency = {}
        for freq, _ in RecurringTransaction.FREQUENCY_CHOICES:
            freq_qs = queryset.filter(frequency=freq, is_active=True)
            count = freq_qs.count()
            total_amount = freq_qs.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            by_frequency[freq] = {
                'count': count,
                'total_amount': str(total_amount),
            }

        # Top recurring - serialize properly
        top_recurring_qs = queryset.filter(is_active=True).order_by(
            '-confidence_score', '-occurrence_count'
        )[:5]
        top_recurring_data = RecurringTransactionSerializer(top_recurring_qs, many=True).data

        # Overdue count
        from datetime import datetime
        now = datetime.now().date()
        overdue_count = queryset.filter(
            is_active=True,
            is_ignored=False,
            next_expected_date__lt=now
        ).count()

        # Get account currency if filtering by account
        account_currency = None
        if account_id:
            try:
                account = BankAccount.objects.get(id=account_id, user=request.user)
                account_currency = account.currency
            except BankAccount.DoesNotExist:
                pass

        # Return plain dict response (don't use the summary serializer)
        return Response({
            'total_count': total_count,
            'active_count': active_count,
            'monthly_recurring_cost': str(monthly_recurring.quantize(Decimal('0.01'))),
            'yearly_recurring_cost': str(yearly_recurring.quantize(Decimal('0.01'))),
            'by_frequency': by_frequency,
            'top_recurring': top_recurring_data,
            'overdue_count': overdue_count,
            'account_currency': account_currency,
        })

    @action(detail=False, methods=['post'])
    def detect(self, request):
        """
        Manually trigger recurring transaction detection.

        Query Parameters:
        - account_id (required): Bank account to analyze
        - days_back (optional, default=365): How far back to look

        Returns:
        - Success message with number of patterns detected
        """
        account_id = request.query_params.get('account_id')
        days_back = int(request.query_params.get('days_back', 365))

        if not account_id:
            return Response(
                {'error': 'account_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify account belongs to user
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Trigger detection task
        detect_recurring_transactions_task.delay(
            account_id=account_id,
            days_back=days_back
        )

        return Response({
            'message': 'Recurring transaction detection started',
            'account_id': account_id,
            'days_back': days_back,
            'status': 'processing'
        })

    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        """Mark a recurring transaction as ignored."""
        recurring = self.get_object()
        recurring.is_ignored = True
        recurring.save(update_fields=['is_ignored'])

        return Response(RecurringTransactionSerializer(recurring).data)

    @action(detail=True, methods=['post'])
    def unignore(self, request, pk=None):
        """Unignore a recurring transaction."""
        recurring = self.get_object()
        recurring.is_ignored = False
        recurring.save(update_fields=['is_ignored'])

        return Response(RecurringTransactionSerializer(recurring).data)

    @action(detail=True, methods=['patch'])
    def add_note(self, request, pk=None):
        """Add or update a note for a recurring transaction."""
        recurring = self.get_object()
        note = request.data.get('note', '')
        recurring.user_notes = note
        recurring.save(update_fields=['user_notes'])

        return Response(RecurringTransactionSerializer(recurring).data)

    @action(detail=True, methods=['patch'])
    def update_details(self, request, pk=None):
        """
        Update user-editable details (display_name and user_notes).

        Request body:
        - display_name (optional): Custom display name for the recurring transaction
        - user_notes (optional): User's notes about this transaction
        """
        recurring = self.get_object()
        update_fields = []

        if 'display_name' in request.data:
            recurring.display_name = request.data['display_name']
            update_fields.append('display_name')

        if 'user_notes' in request.data:
            recurring.user_notes = request.data['user_notes']
            update_fields.append('user_notes')

        if update_fields:
            update_fields.append('updated_at')
            recurring.save(update_fields=update_fields)

        return Response(RecurringTransactionSerializer(recurring).data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue recurring transactions."""
        from datetime import datetime
        now = datetime.now().date()

        overdue_qs = self.get_queryset().filter(
            is_active=True,
            is_ignored=False,
            next_expected_date__lt=now
        ).order_by('next_expected_date')

        serializer = self.get_serializer(overdue_qs, many=True)
        return Response({
            'count': overdue_qs.count(),
            'recurring_transactions': serializer.data
        })

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming recurring transactions."""
        from datetime import datetime, timedelta

        now = datetime.now().date()
        days_ahead = int(request.query_params.get('days', 30))
        future_date = now + timedelta(days=days_ahead)

        upcoming_qs = self.get_queryset().filter(
            is_active=True,
            next_expected_date__range=[now, future_date]
        ).order_by('next_expected_date')

        serializer = self.get_serializer(upcoming_qs, many=True)
        return Response({
            'count': upcoming_qs.count(),
            'days_ahead': days_ahead,
            'recurring_transactions': serializer.data
        })

    @action(detail=True, methods=['get'])
    def linked_transactions(self, request, pk=None):
        """
        Get all actual transactions linked to this recurring transaction pattern.

        Returns the list of Transaction objects that match this recurring pattern.
        """
        recurring = self.get_object()

        # Get the transaction IDs stored in the recurring transaction
        transaction_ids = recurring.transaction_ids or []

        if not transaction_ids:
            return Response({
                'count': 0,
                'recurring_id': recurring.id,
                'recurring_description': recurring.description,
                'transactions': []
            })

        # Fetch the actual transactions
        transactions = Transaction.objects.filter(
            id__in=transaction_ids,
            account__user=request.user  # Security: only user's transactions
        ).order_by('-date')

        serializer = TransactionSerializer(transactions, many=True)

        return Response({
            'count': transactions.count(),
            'recurring_id': recurring.id,
            'recurring_description': recurring.description,
            'recurring_frequency': recurring.frequency,
            'recurring_amount': float(recurring.amount),
            'transactions': serializer.data
        })

