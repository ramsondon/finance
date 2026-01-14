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

    # Pattern details
    description = models.CharField(max_length=255)
    merchant_name = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)

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
        return f"{self.description} ({self.frequency})"

    def get_display_name(self) -> str:
        """Get the best display name for this recurring transaction."""
        return self.merchant_name or self.description

    def is_overdue(self) -> bool:
        """Check if this recurring transaction is overdue (missed)."""
        from datetime import datetime
        return datetime.now().date() > self.next_expected_date

    def days_until_next(self) -> int:
        """Days until next expected occurrence."""
        from datetime import datetime
        delta = self.next_expected_date - datetime.now().date()
        return delta.days

