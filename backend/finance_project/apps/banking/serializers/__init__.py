from rest_framework import serializers
from django.db.models import Sum
from ..models import BankAccount, Transaction, Category, Rule


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "color"]

    def validate_name(self, value):
        """Check if category with this name already exists for the user."""
        # Get the user from context (set by the view)
        user = self.context.get('request').user if self.context.get('request') else None

        if user:
            # Check if a category with this name already exists for this user
            queryset = Category.objects.filter(user=user, name__iexact=value)

            # If updating, exclude the current instance
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    f"A category with this name already exists."
                )

        return value


class BankAccountSerializer(serializers.ModelSerializer):
    current_balance = serializers.SerializerMethodField()
    converted_balance = serializers.SerializerMethodField()
    conversion_rate_age = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ["id", "name", "institution", "iban", "currency", "opening_balance", "opening_balance_date", "current_balance", "converted_balance", "conversion_rate_age", "created_at"]
        read_only_fields = ["created_at", "current_balance", "converted_balance", "conversion_rate_age"]

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

    def get_converted_balance(self, obj):
        """Convert account balance to user's preferred currency."""
        try:
            from ..services.exchange_service import ExchangeService
            from ...accounts.models import UserProfile

            user_profile = UserProfile.objects.get(user=obj.user)
            converted = ExchangeService.get_user_converted_balance(obj, user_profile)
            return float(converted)
        except Exception as e:
            # If conversion fails, return current balance in account currency
            import logging
            logging.warning(f"Failed to convert balance for account {obj.id}: {e}")
            return self.get_current_balance(obj)

    def get_conversion_rate_age(self, obj):
        """Get human-readable age of exchange rates."""
        try:
            from ..services.exchange_service import ExchangeService
            return ExchangeService.get_rate_age()
        except Exception as e:
            import logging
            logging.warning(f"Failed to get rate age: {e}")
            return "Unknown"



class TransactionSerializer(serializers.ModelSerializer):
    account_currency = serializers.CharField(source='account.currency', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "account_currency",
            "account_name",
            "date",
            "amount",
            "reference",
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
