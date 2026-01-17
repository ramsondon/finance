"""Date range calculation utilities for analytics."""
from datetime import date, timedelta
from typing import Tuple, Optional


def get_previous_period(period: str) -> Optional[str]:
    """
    Get the comparison period for a given period.

    Args:
        period: The current period string

    Returns:
        The previous period string for comparison, or None if no comparison is possible
    """
    period_mapping = {
        "current_month": "last_month",
        "last_month": "two_months_ago",
        "current_week": "last_week",
        "last_week": "two_weeks_ago",
        "current_year": "last_year",
        "last_year": "two_years_ago",
        "all_time": None,  # No comparison for all time
    }
    return period_mapping.get(period)


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

    elif period == "two_months_ago":
        # Two months ago: 1st to last day of the month before last
        first_of_this_month = date(today.year, today.month, 1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        first_of_last_month = date(last_of_last_month.year, last_of_last_month.month, 1)
        last_of_two_months_ago = first_of_last_month - timedelta(days=1)
        start = date(last_of_two_months_ago.year, last_of_two_months_ago.month, 1)
        end = last_of_two_months_ago

    elif period == "current_year":
        # Current year: 1st Jan to today
        start = date(today.year, 1, 1)
        end = today

    elif period == "last_year":
        # Last year: 1st Jan to 31st Dec of previous year
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)

    elif period == "two_years_ago":
        # Two years ago: 1st Jan to 31st Dec of year before last
        start = date(today.year - 2, 1, 1)
        end = date(today.year - 2, 12, 31)

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

    elif period == "two_weeks_ago":
        # Two weeks ago: Monday to Sunday of two weeks before current
        days_since_monday = today.weekday()
        end_of_last_week = today - timedelta(days=days_since_monday + 1)
        end_of_two_weeks_ago = end_of_last_week - timedelta(days=7)
        start_of_two_weeks_ago = end_of_two_weeks_ago - timedelta(days=6)
        start = start_of_two_weeks_ago
        end = end_of_two_weeks_ago

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

