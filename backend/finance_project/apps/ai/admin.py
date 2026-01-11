from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from .services.category_generator import CategoryGeneratorService
from .services.insights_service import ProviderRegistry

User = get_user_model()

# Unregister the default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdminExtended(UserAdmin):
    """
    Extended User admin with AI-powered category generation.
    """
    # Extend the default list_display with our custom fields
    list_display = UserAdmin.list_display + ('category_count', 'transaction_count')

    # Add our custom actions to the existing actions
    actions = UserAdmin.actions + ('generate_categories_sync', 'generate_categories_async')

    def category_count(self, obj):
        """Display number of categories for this user."""
        from ..banking.models import Category
        count = Category.objects.filter(user=obj).count()
        return format_html(
            '<span style="background-color: #e8f4f8; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    category_count.short_description = 'Categories'

    def transaction_count(self, obj):
        """Display number of transactions for this user."""
        from ..banking.models import Transaction
        count = Transaction.objects.filter(account__user=obj).count()
        return format_html(
            '<span style="background-color: #fef3c7; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    transaction_count.short_description = 'Transactions'

    def generate_categories_sync(self, request, queryset):
        """
        Synchronously generate categories for selected users.
        Use for quick preview and immediate results.
        """
        # Get active AI provider (optional)
        provider = None
        try:
            provider = ProviderRegistry.get_active()
        except Exception:
            pass

        service = CategoryGeneratorService(provider=provider)

        total_suggestions = 0
        total_created = 0

        for user in queryset:
            # Analyze transactions
            suggestions = service.analyze_transactions(user.id)
            total_suggestions += len(suggestions)

            # Auto-create high confidence categories
            created = service.create_categories(user.id, suggestions, auto_approve=True)
            total_created += len([c for c in created if c.get('created', False)])

        self.message_user(
            request,
            f"✓ Generated {total_suggestions} suggestions and created {total_created} categories for {queryset.count()} user(s).",
            level=messages.SUCCESS
        )
    generate_categories_sync.short_description = "🤖 Generate categories (sync)"

    def generate_categories_async(self, request, queryset):
        """
        Asynchronously generate categories for selected users using Celery.
        Use for large datasets or multiple users.
        """
        from .tasks import generate_categories_task

        task_ids = []
        for user in queryset:
            task = generate_categories_task.delay(user.id, auto_approve=True)
            task_ids.append(task.id)

        self.message_user(
            request,
            f"✓ Started {len(task_ids)} background tasks to generate categories for {queryset.count()} user(s). Check Celery logs for progress.",
            level=messages.SUCCESS
        )
    generate_categories_async.short_description = "🚀 Generate categories (async)"


# Admin action to generate categories from the banking app
class CategoryGenerationMixin:
    """
    Mixin to add category generation actions to any admin.
    """

    def generate_categories_for_user(self, request, user_id):
        """Helper method to generate categories for a specific user."""
        from .services.category_generator import CategoryGeneratorService
        from .services.insights_service import ProviderRegistry

        # Get active AI provider (optional)
        provider = None
        try:
            provider = ProviderRegistry.get_active()
        except Exception:
            pass

        service = CategoryGeneratorService(provider=provider)
        suggestions = service.analyze_transactions(user_id)
        created = service.create_categories(user_id, suggestions, auto_approve=True)

        return suggestions, created

