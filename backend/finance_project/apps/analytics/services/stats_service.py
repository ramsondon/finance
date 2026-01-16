from __future__ import annotations
from typing import Dict, Any
from django.db.models import Sum
from ...banking.models import BankAccount, Transaction


class StatsService:
    def get_account_balance(self, account: BankAccount) -> float:
        """
        Get current balance for a single account respecting opening_balance_date.

        Args:
            account: BankAccount instance

        Returns:
            Current balance as float
        """
        # Build query for transactions
        tx_query = Transaction.objects.filter(account=account)

        # If opening_balance_date is set, only include transactions from that date onward
        if account.opening_balance_date:
            tx_query = tx_query.filter(date__gte=account.opening_balance_date)

        # Sum transactions for this account
        tx_sum = tx_query.aggregate(total=Sum("amount"))["total"] or 0

        # Calculate current balance: opening_balance + sum of transactions
        current_balance = account.opening_balance + tx_sum
        return float(current_balance)

    def overview(self, user_id: int) -> Dict[str, Any]:
        """Calculate account overview with proper balance calculation respecting opening_balance_date.

        Converts all account balances to the user's preferred currency.
        """
        from ...accounts.models import UserProfile
        from ...banking.services.exchange_service import ExchangeService
        from decimal import Decimal

        accounts = BankAccount.objects.filter(user_id=user_id)
        balance = Decimal("0")

        # Get user's preferred currency
        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
            user_currency = user_profile.get_currency()
        except UserProfile.DoesNotExist:
            user_currency = "USD"  # Fallback default

        # Sum all account balances converted to user's preferred currency
        for acc in accounts:
            account_balance = self.get_account_balance(acc)
            # Convert to user's preferred currency
            if acc.currency != user_currency:
                converted = ExchangeService.convert(account_balance, acc.currency, user_currency)
                balance += converted
            else:
                balance += Decimal(str(account_balance))

        # Income and expense are totals across all transactions (not affected by opening_balance_date)
        income = (
            Transaction.objects.filter(account__user_id=user_id, type="income").aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expense = (
            Transaction.objects.filter(account__user_id=user_id, type="expense").aggregate(total=Sum("amount"))["total"]
            or 0
        )
        # monthly trends minimal stub
        monthly = []
        return {
            "total_balance": float(balance),
            "total_balance_currency": user_currency,
            "income_expense_breakdown": {"income": float(income), "expense": float(expense)},
            "monthly_trends": monthly,
        }

    def category_expense_breakdown(self, user_id: int, period: str = "current_month") -> Dict[str, Any]:
        """Return expense totals grouped by category for the user. Uncategorized -> 'Unknown'.

        Args:
            user_id: User ID to get expenses for
            period: One of 'current_month', 'last_month', 'current_year', 'last_year',
                    'current_week', 'last_week', 'all_time'. Defaults to 'current_month'.

        Returns:
            Dict with labels, values, colors, and items lists for pie chart
        """
        from ...banking.models import Transaction
        from .date_utils import get_date_range

        # Get date range for the period
        start_date, end_date = get_date_range(period)

        qs = Transaction.objects.filter(
            account__user_id=user_id,
            type="expense",
            date__gte=start_date,
            date__lte=end_date
        )
        data = (
            qs.values("category_id", "category__name", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        labels, values, colors, items = [], [], [], []
        for row in data:
            cat_id = row["category_id"]
            name = row["category__name"] or "Unknown"
            color = row["category__color"] or "#9ca3af"  # gray-400 as default for Unknown
            value = float(abs(row["total"] or 0))
            labels.append(name)
            values.append(value)
            colors.append(color)
            items.append({"id": cat_id, "name": name, "value": value, "color": color})
        return {"labels": labels, "values": values, "colors": colors, "items": items}
