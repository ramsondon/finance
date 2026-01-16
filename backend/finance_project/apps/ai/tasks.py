"""
Celery tasks for AI-powered features.
"""
from celery import shared_task
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_insights_task(self, user_id: int, timeframe: str = '30d', language: str = None, account_id: int = None):
    """
    Background task to generate AI-powered financial insights based on user's transaction data.

    Uses configured AI provider (Ollama or Mock) to analyze transactions and provide
    personalized financial advice in the user's preferred language.

    Args:
        user_id: User ID to generate insights for
        timeframe: Time period for analysis ("7d", "30d", "90d", "365d")
        language: Language code ('en', 'de', etc.). If None, retrieves from UserProfile
        account_id: Optional specific bank account ID. If None, analyzes all accounts.

    Returns:
        dict with suggestions, analysis, and metadata
    """
    from .services.insights_service import ProviderRegistry
    from ..accounts.models import UserProfile
    from ..banking.models import Transaction, BankAccount

    try:
        logger.info(f"Starting AI insights generation for user_id={user_id}, timeframe={timeframe}, account_id={account_id}")

        # Retrieve language from UserProfile if not provided
        if language is None:
            try:
                profile = UserProfile.objects.get(user_id=user_id)
                language = profile.get_language()
                logger.info(f"Retrieved language from UserProfile: {language}")
            except UserProfile.DoesNotExist:
                language = 'en'
                logger.warning(f"UserProfile not found for user_id={user_id}, defaulting to English")

        logger.info(f"Using language: {language}")

        # Parse timeframe and get transactions
        default_timeframe = 30
        if timeframe.endswith('d'):
            days = int(timeframe[:-1])
            start_date = timezone.now() - timedelta(days=days)
        elif timeframe.endswith('m'):
            months = int(timeframe[:-1])
            start_date = timezone.now() - timedelta(days=30 * months)
        elif timeframe.endswith('y'):
            years = int(timeframe[:-1])
            start_date = timezone.now() - timedelta(days=365 * years)
        else:
            start_date = timezone.now() - timedelta(days=default_timeframe)

        # Get transactions for the user
        # Filter by account_id if provided, otherwise get all user's accounts
        if account_id:
            # Specific account requested - verify it belongs to user
            try:
                account = BankAccount.objects.get(id=account_id, user_id=user_id)
                transactions = Transaction.objects.filter(
                    account_id=account_id,
                    date__gte=start_date,
                    type__in=[Transaction.INCOME, Transaction.EXPENSE]  # Exclude transfers
                )
                logger.info(f"Filtering transactions for account {account_id}: {account.name}")
            except BankAccount.DoesNotExist:
                logger.error(f"Account {account_id} not found or does not belong to user {user_id}")
                return {
                    'user_id': user_id,
                    'language': language,
                    'error': 'Account not found',
                    'success': False
                }
        else:
            # All accounts - get all transactions for user
            transactions = Transaction.objects.filter(
                account__user_id=user_id,
                date__gte=start_date
            )
            logger.info(f"Analyzing all accounts for user_id={user_id}")

        logger.info(f"Found {transactions.count()} transactions for analysis")

        # Prepare context for AI provider
        context = {
            'timeframe': timeframe,
            'transactions': [{
                'id': t.id,
                'date': t.date.isoformat(),
                'amount': float(t.amount),
                'description': t.description,
                'category': t.category.name if t.category else None,
            } for t in transactions]
        }

        # Get active AI provider and generate insights
        provider = ProviderRegistry.get_active()
        logger.info(f"Using AI provider: {provider.name}")

        result = provider.generate_insights(user_id, context, language=language)

        # Enrich result with metadata
        result.update({
            'user_id': user_id,
            'language': language,
            'timeframe': timeframe,
            'transaction_count': transactions.count(),
            'ai_provider': provider.name,
            'success': True
        })

        # Include account_id if specific account was used
        if account_id:
            result['account_id'] = account_id

        logger.info(f"Successfully generated insights for user_id={user_id}")
        return result

    except Exception as exc:
        logger.error(f"Error generating insights for user_id={user_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def generate_categories_task(self, user_id: int, auto_approve: bool = True, language: str = None):
    """
    Background task to generate categories from user's transaction patterns using AI.

    Uses Ollama (GEMMA2 model) to analyze transaction descriptions and types
    to intelligently suggest relevant categories.

    Auto-creates categories with confidence > 0.7 by default, allowing users to
    delete or edit them afterwards.

    Args:
        user_id: User ID to generate categories for
        auto_approve: If True (default), automatically create categories with confidence > 0.7
        language: Language code ('en', 'de', etc.). If None, retrieves from UserProfile

    Returns:
        dict with suggestions and created categories
    """
    from .services.category_generator import CategoryGeneratorService
    from .services.providers.ollama_provider import OllamaProvider
    from ..accounts.models import UserProfile
    import os

    try:
        logger.info(f"Starting AI-powered category generation for user_id={user_id}, auto_approve={auto_approve}")

        # Retrieve language from UserProfile if not provided
        if language is None:
            try:
                profile = UserProfile.objects.get(user_id=user_id)
                language = profile.get_language()
                logger.info(f"Retrieved language from UserProfile: {language}")
            except UserProfile.DoesNotExist:
                language = 'en'
                logger.warning(f"UserProfile not found for user_id={user_id}, defaulting to English")

        logger.info(f"Using language: {language}")

        # Initialize Ollama provider with GEMMA2 model
        ollama_host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
        ollama_model = os.environ.get("OLLAMA_MODEL", "gemma2")

        logger.info(f"Using Ollama at {ollama_host} with model {ollama_model}")

        provider = OllamaProvider(host=ollama_host, model=ollama_model)

        # Initialize service with AI provider
        service = CategoryGeneratorService(provider=provider)

        # Analyze transactions with language preference (will use both pattern-based and AI enhancement)
        suggestions = service.analyze_transactions(user_id, language=language)
        logger.info(f"Generated {len(suggestions)} category suggestions for user_id={user_id}")

        # Log sample suggestions
        if suggestions:
            sample_names = [s['name'] for s in suggestions[:5]]
            logger.info(f"Sample suggestions: {', '.join(sample_names)}")

        # Create categories if auto-approve is enabled (high confidence > 0.7)
        created = []
        if auto_approve:
            created = service.create_categories(user_id, suggestions, auto_approve=True)
            created_count = len([c for c in created if c.get('created', False)])
            logger.info(f"Auto-created {created_count} categories for user_id={user_id}")

        return {
            'user_id': user_id,
            'language': language,
            'suggestions': suggestions,
            'created': created,
            'auto_approved': auto_approve,
            'ai_provider': f"{ollama_model}@{ollama_host}",
            'success': True
        }

    except Exception as exc:
        logger.error(f"Error generating categories for user_id={user_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

