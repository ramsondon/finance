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

    def overview(self, user_id: int, period: str = "current_month", account_id: int = None) -> Dict[str, Any]:
        """Calculate account overview with proper balance calculation respecting opening_balance_date.

        Converts all account balances to the user's preferred currency.
        Income and expense are filtered by the selected period with comparison to previous period.

        Args:
            user_id: User ID
            period: Time period for income/expense calculation. One of 'current_month',
                    'last_month', 'current_week', 'last_week', 'current_year',
                    'last_year', 'all_time'. Defaults to 'current_month'.
            account_id: Optional account ID to filter by. If None, includes all accounts.
        """
        from ...accounts.models import UserProfile
        from ...banking.services.exchange_service import ExchangeService
        from .date_utils import get_date_range, get_previous_period
        from decimal import Decimal

        accounts = BankAccount.objects.filter(user_id=user_id)
        if account_id:
            accounts = accounts.filter(id=account_id)
        balance = Decimal("0")

        # Get user's preferred currency
        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
            user_currency = user_profile.get_currency()
        except UserProfile.DoesNotExist:
            user_currency = "USD"  # Fallback default

        # Sum all account balances converted to user's preferred currency
        # (Total balance is always all-time, not filtered by period)
        for acc in accounts:
            account_balance = self.get_account_balance(acc)
            # Convert to user's preferred currency
            if acc.currency != user_currency:
                converted = ExchangeService.convert(account_balance, acc.currency, user_currency)
                balance += converted
            else:
                balance += Decimal(str(account_balance))

        # Get date range for current period
        start_date, end_date = get_date_range(period)

        # Calculate income and expense for the selected period
        income_total, expense_total = self._calculate_income_expense(
            accounts, start_date, end_date, user_currency
        )

        # Calculate comparison percentages
        previous_period = get_previous_period(period)
        income_change_percent = None
        expense_change_percent = None

        if previous_period:
            prev_start, prev_end = get_date_range(previous_period)
            prev_income, prev_expense = self._calculate_income_expense(
                accounts, prev_start, prev_end, user_currency
            )

            # Calculate income change percentage
            if prev_income == 0:
                income_change_percent = 100.0 if income_total > 0 else 0.0
            else:
                income_change_percent = float(((income_total - prev_income) / prev_income) * 100)

            # Calculate expense change percentage
            if prev_expense == 0:
                expense_change_percent = 100.0 if expense_total > 0 else 0.0
            else:
                expense_change_percent = float(((expense_total - prev_expense) / prev_expense) * 100)

        # monthly trends minimal stub
        monthly = []
        return {
            "total_balance": float(balance),
            "total_balance_currency": user_currency,
            "income_expense_breakdown": {
                "income": float(income_total),
                "expense": float(expense_total)
            },
            "income_change_percent": income_change_percent,
            "expense_change_percent": expense_change_percent,
            "monthly_trends": monthly,
        }

    def _calculate_income_expense(self, accounts, start_date, end_date, user_currency):
        """Helper to calculate income and expense totals for a date range.

        Args:
            accounts: QuerySet of BankAccount objects
            start_date: Start date for filtering
            end_date: End date for filtering
            user_currency: Currency to convert to

        Returns:
            Tuple of (income_total, expense_total) as Decimals
        """
        from ...banking.services.exchange_service import ExchangeService
        from decimal import Decimal

        income_total = Decimal("0")
        expense_total = Decimal("0")

        for acc in accounts:
            # Get income for this account in the date range
            acc_income = (
                Transaction.objects.filter(
                    account=acc,
                    type="income",
                    date__gte=start_date,
                    date__lte=end_date
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )
            # Get expense for this account in the date range
            acc_expense = (
                Transaction.objects.filter(
                    account=acc,
                    type="expense",
                    date__gte=start_date,
                    date__lte=end_date
                ).aggregate(total=Sum("amount"))["total"]
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

        return income_total, expense_total

    def category_expense_breakdown(self, user_id: int, period: str = "current_month", account_id: int = None) -> Dict[str, Any]:
        """Return expense totals grouped by category for the user. Uncategorized -> 'Unknown'.

        Args:
            user_id: User ID to get expenses for
            period: One of 'current_month', 'last_month', 'current_year', 'last_year',
                    'current_week', 'last_week', 'all_time'. Defaults to 'current_month'.
            account_id: Optional account ID to filter expenses by. If None, includes all accounts.

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

        # Filter by account if specified
        if account_id:
            qs = qs.filter(account_id=account_id)

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
