"""Date range calculation utilities for analytics."""
from datetime import date, timedelta
from typing import Tuple


def get_date_range(period: str) -> Tuple[date, date]:
    """
    Calculate start and end dates for a given period.

    Args:
        period: One of 'current_month', 'last_month', 'current_year', 'last_year',
                'current_week', 'last_week', 'all_time'

    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()

    if period == "current_month":
        # Current month: 1st of this month to today
        start = date(today.year, today.month, 1)
        end = today

    elif period == "last_month":
        # Last month: 1st to last day of previous month
        first_of_this_month = date(today.year, today.month, 1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        start = date(last_of_last_month.year, last_of_last_month.month, 1)
        end = last_of_last_month

    elif period == "current_year":
        # Current year: 1st Jan to today
        start = date(today.year, 1, 1)
        end = today

    elif period == "last_year":
        # Last year: 1st Jan to 31st Dec of previous year
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)

    elif period == "current_week":
        # Current week: Monday to today
        # Monday is 0, Sunday is 6
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        end = today

    elif period == "last_week":
        # Last week: Monday to Sunday of the week before current
        days_since_monday = today.weekday()
        end_of_last_week = today - timedelta(days=days_since_monday + 1)
        start_of_last_week = end_of_last_week - timedelta(days=6)
        start = start_of_last_week
        end = end_of_last_week

    elif period == "all_time":
        # All time: earliest possible date to today
        # Using a very old date as practical "all time" start
        start = date(1900, 1, 1)
        end = today

    else:
        # Default to current month if unknown period
        start = date(today.year, today.month, 1)
        end = today

    return start, end

