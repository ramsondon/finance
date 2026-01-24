"""
Field mapper for flexible CSV/JSON transaction import.
Allows users to map source fields to transaction properties.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class FieldMapping:
    """Defines mapping from source field to transaction property."""
    source_field: str  # Field name in CSV/JSON (e.g., "booking" or "column_1")
    target_property: str  # Transaction model property (e.g., "booking_date")
    data_type: str = "string"  # string, date, decimal, integer
    date_format: Optional[str] = None  # For date parsing (e.g., "%Y-%m-%d")
    required: bool = False


class FieldMappingRegistry:
    """Registry of available transaction fields for mapping."""

    AVAILABLE_FIELDS = {
        # Core fields (required)
        "date": FieldMapping("date", "date", "date", required=True),
        "amount": FieldMapping("amount", "amount", "decimal", required=True),
        # Reference is optional - can be derived from fallback fields
        "reference": FieldMapping("reference", "reference", "string", required=False),

        # Optional fields (type is auto-derived from amount, description from reference)
        "description": FieldMapping("description", "description", "string"),
        "booking_type": FieldMapping("bookingTypeTranslation", "booking_type", "string"),

        # Partner/Counterparty (optional)
        "partner_name": FieldMapping("partnerName", "partner_name", "string"),
        "partner_iban": FieldMapping("partnerIban", "partner_iban", "string"),
        "partner_account": FieldMapping("partnerAccount", "partner_account_number", "string"),
        "partner_bank_code": FieldMapping("bankCode", "partner_bank_code", "string"),

        # Merchant (optional)
        "merchant_name": FieldMapping("merchantName", "merchant_name", "string"),

        # Owner/Sender (optional)
        "owner_account": FieldMapping("ownerAccountNumber", "owner_account", "string"),
        "owner_name": FieldMapping("ownerAccountTitle", "owner_name", "string"),

        # Dates
        "booking_date": FieldMapping("bookingDate", "booking_date", "date"),
        "valuation_date": FieldMapping("valuation", "valuation_date", "date"),

        # References
        "reference_number": FieldMapping("referenceNumber", "reference_number", "string"),

        # Card details
        "virtual_card_number": FieldMapping("virtualCardNumber", "virtual_card_number", "string"),
        "virtual_card_device": FieldMapping("virtualCardDeviceName", "virtual_card_device", "string"),
        "payment_app": FieldMapping("virtualCardMobilePaymentApplicationName", "payment_app", "string"),

        # Payment info
        "payment_method": FieldMapping("paymentMethod", "payment_method", "string"),
        "card_brand": FieldMapping("cardBrand", "card_brand", "string"),

        # Fees and rates
        "exchange_rate": FieldMapping("exchangeRateValue", "exchange_rate", "decimal"),
        "transaction_fee": FieldMapping("transactionFee", "transaction_fee", "decimal"),

        # SEPA
        "sepa_scheme": FieldMapping("sepaScheme", "sepa_scheme", "string"),
    }

    @classmethod
    def get_field(cls, field_name: str) -> Optional[FieldMapping]:
        """Get field mapping by name."""
        return cls.AVAILABLE_FIELDS.get(field_name)

    @classmethod
    def list_fields(cls) -> List[str]:
        """List all available field names."""
        return list(cls.AVAILABLE_FIELDS.keys())

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for all fields."""
        return {
            name: mapping.source_field
            for name, mapping in cls.AVAILABLE_FIELDS.items()
        }


