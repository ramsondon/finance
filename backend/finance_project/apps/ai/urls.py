from django.urls import path
from .views import InsightsView, GenerateCategoriesView, CategorySuggestionsView

urlpatterns = [
    path("insights", InsightsView.as_view(), name="ai-insights"),
    path("generate-categories", GenerateCategoriesView.as_view(), name="ai-generate-categories"),
    path("category-suggestions", CategorySuggestionsView.as_view(), name="ai-category-suggestions"),
]

