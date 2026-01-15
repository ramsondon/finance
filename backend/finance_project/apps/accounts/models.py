from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # DEPRECATED: Use preferences['currency'] instead
    # This field is kept for backward compatibility but will be removed in a future version
    currency_preference = models.CharField(max_length=8, default="USD", db_column='currency_preference')
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Profile({self.user.username})"

    # ==================== Language Preferences ====================

    def get_language(self) -> str:
        """
        Get user's language preference from preferences JSONField.

        Returns:
            Language code ('en', 'de', etc.)
            Defaults to 'en' if not set.
        """
        return self.preferences.get('language', 'en')

    def set_language(self, language_code: str) -> None:
        """
        Set user's language preference in preferences JSONField.

        Args:
            language_code: Language code ('en', 'de', etc.)
        """
        if not self.preferences:
            self.preferences = {}
        self.preferences['language'] = language_code
        self.save(update_fields=['preferences'])

    # ==================== Currency Preferences ====================

    def get_currency(self) -> str:
        """
        Get user's currency preference from preferences JSONField.
        Falls back to legacy currency_preference field for backward compatibility.

        Returns:
            Currency code (e.g., 'USD', 'EUR', 'GBP')
            Defaults to 'USD' if not set.
        """
        # Try preferences first (new way)
        if 'currency' in self.preferences:
            return self.preferences.get('currency', 'USD')
        # Fall back to legacy field
        return self.currency_preference or 'USD'

    def set_currency(self, currency_code: str) -> None:
        """
        Set user's currency preference in preferences JSONField.
        Also updates legacy currency_preference field for backward compatibility.

        Args:
            currency_code: Currency code (e.g., 'USD', 'EUR', 'GBP')
        """
        if not self.preferences:
            self.preferences = {}
        self.preferences['currency'] = currency_code
        # Update legacy field too for backward compatibility
        self.currency_preference = currency_code
        self.save(update_fields=['preferences', 'currency_preference'])

    # ==================== Generic Preference Methods ====================

    def get_preference(self, key: str, default=None):
        """
        Get a preference value by key.

        Supported keys:
            - 'language': Language code ('en', 'de', etc.)
            - 'currency': Currency code ('USD', 'EUR', etc.)
            - 'dateFormat': Date format preference
            - 'timeFormat': Time format preference
            - 'numberFormat': Number format preference
            - Any custom preference

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value or default
        """
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value) -> None:
        """
        Set a preference value by key.

        Supported keys:
            - 'language': Language code ('en', 'de', etc.)
            - 'currency': Currency code ('USD', 'EUR', etc.)
            - 'dateFormat': Date format preference
            - 'timeFormat': Time format preference
            - 'numberFormat': Number format preference
            - Any custom preference

        Args:
            key: Preference key
            value: Preference value
        """
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value

        # Special handling: if setting currency, also update legacy field
        if key == 'currency':
            self.currency_preference = value
            self.save(update_fields=['preferences', 'currency_preference'])
        else:
            self.save(update_fields=['preferences'])

    def get_all_preferences(self) -> dict:
        """
        Get all user preferences as a dictionary.

        Returns:
            Dictionary of all preferences including legacy currency_preference
        """
        prefs = dict(self.preferences) if self.preferences else {}

        # Ensure currency is set (with fallback to legacy field)
        if 'currency' not in prefs:
            prefs['currency'] = self.currency_preference or 'USD'

        return prefs


class AllowedGoogleUser(models.Model):
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.email
