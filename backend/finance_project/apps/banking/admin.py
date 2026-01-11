from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import BankAccount, Transaction, Category, Rule


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "institution", "currency", "opening_balance_display", "opening_balance_date", "transaction_count", "created_at")
    list_filter = ("currency", "institution", "created_at")
    search_fields = ("name", "institution", "user__username", "iban")
    readonly_fields = ("created_at", "transaction_count_display", "current_balance_display")
    fieldsets = (
        ("Account Information", {
            "fields": ("user", "name", "institution", "iban", "currency")
        }),
        ("Balance Configuration", {
            "fields": ("opening_balance", "opening_balance_date", "current_balance_display")
        }),
        ("Statistics", {
            "fields": ("transaction_count_display", "created_at"),
            "classes": ("collapse",)
        }),
    )
    actions = ["truncate_transactions", "generate_categories_for_users"]

    def opening_balance_display(self, obj):
        """Display opening balance with currency."""
        return f"{obj.currency} {obj.opening_balance:.2f}"
    opening_balance_display.short_description = "Opening Balance"

    def current_balance_display(self, obj):
        """Display current balance calculation."""
        from django.db.models import Sum
        tx_sum = Transaction.objects.filter(account=obj).aggregate(total=Sum("amount"))["total"] or 0
        if obj.opening_balance_date:
            tx_sum = Transaction.objects.filter(
                account=obj,
                date__gte=obj.opening_balance_date
            ).aggregate(total=Sum("amount"))["total"] or 0
        current = obj.opening_balance + tx_sum
        # Format balance as string first to avoid format code conflict
        formatted_balance = f"{current:.2f}"
        return format_html(
            '<strong style="color: #0066cc; font-size: 14px;">{} {}</strong>',
            obj.currency, formatted_balance
        )
    current_balance_display.short_description = "Current Balance (Calculated)"

    def transaction_count(self, obj):
        """Display number of transactions."""
        count = obj.transactions.count()
        return format_html(
            '<span style="background-color: #e8f4f8; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    transaction_count.short_description = "Transactions"

    def transaction_count_display(self, obj):
        """Display transaction count for readonly field."""
        count = obj.transactions.count()
        return f"{count} transactions"
    transaction_count_display.short_description = "Transaction Count"

    def truncate_transactions(self, request, queryset):
        """Admin action to delete all transactions for selected accounts."""
        total_deleted = 0
        for account in queryset:
            deleted_count, _ = Transaction.objects.filter(account=account).delete()
            total_deleted += deleted_count

        self.message_user(
            request,
            f"✓ Successfully deleted {total_deleted} transactions from {queryset.count()} account(s).",
            level=messages.SUCCESS
        )
    truncate_transactions.short_description = "🗑️ Delete all transactions for selected accounts"

    def generate_categories_for_users(self, request, queryset):
        """
        AI-powered: Generate categories from transactions for account owners.
        """
        from ..ai.services.category_generator import CategoryGeneratorService
        from ..ai.services.insights_service import ProviderRegistry

        # Get active AI provider (optional)
        provider = None
        try:
            provider = ProviderRegistry.get_active()
        except Exception:
            pass

        service = CategoryGeneratorService(provider=provider)

        # Get unique users from selected accounts
        user_ids = set(queryset.values_list('user_id', flat=True))

        total_suggestions = 0
        total_created = 0

        for user_id in user_ids:
            suggestions = service.analyze_transactions(user_id)
            total_suggestions += len(suggestions)

            created = service.create_categories(user_id, suggestions, auto_approve=True)
            total_created += len([c for c in created if c.get('created', False)])

        self.message_user(
            request,
            f"🤖 Generated {total_suggestions} category suggestions and auto-created {total_created} categories for {len(user_ids)} user(s).",
            level=messages.SUCCESS
        )
    generate_categories_for_users.short_description = "🤖 AI: Generate categories from transactions"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "date", "amount_display", "type", "category", "description_preview", "partner_name")
    list_filter = ("type", "category", "account", "date")
    search_fields = ("description", "partner_name", "reference_number")
    date_hierarchy = "date"
    readonly_fields = ("created_at",)
    actions = ["truncate_transactions"]

    def amount_display(self, obj):
        """Display amount with currency and color coding."""
        color = "#10b981" if obj.amount >= 0 else "#ef4444"  # green for positive, red for negative
        # Format amount as string first to avoid format code conflict
        formatted_amount = f"{obj.amount:.2f}"
        return format_html(
            '<strong style="color: {};">{} {}</strong>',
            color, obj.account.currency, formatted_amount
        )
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def description_preview(self, obj):
        """Display truncated description."""
        if obj.description:
            preview = obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
            return format_html('<span title="{}">{}</span>', obj.description, preview)
        return "-"
    description_preview.short_description = "Description"

    def truncate_transactions(self, request, queryset):
        """Admin action to delete selected transactions."""
        count = queryset.count()
        queryset.delete()

        self.message_user(
            request,
            f"✓ Successfully deleted {count} transaction(s).",
            level="success"
        )
    truncate_transactions.short_description = "🗑️ Delete selected transactions"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color")
    search_fields = ("name",)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "priority", "active")
    list_filter = ("active",)
    search_fields = ("name",)

