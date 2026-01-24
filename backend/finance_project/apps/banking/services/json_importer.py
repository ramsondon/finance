from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Tuple, Optional
from .field_mapper import FieldMapper, FieldMappingRegistry

DATE_KEYS = ["booking", "valuation", "transactionDateTime", "execution"]

@dataclass
class ParsedRow:
    date: datetime
    amount: Decimal
    description: str
    type: str  # income|expense|transfer
    category_name: Optional[str] = None
    extra_fields: dict = None  # Additional mapped fields


class JSONImporter:
    """Parses transactional JSON into normalized rows with flexible field mapping.

    Can auto-detect standard fields or use provided field mappings.
    """

    def __init__(self, field_mappings: Optional[dict[str, str]] = None):
        """
        Initialize importer.

        Args:
            field_mappings: Optional dict mapping JSON fields to transaction properties.
        """
        self.field_mappings = field_mappings
        self.mapper = FieldMapper(field_mappings) if field_mappings else None

    def parse(self, content: Any) -> Tuple[List[ParsedRow], List[str]]:
        """Parse JSON content with flexible field mapping."""
        rows: List[ParsedRow] = []
        errors: List[str] = []
        data = content

        if not isinstance(data, list):
            errors.append("JSON payload must be a list of transactions")
            return rows, errors

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Item {idx} is not an object")
                continue

            try:
                if self.mapper:
                    # Use field mapper
                    mapped = self.mapper.map_row(item)
                    parsed_row = self._map_to_parsed_row(mapped, idx)
                else:
                    # Use auto-detection
                    parsed_row = self._parse_auto_detect(item, idx)

                rows.append(parsed_row)
            except Exception as e:
                errors.append(f"Item {idx}: {str(e)}")
                continue

        return rows, errors

    def _parse_auto_detect(self, item: dict, idx: int) -> ParsedRow:
        """Auto-detect and parse transaction from JSON structure."""
        date = self._parse_date(item)
        amount = self._parse_amount(item)

        if date is None or amount is None:
            raise ValueError("Missing required date or amount")

        description = self._compose_description(item)
        tx_type = self._infer_type(amount, item)

        # Category hint
        category_name = None
        cats = item.get("categories")
        if isinstance(cats, list) and cats:
            cat0 = cats[0]
            category_name = str(cat0) if cat0 is not None else None
        elif item.get("bookingTypeTranslation"):
            category_name = str(item.get("bookingTypeTranslation"))

        # Collect extra fields
        # Safe nested object access - use or {} if the nested object is None
        partner_account = item.get("partnerAccount") or {}
        extra_fields = {
            "reference": item.get("reference"),
            "partner_name": item.get("partnerName"),
            "partner_iban": partner_account.get("iban") if isinstance(partner_account, dict) else None,
            "partner_account": partner_account.get("number") if isinstance(partner_account, dict) else None,
            "partner_bank_code": partner_account.get("bankCode") if isinstance(partner_account, dict) else None,
            "owner_account": item.get("ownerAccountNumber"),
            "owner_name": item.get("ownerAccountTitle"),
            "reference_number": item.get("referenceNumber"),
            "booking_date": self._parse_date(item),
            "virtual_card_number": item.get("virtualCardNumber"),
            "virtual_card_device": item.get("virtualCardDeviceName"),
            "payment_app": item.get("virtualCardMobilePaymentApplicationName"),
            "payment_method": item.get("paymentMethod"),
            "merchant_name": item.get("merchantName"),
            "card_brand": item.get("cardBrand"),
            "exchange_rate": item.get("exchangeRateValue"),
            "transaction_fee": item.get("transactionFee"),
            "sepa_scheme": item.get("sepaScheme"),
        }
        # Remove None values
        extra_fields = {k: v for k, v in extra_fields.items() if v}

        return ParsedRow(
            date=date,
            amount=amount,
            description=description,
            type=tx_type,
            category_name=category_name,
            extra_fields=extra_fields
        )

    def _parse_date(self, item: dict) -> Optional[datetime]:
        for key in DATE_KEYS:
            val = item.get(key)
            if val:
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%f%z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%d",
                ]:
                    try:
                        return datetime.strptime(val, fmt)
                    except Exception:
                        continue
        return None

    def _parse_amount(self, item: dict) -> Optional[Decimal]:
        amt = item.get("amount")
        if isinstance(amt, dict):
            val = amt.get("value")
            precision = amt.get("precision", 2)
            try:
                # Convert value to Decimal and divide by 10^precision
                # e.g., 5070 with precision 2 becomes 50.70
                amount = Decimal(str(val))
                if precision and precision > 0:
                    amount = amount / (10 ** precision)
                return amount
            except (InvalidOperation, TypeError, ZeroDivisionError):
                return None
        try:
            return Decimal(str(item.get("amount")))
        except (InvalidOperation, TypeError):
            return None

    def _compose_description(self, item: dict) -> str:
        parts = []
        if item.get("reference"):
            parts.append(str(item.get("reference")))
        if item.get("partnerName"):
            parts.append(str(item.get("partnerName")))
        if item.get("virtualCardMobilePaymentApplicationName"):
            parts.append(str(item.get("virtualCardMobilePaymentApplicationName")))
        if item.get("virtualCardDeviceName"):
            parts.append(str(item.get("virtualCardDeviceName")))
        if item.get("referenceNumber"):
            parts.append(f"Ref: {item.get('referenceNumber')}")
        desc = " | ".join([p for p in parts if p])
        return desc or "Transaction"

    def _infer_type(self, amount: Decimal, item: dict) -> str:
        if amount is None:
            return "expense"
        return "income" if amount >= 0 else "expense"

    def _map_to_parsed_row(self, mapped: dict, idx: int) -> ParsedRow:
        """Convert mapped fields to ParsedRow when using field mapper."""
        # Extract required fields
        # Accept any date-like field as the primary date
        date_val = None
        date_field_used = None
        for date_field in ["date", "booking_date", "valuation_date"]:
            val = mapped.get(date_field)
            if val:
                date_val = val
                date_field_used = date_field
                break

        amount_val = mapped.get("amount")

        # Reference field with fallbacks (Option 1)
        # Priority: reference → partner_name → partner_iban → description
        reference = mapped.get("reference", "")
        if not reference:
            # Try fallback fields in priority order
            fallback_fields = ["partner_name", "partner_iban", "description", "merchant_name"]
            for fallback_field in fallback_fields:
                fallback_val = mapped.get(fallback_field, "")
                if fallback_val:
                    reference = str(fallback_val)
                    break

        description = mapped.get("description", "") or reference  # Fallback to reference

        available_keys = list(mapped.keys())

        if not date_val:
            # Show what date values we found for debugging
            date_debug = {k: mapped.get(k) for k in ["date", "booking_date", "valuation_date"]}
            raise ValueError(f"Missing required field: date. Mapped fields: {available_keys}. Date values found: {date_debug}")
        if amount_val is None:
            raise ValueError(f"Missing required field: amount. Mapped fields: {available_keys}")
        if not reference:
            raise ValueError(f"Missing required field: reference (tried fallbacks: partner_name, partner_iban, description, merchant_name). Mapped fields: {available_keys}")

        # Parse date if it's a string
        if isinstance(date_val, str):
            date = None
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d",
            ]:
                try:
                    date = datetime.strptime(date_val, fmt)
                    break
                except ValueError:
                    continue
            if date is None:
                try:
                    date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                except:
                    raise ValueError(f"Invalid date format: {date_val}")
        else:
            date = date_val

        # Parse amount
        if isinstance(amount_val, Decimal):
            amount = amount_val
        elif isinstance(amount_val, (int, float)):
            amount = Decimal(str(amount_val))
        elif isinstance(amount_val, str):
            amount = Decimal(amount_val.replace(",", "."))
        else:
            raise ValueError(f"Invalid amount: {amount_val}")

        # Infer type from amount
        tx_type = "income" if amount >= 0 else "expense"

        # Collect extra fields (all mapped fields except core ones)
        core_fields = {"date", "amount", "description", "reference", "type"}
        extra_fields = {k: v for k, v in mapped.items() if k not in core_fields and v}

        # Always include reference in extra_fields
        if reference:
            extra_fields["reference"] = reference

        return ParsedRow(
            date=date,
            amount=amount,
            description=str(description).strip() if description else "Transaction",
            type=tx_type,
            category_name=None,
            extra_fields=extra_fields
        )


