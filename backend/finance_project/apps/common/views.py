"""
Generic, reusable views for shared functionality across apps.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class TaskStatusView(APIView):
    """
    Generic Celery task status polling view - reusable across all apps.

    GET /api/task-status/<task_id>/

    Check the status of any background Celery task (category generation,
    rule generation, file imports, etc.).

    Can be imported and used by any app that needs async task polling.
    Supports frontend polling (recommended: every 1 second, max 5 minutes).

    Returns:
        {
            "task_id": "abc-123-def",
            "status": "PENDING" | "PROGRESS" | "SUCCESS" | "FAILURE",
            "result": {...},      // Only if status is SUCCESS
            "error": "..."        // Only if status is FAILURE
        }

    Example usage:
        1. Backend starts async task: task = some_task.delay(user_id)
        2. Returns task_id to frontend via 202 ACCEPTED
        3. Frontend polls GET /api/task-status/{task_id}/ every 1 second
        4. When status is SUCCESS or FAILURE, frontend stops polling
        5. Frontend shows result or error to user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        from celery.result import AsyncResult

        try:
            task_result = AsyncResult(task_id)

            response_data = {
                'task_id': task_id,
                'status': task_result.status,
            }

            if task_result.status == 'SUCCESS':
                response_data['result'] = task_result.result
            elif task_result.status == 'FAILURE':
                response_data['error'] = str(task_result.info)

            return Response(response_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

