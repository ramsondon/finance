"""
Exchange Rate Service

Handles currency conversion using cached USD-based rates.
Base currency is USD (from OpenExchangeRates API).

Features:
- Convert any currency to any other currency
- Get account balance converted to user's preferred currency
- Get age of cached rates
- Fallback to SYSTEM_DEFAULT_CURRENCY if user currency not available
"""
from __future__ import annotations
from decimal import Decimal
import logging
from django.utils import timezone
from ..models import ExchangeRate
from ...accounts.models import UserProfile

logger = logging.getLogger(__name__)


class ExchangeService:
    """
    Service for currency conversion using USD-based rates.

    All rates are stored relative to USD (base currency).
    Conversion formula: amount_in_target = amount_in_source * (rate_target / rate_source)
    """

    BASE_CURRENCY = "USD"

    @staticmethod
    def convert(amount: Decimal | float, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert amount from one currency to another.

        Uses cached USD-based rates from ExchangeRate model.
        If either currency not available, returns original amount and logs warning.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'EUR', 'GBP')
            to_currency: Target currency code (e.g., 'USD', 'EUR')

        Returns:
            Converted amount as Decimal, or original amount if conversion not possible
        """
        if from_currency == to_currency:
            return Decimal(str(amount))

        rate_obj = ExchangeRate.get_rates()
        rates = rate_obj.rates or {}

        try:
            amount = Decimal(str(amount))

            # Get rates (USD = 1.0 as base)
            from_rate = Decimal(str(rates.get(from_currency, 1.0)))
            to_rate = Decimal(str(rates.get(to_currency, 1.0)))

            # If from_currency is USD, rate = 1.0
            if from_currency == ExchangeService.BASE_CURRENCY:
                from_rate = Decimal("1.0")

            # If to_currency is USD, rate = 1.0
            if to_currency == ExchangeService.BASE_CURRENCY:
                to_rate = Decimal("1.0")

            # Conversion formula: amount_in_target = amount_in_source * (rate_target / rate_source)
            if from_rate == 0:
                logger.warning(f"Cannot convert from {from_currency}: rate is 0")
                return amount

            converted = amount * (to_rate / from_rate)
            return Decimal(str(round(converted, 2)))

        except Exception as e:
            logger.error(f"Conversion error {from_currency}->{to_currency}: {e}")
            return Decimal(str(amount))

    @staticmethod
    def get_user_converted_balance(account: BankAccount, user_profile: UserProfile) -> Decimal:
        """
        Get account balance converted to user's preferred currency.

        Args:
            account: BankAccount instance
            user_profile: UserProfile instance with currency preference

        Returns:
            Converted balance as Decimal
        """
        from ...analytics.services.stats_service import StatsService

        # Get account balance in account's currency
        stats_service = StatsService()
        account_balance = stats_service.get_account_balance(account)

        # Get user's preferred currency
        user_currency = user_profile.get_currency()

        # If account already in user's currency, no conversion needed
        if account.currency == user_currency:
            return Decimal(str(account_balance))

        # Convert from account currency to user currency
        return ExchangeService.convert(account_balance, account.currency, user_currency)

    @staticmethod
    def get_rate_age() -> str:
        """
        Get human-readable age of cached exchange rates.

        Returns:
            String like "2h 15m ago", "Just now", "1d 3h ago", etc.
        """
        rate_obj = ExchangeRate.get_rates()

        if not rate_obj.last_updated:
            return "Never updated"

        # Get current timezone-aware datetime
        now = timezone.now()
        last_updated = rate_obj.last_updated

        # Ensure both are timezone-aware
        if last_updated.tzinfo is None:
            last_updated = timezone.make_aware(last_updated)

        delta = now - last_updated
        seconds = delta.total_seconds()

        if seconds < 60:
            return "Just now"

        minutes = int(seconds // 60)
        if minutes < 60:
            return f"{minutes}m ago"

        hours = int(minutes // 60)
        remaining_mins = minutes % 60
        if hours < 24:
            if remaining_mins > 0:
                return f"{hours}h {remaining_mins}m ago"
            return f"{hours}h ago"

        days = int(hours // 24)
        remaining_hours = hours % 24
        if days < 7:
            if remaining_hours > 0:
                return f"{days}d {remaining_hours}h ago"
            return f"{days}d ago"

        weeks = int(days // 7)
        remaining_days = days % 7
        if weeks < 4:
            if remaining_days > 0:
                return f"{weeks}w {remaining_days}d ago"
            return f"{weeks}w ago"

        return f"{days}d ago"

    @staticmethod
    def get_conversion_rate(from_currency: str, to_currency: str) -> Decimal:
        """
        Get the conversion rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Conversion rate as Decimal (e.g., 0.92 means 1 EUR = 0.92 USD)
        """
        if from_currency == to_currency:
            return Decimal("1.0")

        rate_obj = ExchangeRate.get_rates()
        rates = rate_obj.rates or {}

        try:
            from_rate = Decimal(str(rates.get(from_currency, 1.0)))
            to_rate = Decimal(str(rates.get(to_currency, 1.0)))

            if from_currency == ExchangeService.BASE_CURRENCY:
                from_rate = Decimal("1.0")

            if to_currency == ExchangeService.BASE_CURRENCY:
                to_rate = Decimal("1.0")

            if from_rate == 0:
                return Decimal("0")

            return Decimal(str(round(to_rate / from_rate, 6)))

        except Exception as e:
            logger.error(f"Error getting conversion rate {from_currency}->{to_currency}: {e}")
            return Decimal("1.0")

