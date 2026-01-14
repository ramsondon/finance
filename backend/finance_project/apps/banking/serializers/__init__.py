from rest_framework import serializers
from django.db.models import Sum
from ..models import BankAccount, Transaction, Category, Rule


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "color"]


class BankAccountSerializer(serializers.ModelSerializer):
    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ["id", "name", "institution", "iban", "currency", "opening_balance", "opening_balance_date", "current_balance", "created_at"]
        read_only_fields = ["created_at", "current_balance"]

    def get_current_balance(self, obj):
        """Calculate the current balance based on opening_balance and filtered transactions."""
        # Build query for transactions
        tx_query = Transaction.objects.filter(account=obj)

        # If opening_balance_date is set, only include transactions from that date onward
        if obj.opening_balance_date:
            tx_query = tx_query.filter(date__gte=obj.opening_balance_date)

        # Sum transactions for this account
        tx_sum = tx_query.aggregate(total=Sum("amount"))["total"] or 0

        # Calculate current balance: opening_balance + sum of transactions
        return float(obj.opening_balance + tx_sum)


class TransactionSerializer(serializers.ModelSerializer):
    account_currency = serializers.CharField(source='account.currency', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "account_currency",
            "date",
            "amount",
            "description",
            "category",
            "category_name",
            "category_color",
            "type",
            # Extended fields
            "partner_name",
            "partner_iban",
            "partner_account_number",
            "partner_bank_code",
            "owner_account",
            "owner_name",
            "reference_number",
            "booking_date",
            "valuation_date",
            "virtual_card_number",
            "virtual_card_device",
            "payment_app",
            "payment_method",
            "merchant_name",
            "card_brand",
            "exchange_rate",
            "transaction_fee",
            "booking_type",
            "sepa_scheme",
            "meta",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ["id", "name", "conditions", "category", "priority", "active"]
