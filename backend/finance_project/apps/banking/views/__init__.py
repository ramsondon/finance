from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from ..models import BankAccount, Transaction, Category, Rule
from ..serializers import BankAccountSerializer, TransactionSerializer, CategorySerializer, RuleSerializer
from ..services.csv_importer import CSVImporter
from ..services.json_importer import JSONImporter
from ..tasks import import_transactions_task, apply_rules_task

from .recurring import RecurringTransactionViewSet  # Import recurring transaction views


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id
        if hasattr(obj, "account_id"):
            return obj.account.user_id == request.user.id
        return False


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DefaultPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = {"date": ["gte", "lte"], "amount": ["gte", "lte"], "category": ["exact", "isnull"], "type": ["exact"]}
    ordering_fields = ["date", "amount"]
    search_fields = ["description"]
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = Transaction.objects.filter(account__user=self.request.user).select_related("account", "category")
        # Optional filter by specific account via query param
        account_id = self.request.query_params.get("account")
        if account_id:
            try:
                qs = qs.filter(account_id=int(account_id))
            except (TypeError, ValueError):
                pass
        return qs

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        account_id = request.data.get("account")
        file = request.FILES.get("file")
        if not account_id or not file:
            return Response({"code": "bad_request", "message": "account and file required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"code": "not_found", "message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        importer = CSVImporter()
        parsed, errors = importer.parse(file)
        rows = [
            {
                "date": r.date.strftime("%Y-%m-%d"),
                "amount": str(r.amount),
                "reference": r.description,  # Use description as reference
                "description": r.description,
                "type": r.type,
                "category_name": r.category_name,
            }
            for r in parsed
        ]
        import_transactions_task.delay(account.id, rows)
        return Response({"queued": len(rows), "errors": errors})

    @action(detail=False, methods=["post"], url_path="apply-rules")
    def apply_rules(self, request):
        apply_rules_task.delay(request.user.id)
        return Response({"status": "queued"})

    @action(detail=False, methods=["post"], url_path="import-json")
    def import_json(self, request):
        account_id = request.data.get("account")
        payload = request.data.get("transactions") or request.data
        if not account_id or payload is None:
            return Response({"code": "bad_request", "message": "account and transactions required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"code": "not_found", "message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        importer = JSONImporter()
        parsed, errors = importer.parse(payload)
        rows = [
            {
                "date": r.date.strftime("%Y-%m-%d"),
                "amount": str(r.amount),
                "reference": r.description,  # Use description as reference
                "description": r.description,
                "type": r.type,
                "category_name": r.category_name,
            }
            for r in parsed
        ]
        if rows:
            import_transactions_task.delay(account.id, rows)
        return Response({"queued": len(rows), "errors": errors})

    @action(detail=False, methods=["post"], url_path="import-transactions")
    def import_transactions_generic(self, request):
        """Generic import endpoint for CSV or JSON files with flexible field mapping."""
        account_id = request.data.get("account")
        file = request.FILES.get("file")
        field_mappings = request.data.get("field_mappings")  # Optional: {csv_col: tx_property}

        if not account_id or not file:
            return Response(
                {"code": "bad_request", "message": "account and file required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response(
                {"code": "not_found", "message": "Account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Determine file type by extension
        file_extension = file.name.split('.')[-1].lower()

        try:
            if file_extension == 'csv':
                parsed, errors = self._import_csv(file, field_mappings)
            elif file_extension == 'json':
                parsed, errors = self._import_json(file, field_mappings)
            else:
                return Response(
                    {"code": "bad_format", "message": "File must be CSV or JSON"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"code": "parse_error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert parsed rows to API payload
        rows = self._convert_rows_to_payload(parsed, account)

        if rows:
            import_transactions_task.delay(account.id, rows)

        return Response({
            "queued": len(rows),
            "errors": errors,
            "file_type": file_extension
        })

    def _import_csv(self, file, field_mappings):
        """Import CSV file."""
        importer = CSVImporter(field_mappings=field_mappings)
        return importer.parse(file)

    def _import_json(self, file, field_mappings):
        """Import JSON file."""
        import json
        try:
            content = json.loads(file.read().decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

        importer = JSONImporter(field_mappings=field_mappings)
        return importer.parse(content)

    def _convert_rows_to_payload(self, parsed_rows, account):
        """Convert parsed rows to transaction payload."""
        rows = []
        for r in parsed_rows:
            row = {
                "date": r.date.strftime("%Y-%m-%d"),
                "amount": str(r.amount),
                "reference": r.description,  # Use parsed description as reference for basic importers
                "description": r.description,
                "type": r.type,
                "category_name": r.category_name,
            }

            # Add extra fields if present
            if hasattr(r, 'extra_fields') and r.extra_fields:
                # If reference is in extra_fields, use it instead
                if 'reference' in r.extra_fields:
                    row['reference'] = r.extra_fields['reference']
                row.update(r.extra_fields)

            rows.append(row)

        return rows


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RuleViewSet(viewsets.ModelViewSet):
    serializer_class = RuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Rule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(["GET"])  # Public or authenticated? Keep authenticated for now
@permission_classes([permissions.IsAuthenticated])
def currencies_view(request):
    """Return supported currency codes from settings or defaults."""
    default_list = ["EUR", "USD", "GBP", "CHF", "JPY", "AUD", "CAD", "SEK", "NOK"]
    configured = getattr(settings, "SUPPORTED_CURRENCIES", None)
    currencies = configured if isinstance(configured, (list, tuple)) and configured else default_list
    return Response({"currencies": list(currencies)})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def available_fields_view(request):
    """Return available fields for import mapping."""
    from .services.field_mapper import FieldMappingRegistry
    return Response({
        "fields": FieldMappingRegistry.list_fields(),
        "display_names": FieldMappingRegistry.get_display_names()
    })
