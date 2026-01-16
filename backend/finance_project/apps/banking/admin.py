from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.contrib import messages
from .models import BankAccount, Transaction, Category, Rule, RecurringTransaction, ExchangeRate


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
    list_display = ("id", "account", "date", "amount_display", "type", "category", "reference", "description_preview", "partner_name")
    list_filter = ("type", "category", "account", "date")
    search_fields = ("reference", "description", "partner_name", "reference_number")
    date_hierarchy = "date"
    readonly_fields = ("created_at",)
    actions = ["truncate_transactions", "clear_categories"]

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
    truncate_transactions.short_description = "🗑️ Truncate selected transactions"

    def clear_categories(self, request, queryset):
        """Admin action to clear categories for selected transactions."""
        updated_count = queryset.update(category=None)

        self.message_user(
            request,
            f"✓ Cleared categories for {updated_count} transaction(s).",
            level="success"
        )
    clear_categories.short_description = "❌ Clear categories for selected transactions"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color")
    search_fields = ("name",)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "priority", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "get_display_name",
        "user",
        "account",
        "amount_display",
        "frequency",
        "next_expected_date",
        "occurrence_count",
        "confidence_score_display",
        "is_active",
        "is_ignored",
    )
    list_filter = (
        "frequency",
        "is_active",
        "is_ignored",
        "account",
        ("confidence_score", admin.NumericRangeFilter) if hasattr(admin, "NumericRangeFilter") else "confidence_score",
        "detected_at",
    )
    search_fields = (
        "description",
        "merchant_name",
        "user__username",
        "account__name",
    )
    readonly_fields = (
        "detected_at",
        "updated_at",
        "transaction_ids_display",
        "similar_descriptions_display",
        "confidence_details",
    )
    fieldsets = (
        (
            "Pattern Information",
            {
                "fields": (
                    "user",
                    "account",
                    "description",
                    "merchant_name",
                    "amount",
                    "frequency",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "last_occurrence_date",
                    "next_expected_date",
                    "occurrence_count",
                )
            },
        ),
        (
            "Detection Quality",
            {
                "fields": (
                    "confidence_score",
                    "confidence_details",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_ignored",
                    "user_notes",
                )
            },
        ),
        (
            "Transaction Matching",
            {
                "fields": (
                    "transaction_ids_display",
                    "similar_descriptions_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "detected_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "next_expected_date"
    ordering = ["-confidence_score", "-occurrence_count"]

    def get_display_name(self, obj):
        """Get the best display name for this recurring transaction."""
        return obj.get_display_name()

    get_display_name.short_description = "Name"

    def amount_display(self, obj):
        """Display amount with currency."""
        return format_html(
            '<strong style="color: #ef4444;">{} {}</strong>',
            obj.account.currency,
            format(obj.amount, '.2f'),
        )

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def confidence_score_display(self, obj):
        """Display confidence score as a percentage with color coding."""
        score_pct = obj.confidence_score * 100
        if obj.confidence_score >= 0.9:
            color = "#10b981"  # green
        elif obj.confidence_score >= 0.75:
            color = "#3b82f6"  # blue
        elif obj.confidence_score >= 0.6:
            color = "#f59e0b"  # amber
        else:
            color = "#ef4444"  # red

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}%</span>',
            color,
            format(score_pct, '.0f'),
        )

    confidence_score_display.short_description = "Confidence"
    confidence_score_display.admin_order_field = "confidence_score"

    def confidence_details(self, obj):
        """Display explanation of confidence score calculation."""
        return format_html(
            '<div style="padding: 10px; background-color: #f3f4f6; border-radius: 4px; font-family: monospace; font-size: 12px;">'
            '<strong>Confidence Score: {}%</strong><br>'
            '<br>'
            'Calculated from:<br>'
            '• Interval consistency (50% weight)<br>'
            '• Amount consistency (30% weight)<br>'
            '• Occurrence count (20% weight)<br>'
            '<br>'
            'Minimum threshold: 60%<br>'
            'Occurrences: {}'
            '</div>',
            format(obj.confidence_score * 100, '.1f'),
            obj.occurrence_count,
        )

    confidence_details.short_description = "How Confidence is Calculated"

    def transaction_ids_display(self, obj):
        """Display the transaction IDs that form this pattern."""
        ids = obj.transaction_ids or []
        if not ids:
            return "-"
        id_list = ", ".join(str(tid) for tid in ids)
        return format_html(
            '<code style="background-color: #f3f4f6; padding: 4px 8px; border-radius: 4px;">{}</code>',
            id_list,
        )

    transaction_ids_display.short_description = "Matching Transaction IDs"

    def similar_descriptions_display(self, obj):
        """Display all similar descriptions found for this pattern."""
        descriptions = obj.similar_descriptions or []
        if not descriptions:
            return "-"
        desc_html = "<br>".join(
            format_html(
                '<div style="margin: 4px 0; padding: 4px 8px; background-color: #f3f4f6; border-radius: 4px;">• {}</div>',
                desc,
            )
            for desc in descriptions[:10]  # Show first 10
        )
        if len(descriptions) > 10:
            desc_html += format_html(
                '<div style="margin: 4px 0; padding: 4px 8px; color: #6b7280;">... and {} more</div>',
                len(descriptions) - 10,
            )
        return format_html("<div>{}</div>", desc_html)

    similar_descriptions_display.short_description = "Similar Descriptions Found"

    def has_add_permission(self, request):
        """Disable manual creation - only via detection."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers."""
        return request.user.is_superuser


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("last_updated", "currencies_count", "status_display")
    readonly_fields = ("rates_pretty", "last_updated", "api_url", "error_message")
    fields = ("rates_pretty", "last_updated", "api_url", "error_message")
    actions = ["fetch_exchange_rates"]

    def currencies_count(self, obj):
        """Display number of currencies in rates."""
        count = len(obj.rates or {})
        return format_html(
            '<span style="background-color: #d1fae5; color: #065f46; padding: 3px 8px; border-radius: 3px; font-weight: 500;">{} currencies</span>',
            count
        )
    currencies_count.short_description = "Currencies"

    def status_display(self, obj):
        """Display status of last fetch."""
        if obj.error_message:
            return mark_safe(
                '<span style="background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 3px;">❌ Error</span>'
            )
        return mark_safe(
            '<span style="background-color: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 3px;">✓ OK</span>'
        )
    status_display.short_description = "Status"

    def rates_pretty(self, obj):
        """Display rates in a pretty format."""
        import json
        if not obj.rates:
            return "No rates cached"
        # Show first 20 rates
        rates = obj.rates
        display_rates = dict(list(rates.items())[:20])
        pretty_json = json.dumps(display_rates, indent=2)
        if len(rates) > 20:
            pretty_json += f"\n... and {len(rates) - 20} more currencies"
        return format_html(
            '<pre style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; font-size: 12px;">{}</pre>',
            pretty_json
        )
    rates_pretty.short_description = "Exchange Rates (first 20)"

    def fetch_exchange_rates(self, request, queryset):
        """Admin action to manually fetch exchange rates from API."""
        from .tasks import fetch_exchange_rates_task
        from django.contrib import messages

        try:
            # Start the async task
            task = fetch_exchange_rates_task.delay()

            self.message_user(
                request,
                f"🔄 Exchange rates fetch started (Task ID: {task.id}). Rates will be updated shortly.",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Failed to start fetch task: {str(e)}",
                level=messages.ERROR
            )

    fetch_exchange_rates.short_description = "🔄 Fetch latest exchange rates from API"

    def has_add_permission(self, request):
        """Prevent manual addition - only via API fetch."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of exchange rates."""
        return False

    def changelist_view(self, request, extra_context=None):
        """Show only one exchange rate record."""
        extra_context = extra_context or {}
        # Ensure only the singleton record exists
        from .models import ExchangeRate
        ExchangeRate.get_rates()
        return super().changelist_view(request, extra_context)
