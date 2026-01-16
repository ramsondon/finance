from __future__ import annotations
from typing import Dict, Any
from django.db.models import Sum
from ...banking.models import BankAccount, Transaction


class StatsService:
    def overview(self, user_id: int) -> Dict[str, Any]:
        """Calculate account overview with proper balance calculation respecting opening_balance_date."""
        accounts = BankAccount.objects.filter(user_id=user_id)
        balance = 0

        for acc in accounts:
            # Build query for transactions
            tx_query = Transaction.objects.filter(account=acc)

            # If opening_balance_date is set, only include transactions from that date onward
            if acc.opening_balance_date:
                tx_query = tx_query.filter(date__gte=acc.opening_balance_date)

            # Sum transactions for this account
            tx_sum = tx_query.aggregate(total=Sum("amount"))["total"] or 0

            # Calculate current balance: opening_balance + sum of transactions
            current_balance = acc.opening_balance + tx_sum
            balance += current_balance

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
