from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from ..models import BankAccount, Transaction, Category, Rule
from ..serializers import BankAccountSerializer, TransactionSerializer, CategorySerializer, RuleSerializer
from ..services.csv_importer import CSVImporter
from ..services.json_importer import JSONImporter
from ..services.field_mapper import FieldMappingRegistry
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

    @action(detail=False, methods=["post"], url_path="preview-file")
    def preview_file(self, request):
        """Preview file headers/fields for mapping before import."""
        import csv
        import json
        import io

        file = request.FILES.get("file")
        account_id = request.data.get("account")
        if not file:
            return Response(
                {"code": "bad_request", "message": "file required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_extension = file.name.split('.')[-1].lower()
        file_fields = []
        sample_data = []

        def flatten_dict(d, parent_key='', sep='.'):
            """Flatten nested dict with dot notation keys."""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        def extract_keys_recursive(d, parent_key='', sep='.'):
            """Extract all keys from nested dict with dot notation."""
            keys = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    keys.extend(extract_keys_recursive(v, new_key, sep=sep))
                else:
                    keys.append(new_key)
            return keys

        try:
            if file_extension == 'csv':
                # Read CSV headers
                content = file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
                file_fields = reader.fieldnames or []
                # Get first 3 rows as sample
                for i, row in enumerate(reader):
                    if i >= 3:
                        break
                    sample_data.append(row)

            elif file_extension == 'json':
                # Read JSON and extract field names from first object with dot notation
                content = json.loads(file.read().decode('utf-8'))
                if isinstance(content, list) and len(content) > 0:
                    # Get all unique keys from first few objects (flattened)
                    for i, item in enumerate(content[:5]):
                        if isinstance(item, dict):
                            for key in extract_keys_recursive(item):
                                if key not in file_fields:
                                    file_fields.append(key)
                    # Get first 3 items as sample (flattened)
                    sample_data = [flatten_dict(item) if isinstance(item, dict) else item for item in content[:3]]
                elif isinstance(content, dict):
                    file_fields = extract_keys_recursive(content)
                    sample_data = [flatten_dict(content)]
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

        # Get available transaction fields with metadata
        available_fields = []
        for name, mapping in FieldMappingRegistry.AVAILABLE_FIELDS.items():
            available_fields.append({
                "name": name,
                "target_property": mapping.target_property,
                "data_type": mapping.data_type,
                "required": mapping.required,
            })

        # Get saved mappings for this account and file type
        saved_mappings = {}
        if account_id:
            try:
                account = BankAccount.objects.get(id=account_id, user=request.user)
                import_settings = account.meta.get('import_settings', {}) if account.meta else {}
                saved_mappings = import_settings.get(f'mappings_{file_extension}', {})
            except BankAccount.DoesNotExist:
                pass

        return Response({
            "file_type": file_extension,
            "file_fields": file_fields,
            "sample_data": sample_data,
            "transaction_fields": available_fields,
            "saved_mappings": saved_mappings,
        })

    @action(detail=False, methods=["post"], url_path="import-transactions")
    def import_transactions_generic(self, request):
        """Generic import endpoint for CSV or JSON files with flexible field mapping."""
        import json as json_module

        account_id = request.data.get("account")
        file = request.FILES.get("file")
        field_mappings_raw = request.data.get("field_mappings")  # Optional: {csv_col: tx_property}

        # Parse field_mappings if it's a JSON string (from FormData)
        field_mappings = None
        if field_mappings_raw:
            if isinstance(field_mappings_raw, str):
                try:
                    field_mappings = json_module.loads(field_mappings_raw)
                except json_module.JSONDecodeError:
                    field_mappings = None
            elif isinstance(field_mappings_raw, dict):
                field_mappings = field_mappings_raw

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

        # Save field mappings for future imports
        if field_mappings:
            if not account.meta:
                account.meta = {}
            import_settings = account.meta.get('import_settings', {})
            import_settings[f'mappings_{file_extension}'] = field_mappings
            account.meta['import_settings'] = import_settings
            account.save(update_fields=['meta'])

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
                if 'reference' in r.extra_fields and r.extra_fields['reference']:
                    row['reference'] = r.extra_fields['reference']
                    # Derive description from reference if not explicitly mapped
                    if 'description' not in r.extra_fields or not r.extra_fields.get('description'):
                        row['description'] = r.extra_fields['reference']
                row.update(r.extra_fields)

            # Ensure description is always set (fallback to reference)
            if not row.get('description') and row.get('reference'):
                row['description'] = row['reference']

            rows.append(row)

        return rows


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'color']
    ordering = ['name']  # Default ordering by name

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
    from ..services.field_mapper import FieldMappingRegistry
    return Response({
        "fields": FieldMappingRegistry.list_fields(),
        "display_names": FieldMappingRegistry.get_display_names()
    })


class GenerateRulesView(APIView):
    """
    POST /api/banking/rules/generate/

    Trigger background task to generate categorization rules from existing
    AI-created categories by analyzing transaction patterns.

    This endpoint:
    1. Analyzes all categorized transactions grouped by category
    2. Detects common patterns (keywords, amount ranges, types)
    3. Creates rules with confidence > RULE_GENERATION_CONFIDENCE_THRESHOLD
    4. Returns task_id for frontend polling

    Returns (202 ACCEPTED):
        {
            "message": "Rule generation started",
            "task_id": "abc-123-def"
        }

    Requires:
    - User to have at least RULE_GENERATION_MIN_TRANSACTIONS categorized transactions
    - AI-created categories to exist

    Error scenarios:
    - Insufficient transaction data
    - No categories exist
    - Task creation failure
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from ..tasks import generate_rules_from_categories_task
        from ...accounts.models import UserProfile

        # Get user's language preference
        try:
            profile = UserProfile.objects.get(user=request.user)
            language = profile.get_language()
        except UserProfile.DoesNotExist:
            language = 'en'

        # Trigger async task
        task = generate_rules_from_categories_task.delay(request.user.id, language)

        return Response({
            'message': 'Rule generation started in background',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)


