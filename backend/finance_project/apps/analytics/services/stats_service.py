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

        # Income and expense totals, converted to user's preferred currency
        income_total = Decimal("0")
        expense_total = Decimal("0")

        # Calculate income and expense by account, then convert to user's currency
        for acc in accounts:
            # Get income for this account
            acc_income = (
                Transaction.objects.filter(account=acc, type="income").aggregate(total=Sum("amount"))["total"]
                or 0
            )
            # Get expense for this account
            acc_expense = (
                Transaction.objects.filter(account=acc, type="expense").aggregate(total=Sum("amount"))["total"]
                or 0
            )

            # Convert to user's preferred currency
            if acc.currency != user_currency:
                income_converted = ExchangeService.convert(acc_income, acc.currency, user_currency)
                expense_converted = ExchangeService.convert(acc_expense, acc.currency, user_currency)
                income_total += income_converted
                expense_total += expense_converted
            else:
                income_total += Decimal(str(acc_income))
                expense_total += Decimal(str(acc_expense))

        # monthly trends minimal stub
        monthly = []
        return {
            "total_balance": float(balance),
            "total_balance_currency": user_currency,
            "income_expense_breakdown": {"income": float(income_total), "expense": float(expense_total)},
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
        from ...banking.models import Transaction, Category
        from .date_utils import get_date_range
        from decimal import Decimal

        # Get date range for the period
        start_date, end_date = get_date_range(period)

        # Load all categories for this user upfront (avoid N+1 queries)
        # Include ALL categories, not just those with expenses
        categories_by_id = {}
        all_user_categories = Category.objects.filter(user_id=user_id).order_by('name')
        for cat in all_user_categories:
            categories_by_id[cat.id] = {"name": cat.name, "color": cat.color}

        # Get all expense transactions for the user in the date range
        # Use select_related to load category in one query
        qs = Transaction.objects.filter(
            account__user_id=user_id,
            type="expense",
            date__gte=start_date,
            date__lte=end_date
        ).select_related('category')

        # Build a dictionary to aggregate by category
        # Initialize with ALL categories so they all appear in results (with 0 if no expenses)
        category_totals = {}
        for cat_id, cat_info in categories_by_id.items():
            key = (cat_id, cat_info["name"], cat_info["color"])
            category_totals[key] = Decimal('0')

        # Add uncategorized category if there are any uncategorized transactions
        uncategorized_key = (None, "Unknown", "#9ca3af")
        category_totals[uncategorized_key] = Decimal('0')

        # Now process transactions and update totals
        for tx in qs:
            cat_id = tx.category_id

            # Get category info from cache, or use defaults for uncategorized
            if cat_id and cat_id in categories_by_id:
                cat_info = categories_by_id[cat_id]
                cat_name = cat_info["name"]
                cat_color = cat_info["color"]
            else:
                cat_name = "Unknown"
                cat_color = "#9ca3af"

            key = (cat_id, cat_name, cat_color)
            category_totals[key] += Decimal(str(abs(tx.amount)))

        # Convert to lists and sort by amount descending
        labels, values, colors, items = [], [], [], []

        # Sort by amount descending, but only include categories with expenses > 0
        sorted_categories = sorted(
            [(k, v) for k, v in category_totals.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )

        for (cat_id, cat_name, cat_color), total in sorted_categories:
            labels.append(cat_name)
            values.append(float(total))
            colors.append(cat_color)
            items.append({"id": cat_id, "name": cat_name, "value": float(total), "color": cat_color})

        return {"labels": labels, "values": values, "colors": colors, "items": items}
