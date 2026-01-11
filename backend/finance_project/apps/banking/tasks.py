from __future__ import annotations
from celery import shared_task
from django.db import transaction as db_txn
from datetime import datetime
from decimal import Decimal
import logging
from .models import BankAccount, Transaction, Category
from .services.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def import_transactions_task(self, account_id: int, rows: list[dict]):
    """Import transactions with extended field support and safe truncation."""
    logger.info(f"Starting import_transactions_task for account_id={account_id} with {len(rows)} rows")

    account = BankAccount.objects.get(id=account_id)
    engine = RuleEngine()

    # Field length limits to prevent database errors
    FIELD_LIMITS = {
        "description": 1024,
        "partner_name": 255,
        "partner_iban": 34,
        "partner_account_number": 50,
        "partner_bank_code": 20,
        "owner_account": 50,
        "owner_name": 255,
        "reference_number": 100,
        "virtual_card_number": 20,
        "virtual_card_device": 1024,
        "payment_app": 100,
        "merchant_name": 255,
        "card_brand": 50,
        "booking_type": 100,
        "sepa_scheme": 50,
    }

    def truncate_field(field_name: str, value) -> str:
        """Safely truncate field values to max length with logging."""
        if value is None or value == '':
            return ''

        if not isinstance(value, str):
            value = str(value)

        limit = FIELD_LIMITS.get(field_name, 255)

        original_len = len(value)
        if original_len > limit:
            logger.warning(
                f"Field '{field_name}' exceeds limit. "
                f"Original length: {original_len}, Limit: {limit}. "
                f"Value preview: {value[:100]}..."
            )
            return value[:limit]
        return value

    with db_txn.atomic():
        for idx, row in enumerate(rows, start=1):
            try:
                logger.debug(f"Processing row {idx}/{len(rows)}")

                # Parse date
                try:
                    date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                except (ValueError, KeyError) as e:
                    logger.error(f"Row {idx}: Failed to parse date. Error: {e}. Value: {row.get('date')}")
                    raise

                # Parse amount with precision support
                try:
                    amount_val = row["amount"]

                    # Handle structured amount object with precision (e.g., {"value": 5070, "precision": 2})
                    if isinstance(amount_val, dict):
                        value = Decimal(str(amount_val.get("value", 0)))
                        precision = amount_val.get("precision", 2)
                        # Divide by 10^precision to get correct decimal value
                        # e.g., 5070 with precision 2 becomes 50.70
                        amount = value / (10 ** precision)
                        logger.debug(f"Row {idx}: Parsed structured amount. Value={amount_val.get('value')}, Precision={precision}, Result={amount}")
                    else:
                        # Simple numeric value
                        amount = Decimal(str(amount_val))
                        logger.debug(f"Row {idx}: Parsed simple amount. Value={amount}")
                except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
                    logger.error(f"Row {idx}: Failed to parse amount. Error: {e}. Value: {row.get('amount')}")
                    raise

                # Validate and truncate all fields
                logger.debug(f"Row {idx}: Validating fields")
                tx_data = {
                    "account": account,
                    "date": date,
                    "amount": amount,
                    "description": truncate_field("description", row.get("description", "")),
                    "type": row.get("type", "expense"),
                    # Extended fields
                    "partner_name": truncate_field("partner_name", row.get("partner_name", "")),
                    "partner_iban": truncate_field("partner_iban", row.get("partner_iban", "")),
                    "partner_account_number": truncate_field("partner_account_number", row.get("partner_account_number", "")),
                    "partner_bank_code": truncate_field("partner_bank_code", row.get("partner_bank_code", "")),
                    "owner_account": truncate_field("owner_account", row.get("owner_account", "")),
                    "owner_name": truncate_field("owner_name", row.get("owner_name", "")),
                    "reference_number": truncate_field("reference_number", row.get("reference_number", "")),
                    "virtual_card_number": truncate_field("virtual_card_number", row.get("virtual_card_number", "")),
                    "virtual_card_device": truncate_field("virtual_card_device", row.get("virtual_card_device", "")),
                    "payment_app": truncate_field("payment_app", row.get("payment_app", "")),
                    "merchant_name": truncate_field("merchant_name", row.get("merchant_name", "")),
                    "card_brand": truncate_field("card_brand", row.get("card_brand", "")),
                    "booking_type": truncate_field("booking_type", row.get("booking_type", "")),
                    "sepa_scheme": truncate_field("sepa_scheme", row.get("sepa_scheme", "")),
                    "payment_method": truncate_field("payment_method", row.get("payment_method", "")),
                }

                # Log all field lengths before saving
                logger.debug(f"Row {idx}: Field lengths: {[(k, len(v) if isinstance(v, str) else 0) for k, v in tx_data.items() if isinstance(v, str)]}")


                # Handle optional date fields
                if row.get("booking_date"):
                    try:
                        booking_date_val = row["booking_date"]
                        # Handle both string and datetime objects
                        if isinstance(booking_date_val, str):
                            tx_data["booking_date"] = datetime.strptime(booking_date_val, "%Y-%m-%d").date()
                        else:
                            # Already a datetime object, extract the date part
                            tx_data["booking_date"] = booking_date_val.date() if hasattr(booking_date_val, 'date') else booking_date_val
                        logger.debug(f"Row {idx}: Set booking_date={tx_data['booking_date']}")
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"Row {idx}: Failed to parse booking_date. Error: {e}. Value: {row.get('booking_date')}")
                        tx_data["booking_date"] = None

                if row.get("valuation_date"):
                    try:
                        valuation_date_val = row["valuation_date"]
                        # Handle both string and datetime objects
                        if isinstance(valuation_date_val, str):
                            tx_data["valuation_date"] = datetime.strptime(valuation_date_val, "%Y-%m-%d").date()
                        else:
                            # Already a datetime object, extract the date part
                            tx_data["valuation_date"] = valuation_date_val.date() if hasattr(valuation_date_val, 'date') else valuation_date_val
                        logger.debug(f"Row {idx}: Set valuation_date={tx_data['valuation_date']}")
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"Row {idx}: Failed to parse valuation_date. Error: {e}. Value: {row.get('valuation_date')}")
                        tx_data["valuation_date"] = None

                # Handle optional numeric fields
                if row.get("exchange_rate"):
                    try:
                        tx_data["exchange_rate"] = Decimal(str(row["exchange_rate"]))
                        logger.debug(f"Row {idx}: Set exchange_rate={tx_data['exchange_rate']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Row {idx}: Failed to parse exchange_rate. Error: {e}. Value: {row.get('exchange_rate')}")
                        tx_data["exchange_rate"] = None

                if row.get("transaction_fee"):
                    try:
                        tx_data["transaction_fee"] = Decimal(str(row["transaction_fee"]))
                        logger.debug(f"Row {idx}: Set transaction_fee={tx_data['transaction_fee']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Row {idx}: Failed to parse transaction_fee. Error: {e}. Value: {row.get('transaction_fee')}")
                        tx_data["transaction_fee"] = None

                # Create transaction
                logger.debug(f"Row {idx}: Creating transaction object")
                tx = Transaction.objects.create(**tx_data)
                logger.info(f"Row {idx}: Transaction created successfully. ID={tx.id}, Amount={tx.amount}, Date={tx.date}")

                # optional category by name
                cat_name = row.get("category_name")
                if cat_name:
                    logger.debug(f"Row {idx}: Assigning category '{cat_name}'")
                    cat, created = Category.objects.get_or_create(user=account.user, name=cat_name)
                    tx.category = cat
                    tx.save(update_fields=["category"])
                    logger.info(f"Row {idx}: Category assigned. Created={created}")

                # Apply rules
                logger.debug(f"Row {idx}: Applying categorization rules")
                engine.apply_rules(account.user_id, tx)
                logger.debug(f"Row {idx}: Rules applied successfully")

            except Exception as e:
                logger.error(
                    f"Row {idx}: Failed to import transaction. "
                    f"Error type: {type(e).__name__}. "
                    f"Error message: {str(e)}. "
                    f"Row data keys: {list(row.keys())}",
                    exc_info=True
                )
                raise

    logger.info(f"Completed import_transactions_task for account_id={account_id}. Processed {len(rows)} rows successfully")


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def apply_rules_task(self, user_id: int):
    engine = RuleEngine()
    qs = Transaction.objects.filter(account__user_id=user_id, category__isnull=True)
    for tx in qs.iterator():
        engine.apply_rules(user_id, tx)
