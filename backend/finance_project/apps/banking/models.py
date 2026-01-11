from django.conf import settings
from django.db import models


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#3b82f6")  # hex

    class Meta:
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
