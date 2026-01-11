from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import csv
from .field_mapper import FieldMapper

DATE_FORMATS = ["%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"]


@dataclass
class ParsedRow:
    date: datetime
    amount: Decimal
    description: str
    type: str
    category_name: Optional[str] = None
    extra_fields: Dict = None  # Additional mapped fields


class CSVImporter:
    """Parse a CSV file-like object into validated rows with flexible field mapping.

    Can auto-detect standard headers or use provided field mappings.
    """

    def __init__(self, field_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize importer.

        Args:
            field_mappings: Optional dict mapping CSV columns to transaction properties.
                           If None, uses default/auto-detected mappings.
        """
        self.field_mappings = field_mappings
        self.mapper = FieldMapper(field_mappings) if field_mappings else None

    def parse(self, file) -> tuple[List[ParsedRow], List[Dict]]:
        """Parse CSV file with flexible field mapping."""
        reader = csv.DictReader((l.decode() if isinstance(l, bytes) else l for l in file))
        rows: List[ParsedRow] = []
        errors: List[Dict] = []

        for idx, raw in enumerate(reader, start=1):
            try:
                # Use field mapper if provided, otherwise use defaults
                if self.mapper:
                    mapped = self.mapper.map_row(raw)
                    parsed_row = self._map_to_parsed_row(mapped, idx)
                else:
                    parsed_row = self._parse_default_format(raw, idx)

                rows.append(parsed_row)
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        return rows, errors

    def _parse_default_format(self, raw: Dict, row_idx: int) -> ParsedRow:
        """Parse row using default format (date, amount, description, type, category)."""
        date_str = (raw.get("date") or "").strip()
        amount_str = (raw.get("amount") or "").replace(",", ".").strip()
        description = (raw.get("description") or "").strip()
        type_ = (raw.get("type") or "").strip().lower()
        category_name = raw.get("category") or None

        date = None
        for fmt in DATE_FORMATS:
            try:
                date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        if date is None:
            raise ValueError(f"Invalid date format: {date_str}")

        amount = Decimal(amount_str)

        if type_ not in {"income", "expense", "transfer"}:
            raise ValueError(f"Invalid type: {type_}")

        return ParsedRow(
            date=date,
            amount=amount,
            description=description,
            type=type_,
            category_name=category_name,
            extra_fields={}
        )

    def _map_to_parsed_row(self, mapped: Dict, row_idx: int) -> ParsedRow:
        """Convert mapped fields to ParsedRow."""
        # Extract required fields
        date_val = mapped.get("date")
        amount_val = mapped.get("amount")
        description = mapped.get("description", "")
        tx_type = mapped.get("type", "expense")
        category_name = mapped.get("category")

        # Parse date
        if isinstance(date_val, str):
            for fmt in DATE_FORMATS:
                try:
                    date = datetime.strptime(date_val, fmt)
                    break
                except ValueError:
                    continue
            else:
                try:
                    date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                except:
                    raise ValueError(f"Invalid date: {date_val}")
        else:
            date = date_val

        # Parse amount
        if isinstance(amount_val, str):
            amount = Decimal(amount_val.replace(",", "."))
        else:
            amount = Decimal(str(amount_val))

        if tx_type not in {"income", "expense", "transfer"}:
            tx_type = "income" if amount > 0 else "expense"

        # Collect extra fields
        extra_fields = {k: v for k, v in mapped.items()
                       if k not in {"date", "amount", "description", "type", "category"} and v}

        return ParsedRow(
            date=date,
            amount=amount,
            description=str(description).strip() if description else "",
            type=tx_type,
            category_name=category_name,
            extra_fields=extra_fields
        )