class FieldMapper:
    """Maps source data to transaction properties based on user mappings."""

    def __init__(self, mappings: Dict[str, str]):
        """
        Initialize mapper.

        Args:
            mappings: Dict mapping target property names to source field names
                     e.g., {"date": "booking", "partner_iban": "partnerAccount.iban"}
                     This format allows multiple JSON fields to map to different transaction properties.
        """
        self.mappings = mappings
        self.registry = FieldMappingRegistry()

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """
        Get value from nested dict using dot notation.

        Args:
            data: Source dictionary
            key: Key with optional dot notation (e.g., "partnerAccount.iban")

        Returns:
            Value at the nested path, or None if not found
        """
        if '.' not in key:
            return data.get(key)

        parts = key.split('.')
        current = data
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    def map_row(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a row of source data to transaction properties.

        Args:
            source_data: Dictionary with source field values

        Returns:
            Dictionary with mapped transaction properties
        """
        result = {}

        # mappings format: {target_property: source_field}
        # e.g., {"date": "booking", "partner_iban": "partnerAccount.iban"}
        for target_property, source_field in self.mappings.items():
            # Use nested value getter to handle dot notation
            value = self._get_nested_value(source_data, source_field)

            if value is None or value == '':
                continue

            # Look up field info by the target property name
            # The registry keys match the target_property for most fields
            field_info = self.registry.get_field(target_property)

            if not field_info:
                # Try looking up by common name mappings
                # Some target_properties differ from registry keys
                name_to_key = {
                    "partner_account_number": "partner_account",
                }
                registry_key = name_to_key.get(target_property, target_property)
                field_info = self.registry.get_field(registry_key)

            if not field_info:
                # If still not in registry, use as-is
                result[target_property] = value
                continue

            # Transform value based on data type
            try:
                if field_info.data_type == "date":
                    parsed_value = self._parse_date(value, field_info.date_format)
                    if parsed_value:
                        result[target_property] = parsed_value
                    else:
                        # Debug: date parsing returned None
                        import logging
                        logging.warning(f"Date parsing failed for {target_property}: raw value was {repr(value)}")
                elif field_info.data_type == "decimal":
                    # Special handling for amount with precision
                    # If source_field is like "amount.value", look for precision in "amount.precision"
                    precision = None
                    if '.value' in source_field:
                        precision_field = source_field.replace('.value', '.precision')
                        precision = self._get_nested_value(source_data, precision_field)
                    # Also check if the parent "amount" object has precision
                    elif '.' not in source_field:
                        # Direct field like "amount" - check if source_data has amount.precision
                        precision = self._get_nested_value(source_data, f"{source_field}.precision")

                    parsed_value = self._parse_decimal(value, precision)
                    if parsed_value is not None:
                        result[target_property] = parsed_value
                elif field_info.data_type == "integer":
                    result[target_property] = int(value)
                else:  # string
                    result[target_property] = str(value).strip()
            except Exception as e:
                # Log but don't fail on individual field conversion
                # Only store non-None values
                if value is not None and value != '':
                    result[target_property] = value

        return result

    @staticmethod
    def _parse_date(value: Any, date_format: Optional[str] = None) -> str:
        """Parse date value to YYYY-MM-DD format."""
        from datetime import datetime

        if isinstance(value, str):
            if not value or value.lower() in ('null', 'none', ''):
                return None

            # Try multiple formats
            formats = [
                date_format,
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%d/%m/%Y",
            ]

            for fmt in formats:
                if fmt is None:
                    continue
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If no format matches, try ISO parse
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d")
            except:
                return None

        return str(value)[:10] if value else None

    @staticmethod
    def _parse_decimal(value: Any, precision: Any = None) -> str:
        """Parse decimal value, applying precision if provided.

        Args:
            value: The numeric value (can be int, float, str, or dict with value/precision)
            precision: Optional precision to apply (e.g., 2 means divide by 100)

        Returns:
            String representation of the decimal value
        """
        from decimal import Decimal, InvalidOperation

        if value is None or value == '':
            return None

        if isinstance(value, dict):
            # Handle {"value": -350, "precision": 2, "currency": "EUR"} structure
            val = value.get("value")
            dict_precision = value.get("precision", 0)
            try:
                amount = Decimal(str(val))
                if dict_precision and int(dict_precision) > 0:
                    amount = amount / (10 ** int(dict_precision))
                return str(amount)
            except (InvalidOperation, TypeError):
                return None

        try:
            # Handle string with comma as decimal separator
            if isinstance(value, str):
                value = value.replace(",", ".")

            amount = Decimal(str(value))

            # Apply precision if provided (e.g., precision=2 means value 5000 -> 50.00)
            if precision is not None:
                try:
                    prec = int(precision)
                    if prec > 0:
                        amount = amount / (10 ** prec)
                except (ValueError, TypeError):
                    pass

            return str(amount)
        except InvalidOperation:
            return None

