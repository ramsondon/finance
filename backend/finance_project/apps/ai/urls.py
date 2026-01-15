from django.urls import path
from .views import InsightsView, GenerateCategoriesView, CategorySuggestionsView, TaskStatusView

urlpatterns = [
    path("insights", InsightsView.as_view(), name="ai-insights"),
    path("generate-categories", GenerateCategoriesView.as_view(), name="ai-generate-categories"),
    path("task-status/<str:task_id>", TaskStatusView.as_view(), name="ai-task-status"),
    path("category-suggestions", CategorySuggestionsView.as_view(), name="ai-category-suggestions"),
]

