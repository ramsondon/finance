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
        # Core fields
        "date": FieldMapping("date", "date", "date", required=True),
        "amount": FieldMapping("amount", "amount", "decimal", required=True),
        "description": FieldMapping("description", "description", "string"),
        "type": FieldMapping("type", "type", "string"),

        # Partner/Counterparty
        "partner_name": FieldMapping("partnerName", "partner_name", "string"),
        "partner_iban": FieldMapping("partnerIban", "partner_iban", "string"),
        "partner_account": FieldMapping("partnerAccount", "partner_account_number", "string"),
        "partner_bank_code": FieldMapping("bankCode", "partner_bank_code", "string"),
        "merchant_name": FieldMapping("merchantName", "merchant_name", "string"),

        # Owner/Sender
        "owner_account": FieldMapping("ownerAccountNumber", "owner_account", "string"),
        "owner_name": FieldMapping("ownerAccountTitle", "owner_name", "string"),

        # Dates
        "booking_date": FieldMapping("booking", "booking_date", "date"),
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
        "booking_type": FieldMapping("bookingTypeTranslation", "booking_type", "string"),

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
            mappings: Dict mapping source field names to target property names
                     e.g., {"booking": "date", "partnerName": "partner_name"}
        """
        self.mappings = mappings
        self.registry = FieldMappingRegistry()

    def map_row(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a row of source data to transaction properties.

        Args:
            source_data: Dictionary with source field values

        Returns:
            Dictionary with mapped transaction properties
        """
        result = {}

        for source_field, target_property in self.mappings.items():
            if source_field not in source_data:
                continue

            value = source_data[source_field]
            if value is None or value == '':
                continue

            # Get field mapping info
            field_info = self.registry.get_field(target_property)
            if not field_info:
                # If not in registry, use as-is
                result[target_property] = value
                continue

            # Transform value based on data type
            try:
                if field_info.data_type == "date":
                    result[target_property] = self._parse_date(value, field_info.date_format)
                elif field_info.data_type == "decimal":
                    result[target_property] = self._parse_decimal(value)
                elif field_info.data_type == "integer":
                    result[target_property] = int(value)
                else:  # string
                    result[target_property] = str(value).strip()
            except Exception as e:
                # Log but don't fail on individual field conversion
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
    def _parse_decimal(value: Any) -> str:
        """Parse decimal value preserving precision."""
        from decimal import Decimal, InvalidOperation

        if value is None or value == '':
            return None

        if isinstance(value, dict):
            # Handle {"value": -350, "precision": 2} structure
            val = value.get("value")
            return str(Decimal(str(val)))

        try:
            return str(Decimal(str(value)))
        except InvalidOperation:
            return None

