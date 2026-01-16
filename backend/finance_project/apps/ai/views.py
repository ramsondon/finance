from datetime import timedelta

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import InsightsRequestSerializer
from .services.insights_service import ProviderRegistry
from .services.providers.mock_provider import provider as mock_provider
from .services.providers.ollama_provider import provider as ollama_provider
from .tasks import generate_categories_task
from ..banking.models import Transaction

# Register providers at import time
ProviderRegistry.register(mock_provider)
ProviderRegistry.register(ollama_provider)


class InsightsView(APIView):
    """
    POST /api/ai/insights/

    Generate AI-powered financial insights based on user's transaction data.
    Uses user's language preference from UserProfile for localized insights.

    Body (optional):
        {
            "timeframe": "30d",  // "7d", "30d", "90d", "365d" (default: "30d")
            "categories": []     // Optional category filter
        }

    Returns:
        {
            "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
            "analysis": "Detailed financial analysis...",
            "language": "de"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ..accounts.models import UserProfile

        req = InsightsRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        # Get user's language preference from UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            language = profile.get_language()
        except UserProfile.DoesNotExist:
            language = 'en'  # Fallback to English if no profile

        provider = ProviderRegistry.get_active()
        context = req.validated_data.copy()
        default_timeframe = 30
        timeframe = context.get('timeframe', f'{default_timeframe}d')

        # timeframe = "7d", "30d", "90d", "365d"
        # convert the timeframe to a real date from now

        transactions = Transaction.objects.filter(account__user=request.user)
        now = timezone.now()
        if timeframe:
            if timeframe.endswith('d'):
                days = int(timeframe[:-1])
                start_date = now - timedelta(days=days)
            elif timeframe.endswith('m'):
                months = int(timeframe[:-1])
                start_date = now - timedelta(days=30 * months)
            elif timeframe.endswith('y'):
                years = int(timeframe[:-1])
                start_date = now - timedelta(days=365 * years)
            else:
                start_date = now - timedelta(days=default_timeframe)  # default to 30 days
        else:
            start_date = now - timedelta(days=default_timeframe)  # default to 30 days
        transactions = transactions.filter(date__gte=start_date)
        context.update({
            'timeframe': timeframe,
            'transactions': [{
                'id': t.id,
                'date': t.date.isoformat(),
                'amount': float(t.amount),
                'description': t.description,
                'category': t.category.name if t.category else None,
            } for t in transactions]
        })

        # Add more timeframe parsing as needed

        data = provider.generate_insights(request.user.id, context, language=language)
        data['language'] = language
        return Response(data)


class GenerateCategoriesView(APIView):
    """
    POST /api/ai/generate-categories/

    Analyzes user's transactions and generates category suggestions using AI.
    Automatically creates categories with confidence > 0.7 using user's language preference.

    Language is retrieved from UserProfile.preferences (server-side source of truth).

    Body (optional):
        {
            "auto_approve": true  // If true, automatically creates categories with confidence > 0.7 (default: true)
        }

    Returns:
        {
            "message": "Category generation started",
            "task_id": "abc-123-def",
            "user_id": 1,
            "language": "de"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ..accounts.models import UserProfile

        auto_approve = request.data.get('auto_approve', True)

        # Get user's language from UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            language = profile.get_language()
        except UserProfile.DoesNotExist:
            language = 'en'  # Fallback to English if no profile

        # Trigger async task with language and auto_approve
        task = generate_categories_task.delay(request.user.id, auto_approve, language)

        return Response({
            'message': 'Category generation started in background',
            'task_id': task.id,
            'user_id': request.user.id,
            'language': language,
            'auto_approve': auto_approve
        }, status=status.HTTP_202_ACCEPTED)



class CategorySuggestionsView(APIView):
    """
    GET /api/ai/category-suggestions/

    Get category suggestions without creating them (synchronous).
    Uses user's language preference from UserProfile.
    Useful for preview before creating.

    Returns:
        {
            "suggestions": [
                {
                    "name": "Lebensmittel" (or "Groceries"),
                    "color": "#22c55e",
                    "confidence": 0.85,
                    "transaction_count": 45,
                    "keywords": ["supermarket", "grocery"]
                }
            ],
            "language": "de"
        }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services.category_generator import CategoryGeneratorService
        from ..accounts.models import UserProfile

        # Get user's language from UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            language = profile.get_language()
        except UserProfile.DoesNotExist:
            language = 'en'  # Fallback to English if no profile

        # Get active AI provider (optional)
        provider = None
        try:
            provider = ProviderRegistry.get_active()
        except Exception:
            pass

        service = CategoryGeneratorService(provider=provider)
        suggestions = service.analyze_transactions(request.user.id, language=language)

        return Response({
            'suggestions': suggestions,
            'count': len(suggestions),
            'language': language
        })

    def post(self, request):
        """
        POST /api/ai/category-suggestions/

        Create categories from suggestions.

        Body:
            {
                "suggestions": [
                    {"name": "Lebensmittel", "color": "#22c55e"},
                    {"name": "Verkehrsmittel", "color": "#3b82f6"}
                ]
            }
        """
        from .services.category_generator import CategoryGeneratorService

        suggestions = request.data.get('suggestions', [])

        if not suggestions:
            return Response(
                {'error': 'No suggestions provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = CategoryGeneratorService()
        created = service.create_categories(request.user.id, suggestions, auto_approve=True)

        return Response({
            'created': created,
            'count': len(created)
        })


