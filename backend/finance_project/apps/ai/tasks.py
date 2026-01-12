"""
Celery tasks for AI-powered features.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_categories_task(self, user_id: int, auto_approve: bool = False, language: str = 'en'):
    """
    Background task to generate categories from user's transaction patterns using AI.

    Uses Ollama (GEMMA3 model) to analyze transaction descriptions and types
    to intelligently suggest relevant categories.

    Args:
        user_id: User ID to generate categories for
        auto_approve: If True, automatically create categories with confidence > 0.7
        language: Language code ('en', 'de', etc.) for AI-generated category names

    Returns:
        dict with suggestions and created categories
    """
    from .services.category_generator import CategoryGeneratorService
    from .services.providers.ollama_provider import OllamaProvider
    import os

    try:
        logger.info(f"Starting AI-powered category generation for user_id={user_id}, auto_approve={auto_approve}, language={language}")

        # Initialize Ollama provider with GEMMA3 model
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

        # Create categories if auto-approve is enabled
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

