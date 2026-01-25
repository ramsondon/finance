from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.contrib import messages
from .models import BankAccount, Transaction, Category, Rule, RecurringTransaction, ExchangeRate, Import, ImportTransaction, Anomaly, AnomalyNotification, UserAnomalyPreferences


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
    actions = ["truncate_transactions", "generate_categories_for_users", "trigger_anomaly_detection"]

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

    def trigger_anomaly_detection(self, request, queryset):
        """
        Admin action to manually trigger anomaly detection for selected accounts.
        """
        import logging
        from .services.anomaly_detector import AnomalyDetectionService, create_anomaly_if_new

        logger = logging.getLogger(__name__)
        logger.info(f"Starting anomaly detection for {queryset.count()} accounts")

        total_accounts = queryset.count()
        total_transactions = 0
        total_anomalies = 0
        errors = []

        for account in queryset:
            try:
                logger.info(f"Processing account: {account.name}")
                # Get all transactions for this account
                transactions = Transaction.objects.filter(account=account)
                transactions_count = transactions.count()
                logger.info(f"Account {account.name} has {transactions_count} transactions")

                detector = AnomalyDetectionService(account.user, account)
                logger.info(f"Detector initialized for user {account.user.username}, detection enabled: {detector.preferences.anomaly_detection_enabled}")
                logger.info(f"Enabled types: {detector.preferences.enabled_types}")

                for transaction in transactions:
                    anomalies = detector.detect_all_anomalies_for_transaction(transaction)
                    logger.info(f"Transaction {transaction.id} detected {len(anomalies)} anomalies")

                    # Save anomalies and create notifications
                    for anomaly in anomalies:
                        created = create_anomaly_if_new(anomaly)
                        if created:
                            logger.info(f"Created anomaly: {anomaly.anomaly_type}")
                            total_anomalies += 1
                        else:
                            logger.info(f"Duplicate anomaly skipped: {anomaly.anomaly_type}")
                    total_transactions += 1

            except Exception as e:
                logger.error(f"Error processing account {account.name}: {str(e)}", exc_info=True)
                errors.append(f"Error processing account {account.name}: {str(e)}")

        if errors:
            message = f"⚠️ Anomaly detection completed with errors:\n" + "\n".join(errors[:3])
            if len(errors) > 3:
                message += f"\n... and {len(errors) - 3} more errors"
            self.message_user(request, message, level=messages.WARNING)
        else:
            message = (
                f"🚨 Anomaly detection completed!\n"
                f"Accounts: {total_accounts}\n"
                f"Transactions scanned: {total_transactions}\n"
                f"Anomalies detected: {total_anomalies}"
            )
            self.message_user(request, message, level=messages.SUCCESS)

        logger.info(f"Anomaly detection complete. Total anomalies: {total_anomalies}")
    trigger_anomaly_detection.short_description = "🚨 Trigger anomaly detection"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "date", "amount_display", "type", "category", "reference", "description_preview", "partner_name")
    list_filter = ("type", "category", "account", "date")
    search_fields = ("reference", "description", "partner_name", "reference_number")
    date_hierarchy = "date"
    readonly_fields = ("created_at",)
    actions = ["truncate_transactions", "clear_categories", "detect_anomalies_for_transactions"]

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

    def detect_anomalies_for_transactions(self, request, queryset):
        """
        Admin action to manually trigger anomaly detection for selected transactions.
        """
        from .services.anomaly_detector import AnomalyDetectionService, create_anomaly_if_new

        total_transactions = queryset.count()
        total_anomalies = 0
        errors = []

        try:
            # Group transactions by account to reuse detector
            accounts = {}
            for transaction in queryset:
                account_id = transaction.account_id
                if account_id not in accounts:
                    accounts[account_id] = {
                        'account': transaction.account,
                        'user': transaction.account.user,
                        'transactions': []
                    }
                accounts[account_id]['transactions'].append(transaction)

            # Detect anomalies for each account
            for account_info in accounts.values():
                detector = AnomalyDetectionService(account_info['user'], account_info['account'])
                for transaction in account_info['transactions']:
                    anomalies = detector.detect_all_anomalies_for_transaction(transaction)
                    # Save anomalies and create notifications
                    for anomaly in anomalies:
                        if create_anomaly_if_new(anomaly):
                            total_anomalies += 1

            message = (
                f"🚨 Anomaly detection completed!\n"
                f"Transactions scanned: {total_transactions}\n"
                f"Anomalies detected: {total_anomalies}"
            )
            self.message_user(request, message, level=messages.SUCCESS)
        except Exception as e:
            error_msg = f"❌ Error during anomaly detection: {str(e)}"
            self.message_user(request, error_msg, level=messages.ERROR)
    detect_anomalies_for_transactions.short_description = "🚨 Detect anomalies for selected transactions"


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


