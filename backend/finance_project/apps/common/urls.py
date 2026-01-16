from django.urls import path
from .views import TaskStatusView

urlpatterns = [
    path("task-status/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
]

