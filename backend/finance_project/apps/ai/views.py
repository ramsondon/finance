from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import InsightsRequestSerializer
from .services.insights_service import ProviderRegistry
from .services.providers.mock_provider import provider as mock_provider
from .services.providers.ollama_provider import provider as ollama_provider
from .tasks import generate_categories_task

# Register providers at import time
ProviderRegistry.register(mock_provider)
ProviderRegistry.register(ollama_provider)


class InsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        req = InsightsRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        provider = ProviderRegistry.get_active()
        data = provider.generate_insights(request.user.id, req.validated_data)
        return Response(data)


class GenerateCategoriesView(APIView):
    """
    POST /api/ai/generate-categories/

    Analyzes user's transactions and generates category suggestions using AI.

    Body (optional):
        {
            "auto_approve": false  // If true, automatically creates categories with confidence > 0.7
        }

    Returns:
        {
            "message": "Category generation started",
            "task_id": "abc-123-def",
            "user_id": 1
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auto_approve = request.data.get('auto_approve', False)

        # Trigger async task
        task = generate_categories_task.delay(request.user.id, auto_approve)

        return Response({
            'message': 'Category generation started in background',
            'task_id': task.id,
            'user_id': request.user.id,
            'auto_approve': auto_approve
        }, status=status.HTTP_202_ACCEPTED)


class CategorySuggestionsView(APIView):
    """
    GET /api/ai/category-suggestions/

    Get category suggestions without creating them (synchronous).
    Useful for preview before creating.

    Returns:
        {
            "suggestions": [
                {
                    "name": "Groceries",
                    "color": "#22c55e",
                    "confidence": 0.85,
                    "transaction_count": 45,
                    "keywords": ["supermarket", "grocery"]
                }
            ]
        }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services.category_generator import CategoryGeneratorService

        # Get active AI provider (optional)
        provider = None
        try:
            provider = ProviderRegistry.get_active()
        except Exception:
            pass

        service = CategoryGeneratorService(provider=provider)
        suggestions = service.analyze_transactions(request.user.id)

        return Response({
            'suggestions': suggestions,
            'count': len(suggestions)
        })

    def post(self, request):
        """
        POST /api/ai/category-suggestions/

        Create categories from suggestions.

        Body:
            {
                "suggestions": [
                    {"name": "Groceries", "color": "#22c55e"},
                    {"name": "Transport", "color": "#3b82f6"}
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