@admin.register(Import)
class ImportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account_name",
        "user_display",
        "import_source",
        "file_name_display",
        "transactions_summary",
        "success_rate_display",
        "created_at_display",
    )
    list_filter = (
        "import_source",
        "created_at",
        "account",
        "user",
    )
    search_fields = (
        "file_name",
        "account__name",
        "user__username",
        "import_source",
    )
    readonly_fields = (
        "account",
        "user",
        "import_source",
        "file_name",
        "total_transactions",
        "successful_transactions",
        "failed_transactions",
        "created_at",
        "meta_pretty",
        "import_transactions_links",
    )
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Import Information",
            {
                "fields": (
                    "account",
                    "user",
                    "import_source",
                    "file_name",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "total_transactions",
                    "successful_transactions",
                    "failed_transactions",
                ),
                "description": "Summary of transaction import results",
            },
        ),
        (
            "Imported Transactions",
            {
                "fields": ("import_transactions_links",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "meta_pretty",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def account_name(self, obj):
        """Display account name with link."""
        return format_html(
            '<a href="/admin/banking/bankaccount/{}/change/">{}</a>',
            obj.account.id,
            obj.account.name
        )
    account_name.short_description = "Account"
    account_name.admin_order_field = "account__name"

    def user_display(self, obj):
        """Display user with link."""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_display.short_description = "User"
    user_display.admin_order_field = "user__username"

    def file_name_display(self, obj):
        """Display file name with truncation."""
        if not obj.file_name:
            return "-"
        if len(obj.file_name) > 40:
            return format_html(
                '<span title="{}">{}</span>',
                obj.file_name,
                obj.file_name[:40] + "..."
            )
        return obj.file_name
    file_name_display.short_description = "File"
    file_name_display.admin_order_field = "file_name"

    def transactions_summary(self, obj):
        """Display transaction counts summary."""
        return format_html(
            '<span style="font-family: monospace;">{} total | {} ✓ | {} ✗</span>',
            obj.total_transactions,
            obj.successful_transactions,
            obj.failed_transactions,
        )
    transactions_summary.short_description = "Transactions"

    def success_rate_display(self, obj):
        """Display success rate as percentage with color coding."""
        if obj.total_transactions == 0:
            return "-"

        success_rate = (obj.successful_transactions / obj.total_transactions) * 100

        if success_rate == 100:
            color = "#10b981"  # green
        elif success_rate >= 90:
            color = "#3b82f6"  # blue
        elif success_rate >= 75:
            color = "#f59e0b"  # amber
        else:
            color = "#ef4444"  # red

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}%</span>',
            color,
            format(success_rate, '.0f'),
        )
    success_rate_display.short_description = "Success Rate"

    def created_at_display(self, obj):
        """Display creation time in a readable format."""
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_display.short_description = "Created"
    created_at_display.admin_order_field = "created_at"

    def meta_pretty(self, obj):
        """Display metadata in a pretty format."""
        import json
        if not obj.meta:
            return "No metadata"
        pretty_json = json.dumps(obj.meta, indent=2)
        return format_html(
            '<pre style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; font-size: 12px;">{}</pre>',
            pretty_json
        )
    meta_pretty.short_description = "Metadata"

    def import_transactions_links(self, obj):
        """Display links to ImportTransaction records for this import."""
        import_txs = obj.import_transactions.all()
        if not import_txs.exists():
            return "No linked transactions yet"

        count = import_txs.count()
        created_count = import_txs.filter(was_created=True).count()
        updated_count = import_txs.filter(was_created=False).count()

        # Create a link to filter ImportTransaction by this Import
        link_url = f'/admin/banking/importtransaction/?import_record__id__exact={obj.id}'

        return format_html(
            '<div style="padding: 10px; background-color: #f0f9ff; border-radius: 4px;">'
            '<strong>{} transactions linked to this import</strong><br>'
            '<a href="{}" style="color: #0066cc; text-decoration: none;">View all transactions →</a><br><br>'
            '<span style="font-size: 12px; color: #6b7280;">'
            '• {} newly created<br>'
            '• {} updated'
            '</span>'
            '</div>',
            count,
            link_url,
            created_count,
            updated_count,
        )
    import_transactions_links.short_description = "Linked Transactions"

    def has_add_permission(self, request):
        """Prevent manual addition - only via import process."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers."""
        return request.user.is_superuser


@admin.register(ImportTransaction)
class ImportTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "import_display",
        "transaction_display",
        "action_display",
        "created_at_display",
    )
    list_filter = (
        "was_created",
        "created_at",
        "import_record__account",
        "import_record__user",
        "import_record__import_source",
    )
    search_fields = (
        "transaction__description",
        "transaction__reference",
        "transaction__partner_name",
        "import_record__file_name",
    )
    readonly_fields = (
        "import_record",
        "transaction",
        "was_created",
        "created_at",
        "transaction_details",
    )
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Link Information",
            {
                "fields": (
                    "import_record",
                    "transaction",
                    "was_created",
                    "created_at",
                ),
            },
        ),
        (
            "Transaction Details",
            {
                "fields": ("transaction_details",),
                "classes": ("collapse",),
            },
        ),
    )

    def import_display(self, obj):
        """Display import with link and account info."""
        return format_html(
            '<a href="/admin/banking/import/{}/change/">Import #{}</a><br>'
            '<span style="font-size: 12px; color: #6b7280;">{} | {}</span>',
            obj.import_record.id,
            obj.import_record.id,
            obj.import_record.account.name,
            obj.import_record.created_at.strftime("%Y-%m-%d %H:%M"),
        )
    import_display.short_description = "Import"
    import_display.admin_order_field = "import_record__created_at"

    def transaction_display(self, obj):
        """Display transaction with link and key details."""
        return format_html(
            '<a href="/admin/banking/transaction/{}/change/">Transaction #{}</a><br>'
            '<span style="font-size: 12px; color: #6b7280;">{} | {} {}</span>',
            obj.transaction.id,
            obj.transaction.id,
            obj.transaction.date,
            obj.transaction.account.currency,
            format(obj.transaction.amount, '.2f'),
        )
    transaction_display.short_description = "Transaction"
    transaction_display.admin_order_field = "transaction__date"

    def action_display(self, obj):
        """Display whether transaction was created or updated."""
        if obj.was_created:
            return mark_safe(
                '<span style="background-color: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 3px; font-weight: 500;">✓ Created</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 3px; font-weight: 500;">⟲ Updated</span>'
            )
    action_display.short_description = "Action"
    action_display.admin_order_field = "was_created"

    def created_at_display(self, obj):
        """Display creation time."""
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_display.short_description = "Imported At"
    created_at_display.admin_order_field = "created_at"

    def transaction_details(self, obj):
        """Display detailed transaction information."""
        tx = obj.transaction
        return format_html(
            '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
            '<tr style="background-color: #f3f4f6;"><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Date</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;">{}</td></tr>'
            '<tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Amount</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;">{} {}</td></tr>'
            '<tr style="background-color: #f3f4f6;"><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Type</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;">{}</td></tr>'
            '<tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Reference</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;"><code>{}</code></td></tr>'
            '<tr style="background-color: #f3f4f6;"><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Description</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;">{}</td></tr>'
            '<tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Category</strong></td>'
            '<td style="padding: 8px; border: 1px solid #e5e7eb;">{}</td></tr>'
            '</table>',
            tx.date,
            tx.account.currency,
            format(tx.amount, '.2f'),
            tx.type,
            tx.reference or "-",
            tx.description or "-",
            tx.category.name if tx.category else "-",
        )
    transaction_details.short_description = "Transaction Information"

    def has_add_permission(self, request):
        """Prevent manual addition - only created by import process."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers."""
        return request.user.is_superuser


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ("title", "anomaly_type", "severity_badge", "anomaly_score", "user", "account", "is_dismissed", "created_at")
    list_filter = ("anomaly_type", "severity", "is_dismissed", "is_confirmed", "created_at")
    search_fields = ("title", "description", "user__username", "account__name")
    readonly_fields = ("created_at", "updated_at", "anomaly_score", "expected_value", "actual_value", "deviation_percent", "context_data")
    fieldsets = (
        ("Anomaly Information", {
            "fields": ("anomaly_type", "severity", "title", "description", "reason")
        }),
        ("Detection Details", {
            "fields": ("user", "account", "transaction", "recurring")
        }),
        ("Scoring", {
            "fields": ("anomaly_score", "expected_value", "actual_value", "deviation_percent")
        }),
        ("Analysis", {
            "fields": ("context_data",),
            "classes": ("collapse",)
        }),
        ("User Feedback", {
            "fields": ("is_dismissed", "dismissed_by_user", "dismissed_at", "is_false_positive", "is_confirmed")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    date_hierarchy = "created_at"
    actions = ["mark_dismissed", "mark_false_positive"]

    def severity_badge(self, obj):
        """Display severity with color coding."""
        colors = {
            'critical': '#dc2626',
            'warning': '#f59e0b',
            'info': '#3b82f6',
        }
        color = colors.get(obj.severity, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: 500;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = "Severity"
    severity_badge.admin_order_field = "severity"

    def mark_dismissed(self, request, queryset):
        """Mark selected anomalies as dismissed."""
        count = queryset.update(is_dismissed=True, dismissed_by_user=True)
        self.message_user(request, f"{count} anomalies marked as dismissed.", messages.SUCCESS)
    mark_dismissed.short_description = "Mark selected anomalies as dismissed"

    def mark_false_positive(self, request, queryset):
        """Mark selected anomalies as false positive."""
        count = queryset.update(is_false_positive=True, is_dismissed=True)
        self.message_user(request, f"{count} anomalies marked as false positive.", messages.SUCCESS)
    mark_false_positive.short_description = "Mark selected anomalies as false positive"

    def has_add_permission(self, request):
        """Prevent manual addition - only created by detection system."""
        return False


@admin.register(AnomalyNotification)
class AnomalyNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "anomaly_title", "is_read", "is_notified_via_email", "is_notified_via_push", "created_at")
    list_filter = ("is_read", "is_notified_via_email", "is_notified_via_push", "created_at")
    search_fields = ("user__username", "anomaly__title")
    readonly_fields = ("created_at", "anomaly")
    fieldsets = (
        ("Notification", {
            "fields": ("user", "anomaly")
        }),
        ("Delivery Status", {
            "fields": ("is_read", "is_notified_via_email", "is_notified_via_push")
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    date_hierarchy = "created_at"

    def anomaly_title(self, obj):
        """Display anomaly title."""
        return obj.anomaly.title
    anomaly_title.short_description = "Anomaly"
    anomaly_title.admin_order_field = "anomaly__title"

    def has_add_permission(self, request):
        """Prevent manual addition."""
        return False


@admin.register(UserAnomalyPreferences)
class UserAnomalyPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "anomaly_detection_enabled", "sensitivity", "notify_on_critical", "notify_on_warning")
    list_filter = ("anomaly_detection_enabled", "sensitivity", "notify_on_critical", "notify_on_warning", "email_notifications", "push_notifications")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("User", {
            "fields": ("user",)
        }),
        ("Global Settings", {
            "fields": ("anomaly_detection_enabled", "sensitivity")
        }),
        ("Notification Preferences", {
            "fields": ("notify_on_critical", "notify_on_warning", "notify_on_info", "email_notifications", "push_notifications")
        }),
        ("Detection Configuration", {
            "fields": ("enabled_types", "amount_deviation_percent", "spending_spike_multiplier", "days_before_inactive")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

