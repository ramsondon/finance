from django.conf import settings
from django.db import models


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#3b82f6")  # hex

    class Meta:
        ordering = ["user", "name"]
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"


class BankAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=34, blank=True)  # IBAN max length is 34 chars
    currency = models.CharField(max_length=8, default="EUR")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    opening_balance_date = models.DateField(null=True, blank=True, help_text="Reference date for opening balance. If set, balance calculations start from this date.")
    meta = models.JSONField(default=dict, blank=True, help_text="Additional metadata including import settings")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"


class Transaction(models.Model):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
        (TRANSFER, "Transfer"),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=512)
    description = models.CharField(max_length=1024, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # Extended fields for rich transaction data
    partner_name = models.CharField(max_length=255, blank=True)
    partner_iban = models.CharField(max_length=34, blank=True)
    partner_account_number = models.CharField(max_length=50, blank=True)
    partner_bank_code = models.CharField(max_length=20, blank=True)

    owner_account = models.CharField(max_length=50, blank=True)
    owner_name = models.CharField(max_length=255, blank=True)

    reference_number = models.CharField(max_length=100, blank=True)
    booking_date = models.DateField(null=True, blank=True)
    valuation_date = models.DateField(null=True, blank=True)

    virtual_card_number = models.CharField(max_length=20, blank=True)  # Masked
    virtual_card_device = models.CharField(max_length=1024, blank=True)  # Increased from 255
    payment_app = models.CharField(max_length=100, blank=True)  # e.g., Google Pay

    payment_method = models.CharField(max_length=50, blank=True)  # e.g., CARD, SEPA, TRANSFER
    merchant_name = models.CharField(max_length=255, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)  # VISA, Mastercard, etc.

    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    transaction_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    booking_type = models.CharField(max_length=100, blank=True)
    sepa_scheme = models.CharField(max_length=50, blank=True)

    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["date", "account"]),
            models.Index(fields=["amount", "account"]),
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.amount} {self.description}"


class Rule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    conditions = models.JSONField(default=dict)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority", "id"]

    def __str__(self) -> str:
        return f"Rule({self.name})"


class ExchangeRate(models.Model):
    """
    Global singleton model for storing USD-based exchange rates.

    OpenExchangeRates API provides rates with USD as base currency.
    This model caches the rates with last_updated timestamp for tracking freshness.
    """
    # Rates stored as JSON: {"EUR": 0.92, "GBP": 0.79, "JPY": 145.5, ...}
    rates = models.JSONField(default=dict, help_text="Exchange rates with USD as base (e.g., {EUR: 0.92, GBP: 0.79})")

    # When rates were last successfully fetched
    last_updated = models.DateTimeField(auto_now_add=True, help_text="Timestamp of last successful rate fetch from API")

    # Metadata
    api_url = models.URLField(blank=True, help_text="API endpoint used for fetch")
    error_message = models.TextField(blank=True, help_text="Last error message if fetch failed")

    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"

    def __str__(self) -> str:
        return f"ExchangeRate(updated={self.last_updated.strftime('%Y-%m-%d %H:%M:%S') if self.last_updated else 'never'})"

    @staticmethod
    def get_rates():
        """Get the current cached rates. Creates default if doesn't exist."""
        rate_obj, _ = ExchangeRate.objects.get_or_create(pk=1)
        return rate_obj


class RecurringTransaction(models.Model):
    """
    Stores detected recurring transaction patterns.

    Used to track subscriptions, regular payments, and other recurring costs.
    """
    FREQUENCY_CHOICES = [
        ("weekly", "Weekly"),
        ("bi-weekly", "Bi-weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="recurring_transactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Pattern details (used by algorithm - do not edit)
    description = models.CharField(max_length=255, help_text="Original description used for pattern matching")
    merchant_name = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)

    # User customization
    display_name = models.CharField(max_length=255, blank=True, help_text="User-defined display name (falls back to merchant_name or description)")

    # Timing
    next_expected_date = models.DateField()
    last_occurrence_date = models.DateField()

    # Statistics
    occurrence_count = models.PositiveIntegerField(default=1)
    confidence_score = models.FloatField(default=0.0, help_text="0-1 confidence that this is truly recurring")

    # Tracking
    is_active = models.BooleanField(default=True)
    is_ignored = models.BooleanField(default=False, help_text="User marked this as not relevant")
    user_notes = models.TextField(blank=True, help_text="User's notes about this recurring transaction")

    # Meta
    similar_descriptions = models.JSONField(default=list, help_text="All transaction descriptions that matched this pattern")
    transaction_ids = models.JSONField(default=list, help_text="IDs of transactions that form this pattern")

    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-confidence_score", "-occurrence_count"]
        unique_together = ("account", "description", "frequency")
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["account", "is_active"]),
            models.Index(fields=["frequency", "next_expected_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_display_name()} ({self.frequency})"

    def get_display_name(self) -> str:
        """Get the best display name for this recurring transaction."""
        return self.display_name or self.merchant_name or self.description

    def is_overdue(self) -> bool:
        """Check if this recurring transaction is overdue (missed)."""
        from datetime import datetime
        return datetime.now().date() > self.next_expected_date

    def days_until_next(self) -> int:
        """Days until next expected occurrence."""
        from datetime import datetime
        delta = self.next_expected_date - datetime.now().date()
        return delta.days


class Import(models.Model):
    """
    Tracks individual import sessions.

    Each time transactions are imported from a file or data source,
    a new Import record is created to group all transactions from that import.
    """
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="imports")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Import metadata
    import_source = models.CharField(max_length=100, blank=True, help_text="Source of import (e.g., 'csv', 'bank_api', 'manual')")
    file_name = models.CharField(max_length=255, blank=True, help_text="Original file name if imported from file")

    # Statistics
    total_transactions = models.PositiveIntegerField(default=0, help_text="Total number of transactions in this import")
    successful_transactions = models.PositiveIntegerField(default=0, help_text="Number of successfully processed transactions")
    failed_transactions = models.PositiveIntegerField(default=0, help_text="Number of transactions that failed to process")

    # Status tracking
    meta = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the import process")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this import was created")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Import({self.account.name}, {self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class ImportTransaction(models.Model):
    """
    Links transactions to their import session.

    Allows tracing which import created or updated which transactions,
    useful for auditing and bulk operations on imported data.
    """
    import_record = models.ForeignKey(Import, on_delete=models.CASCADE, related_name="import_transactions")
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="imports")

    # Track what happened during import
    was_created = models.BooleanField(default=True, help_text="True if transaction was created, False if updated")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("import_record", "transaction")
        indexes = [
            models.Index(fields=["import_record", "was_created"]),
            models.Index(fields=["transaction", "-created_at"]),
        ]

    def __str__(self) -> str:
        action = "Created" if self.was_created else "Updated"
        return f"ImportTransaction({action}, {self.transaction.id})"

