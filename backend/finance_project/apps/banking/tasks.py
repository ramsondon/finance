from __future__ import annotations
from celery import shared_task
from django.db import transaction as db_txn
from datetime import datetime
from decimal import Decimal
import logging
from .models import BankAccount, Transaction, Category, Import, ImportTransaction
from .services.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def import_transactions_task(self, account_id: int, rows: list[dict], file_name: str = '', import_source: str = 'csv'):
    """Import transactions with extended field support and safe truncation.

    Creates an Import record to track this import session and connects all
    imported transactions to it via ImportTransaction records.

    Args:
        account_id: BankAccount ID to import to
        rows: List of transaction dictionaries to import
        file_name: Original file name (optional, for tracking)
        import_source: Source of import (e.g., 'csv', 'json', 'bank_api')
    """
    logger.info(f"Starting import_transactions_task for account_id={account_id} with {len(rows)} rows from source={import_source}")

    account = BankAccount.objects.get(id=account_id)
    engine = RuleEngine()

    # Create Import record to track this import session
    import_record = Import.objects.create(
        account=account,
        user=account.user,
        import_source=import_source,
        file_name=file_name,
        total_transactions=len(rows),
        meta={}
    )
    logger.info(f"Created Import record. ID={import_record.id}, file_name={file_name}, source={import_source}")

    # Field length limits to prevent database errors
    FIELD_LIMITS = {
        "reference": 512,
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

    successful_count = 0
    failed_count = 0

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

                # Determine transaction type: label as "transfer" if partner_iban matches internal account
                transaction_type = row.get("type", "expense")
                partner_iban = row.get("partner_iban", "").strip().upper()

                if partner_iban:
                    # Check if partner_iban matches any of the user's bank accounts
                    user_account_ibans = BankAccount.objects.filter(
                        user=account.user
                    ).values_list('iban', flat=True)

                    user_account_ibans_upper = [iban.strip().upper() for iban in user_account_ibans if iban]

                    if partner_iban in user_account_ibans_upper:
                        transaction_type = "transfer"
                        logger.info(f"Row {idx}: Detected internal transfer. Partner IBAN matches user account. Setting type='transfer'")
                    else:
                        logger.debug(f"Row {idx}: Partner IBAN '{partner_iban}' does not match any user accounts")

                tx_data = {
                    "account": account,
                    "date": date,
                    "amount": amount,
                    "reference": truncate_field("reference", row.get("reference", "")),
                    "description": truncate_field("description", row.get("description", "")),
                    "type": transaction_type,
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

                # Create ImportTransaction link to track this import
                ImportTransaction.objects.create(
                    import_record=import_record,
                    transaction=tx,
                    was_created=True
                )
                logger.debug(f"Row {idx}: Created ImportTransaction link. ID={tx.id}")

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

                successful_count += 1

            except Exception as e:
                logger.error(
                    f"Row {idx}: Failed to import transaction. "
                    f"Error type: {type(e).__name__}. "
                    f"Error message: {str(e)}. "
                    f"Row data keys: {list(row.keys())}",
                    exc_info=True
                )
                failed_count += 1
                raise

    # Update Import record with final statistics
    import_record.successful_transactions = successful_count
    import_record.failed_transactions = failed_count
    import_record.save(update_fields=['successful_transactions', 'failed_transactions'])

    logger.info(
        f"Completed import_transactions_task for account_id={account_id}. "
        f"Import ID={import_record.id}: "
        f"Successful={successful_count}, Failed={failed_count}, Total={len(rows)}"
    )


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def apply_rules_task(self, user_id: int):
    engine = RuleEngine()
    qs = Transaction.objects.filter(account__user_id=user_id, category__isnull=True)
    for tx in qs.iterator():
        engine.apply_rules(user_id, tx)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def detect_recurring_transactions_task(self, account_id: int, days_back: int = 365):
    """
    Detect recurring transaction patterns for a bank account.

    This task analyzes transaction history and identifies recurring payments
    such as subscriptions, regular expenses, and income deposits.
    """
    from .services.recurring_detector import RecurringTransactionDetector
    from .models import RecurringTransaction

    logger.info(f"Starting recurring transaction detection for account_id={account_id}, looking back {days_back} days")

    try:
        account = BankAccount.objects.get(id=account_id)
        detector = RecurringTransactionDetector(account_id)
        patterns = detector.detect(days_back=days_back)

        logger.info(f"Detected {len(patterns)} recurring patterns for account {account_id}")

        # Store detected patterns in database
        created_count = 0
        updated_count = 0

        for pattern in patterns:
            # Try to update existing or create new
            recurring, created = RecurringTransaction.objects.update_or_create(
                account=account,
                description=pattern.description,
                frequency=pattern.frequency,
                defaults={
                    'user_id': account.user_id,
                    'merchant_name': '',
                    'amount': pattern.amount,
                    'next_expected_date': pattern.next_expected_date,
                    'last_occurrence_date': pattern.last_occurrence_date,
                    'occurrence_count': pattern.occurrence_count,
                    'confidence_score': pattern.confidence_score,
                    'similar_descriptions': pattern.similar_descriptions,
                    'transaction_ids': pattern.transaction_ids,
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1
                logger.debug(f"Updated recurring transaction: {pattern.description} ({pattern.frequency})")

        logger.info(f"Created {created_count} new recurring patterns, updated {updated_count} existing patterns")

    except BankAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error detecting recurring transactions for account {account_id}: {str(e)}", exc_info=True)
        raise


@shared_task(bind=True)
def check_recurring_transaction_overdue_task(self):
    """
    Check for overdue recurring transactions and create notifications.

    This runs periodically (e.g., daily) to identify subscriptions that
    haven't occurred when expected.
    """
    from .models import RecurringTransaction
    from datetime import datetime

    logger.info("Checking for overdue recurring transactions")

    now = datetime.now().date()
    overdue = RecurringTransaction.objects.filter(
        is_active=True,
        is_ignored=False,
        next_expected_date__lt=now
    )

    overdue_count = overdue.count()
    logger.info(f"Found {overdue_count} overdue recurring transactions")

    # TODO: In future, create notifications for overdue recurring transactions
    # This could be used to alert users of missed payments or cancelled subscriptions


@shared_task(bind=True, max_retries=3)
def generate_rules_from_categories_task(self, user_id: int, language: str = None):
    """
    Generate categorization rules using TWO STRATEGIES:

    Strategy A (Preferred): Analyze pre-assigned transactions (2+ per category)
    Strategy B (Fallback): Use category name to find matching transactions (2+ matches)

    This task:
    1. Gets all categories created by the user
    2. Gets ALL transactions (regardless of category assignment)
    3. For each category, tries Strategy A, then Strategy B if needed
    4. Creates rules based on discovered patterns
    5. Uses configurable confidence threshold

    Supports multilingual logging based on user's language preference.

    Args:
        user_id: User ID to generate rules for
        language: Language code ('en', 'de', etc.). Defaults to user's language preference.

    Returns:
        dict with:
        - suggestions_count: Total categories analyzed
        - created_count: Rules successfully created
        - insufficient_data: Whether there was insufficient transaction data
        - created_rules: List of created rules with strategy info
    """
    from django.conf import settings
    from ..accounts.models import UserProfile

    try:
        logger.info(f"[{user_id}] Starting rule generation")

        # Get user and language
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            if language is None:
                language = profile.get_language()
        except UserProfile.DoesNotExist:
            language = language or 'en'

        logger.info(f"[{language.upper()}] Language: {language} | User: {user_id}")

        # Get confidence threshold from settings
        confidence_threshold = getattr(settings, 'RULE_GENERATION_CONFIDENCE_THRESHOLD', 0.7)
        logger.info(f"[{language.upper()}] Confidence threshold: {confidence_threshold}")

        # Get all categories for this user
        categories = Category.objects.filter(user_id=user_id)
        category_count = categories.count()

        if category_count == 0:
            logger.warning(f"[{language.upper()}] No categories found")
            return {
                'suggestions_count': 0,
                'created_count': 0,
                'insufficient_data': True,
                'message': 'No categories found. Create categories first before generating rules.'
            }

        logger.info(f"[{language.upper()}] Found {category_count} categories")

        # Get ALL transactions for this user (regardless of categorization)
        all_transactions = list(Transaction.objects.filter(
            account__user_id=user_id
        ).select_related('category').order_by("-date")[:2000])  # Limit to 2000 for performance

        total_transaction_count = len(all_transactions)
        logger.info(f"[{language.upper()}] Found {total_transaction_count} total transactions")

        # Check if enough data
        min_transactions = getattr(settings, 'RULE_GENERATION_MIN_TRANSACTIONS', 10)
        if total_transaction_count < min_transactions:
            logger.warning(f"[{language.upper()}] Insufficient data: {total_transaction_count}/{min_transactions}")
            return {
                'suggestions_count': 0,
                'created_count': 0,
                'insufficient_data': True,
                'message': f'Need at least {min_transactions} transactions to generate rules'
            }

        suggestions = []
        created_rules = []

        # For each category, try two strategies
        for category in categories:
            logger.info(f"[{language.upper()}] ===== Analyzing: {category.name} =====")

            # STRATEGY A: Check if transactions are already assigned to this category
            categorized_txs = [tx for tx in all_transactions if tx.category_id == category.id]
            categorized_count = len(categorized_txs)

            analysis_txs = None
            strategy_used = None

            if categorized_count >= 2:
                # STRATEGY A: Use pre-assigned transactions
                logger.info(f"[{language.upper()}] Strategy A: Found {categorized_count} pre-assigned txs")
                analysis_txs = categorized_txs
                strategy_used = "assigned"
            else:
                # STRATEGY B: Use category name to find matching transactions
                logger.info(f"[{language.upper()}] Strategy B: Searching by category name...")
                category_name_lower = category.name.lower()
                category_keywords = [w for w in category_name_lower.split() if len(w) > 2]

                logger.debug(f"[{language.upper()}] Keywords from '{category.name}': {category_keywords}")

                if category_keywords:
                    # Find transactions matching category keywords
                    matching_txs = []
                    for tx in all_transactions:
                        if tx.description:
                            tx_desc_lower = tx.description.lower()
                            if any(kw in tx_desc_lower for kw in category_keywords):
                                matching_txs.append(tx)

                    logger.info(f"[{language.upper()}] Found {len(matching_txs)} matching txs for '{category.name}'")

                    if len(matching_txs) >= 2:
                        analysis_txs = matching_txs
                        strategy_used = "keyword_search"
                    else:
                        logger.debug(f"[{language.upper()}] Only {len(matching_txs)} matches, need 2+. Skipping.")
                        continue
                else:
                    logger.debug(f"[{language.upper()}] No keywords in category name. Skipping.")
                    continue

            if analysis_txs is None:
                continue

            # Analyze patterns from selected transactions
            descriptions = [tx.description.lower() for tx in analysis_txs if tx.description]
            amounts = [float(tx.amount) for tx in analysis_txs]
            types = [tx.type for tx in analysis_txs]

            # IMPROVED: Find keywords with frequency threshold (40%+)
            keywords = set()
            for desc in descriptions:
                words = set(desc.split())
                keywords.update(w for w in words if len(w) > 3 and w.isalnum())

            most_common_keyword = None
            keyword_frequency = 0.0
            if keywords:
                keyword_counts = {}
                for keyword in keywords:
                    count = sum(1 for desc in descriptions if keyword in desc)
                    keyword_counts[keyword] = count

                # IMPROVED: Only accept keywords that appear in 40%+ of transactions
                min_frequency = max(1, len(descriptions) * 0.4)
                qualified_keywords = {k: v for k, v in keyword_counts.items() if v >= min_frequency}

                if qualified_keywords:
                    most_common_keyword = max(qualified_keywords, key=qualified_keywords.get)
                    keyword_frequency = qualified_keywords[most_common_keyword] / len(descriptions)
                    logger.debug(
                        f"[{language.upper()}] Keyword '{most_common_keyword}': "
                        f"frequency={keyword_frequency:.2f} (appears {qualified_keywords[most_common_keyword]}/{len(descriptions)})"
                    )

            # IMPROVED: Amount confidence using Coefficient of Variation
            if amounts and len(amounts) >= 2:
                avg_amount = sum(amounts) / len(amounts)
                amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
                amount_std_dev = amount_variance ** 0.5

                if avg_amount > 0:
                    # Use Coefficient of Variation for better scaling
                    cv = amount_std_dev / abs(avg_amount)
                    # Convert CV to confidence: high CV = low confidence
                    # CV 0.1 (10%) → 0.95 confidence
                    # CV 0.5 (50%) → 0.67 confidence
                    # CV 1.0 (100%) → 0.37 confidence
                    amount_confidence = max(0, 1 - (cv * 0.63))
                else:
                    amount_confidence = 0.5
            else:
                amount_confidence = 0.5

            # Type consistency
            if types:
                most_common_type = max(set(types), key=types.count)
                type_confidence = types.count(most_common_type) / len(types)
            else:
                most_common_type = 'expense'
                type_confidence = 0.5

            # IMPROVED: Keyword confidence from frequency (not binary)
            if most_common_keyword:
                # 40% frequency → 0.6 confidence
                # 70% frequency → 0.8 confidence
                # 100% frequency → 0.95 confidence
                keyword_confidence = 0.6 + (keyword_frequency * 0.35)
            else:
                keyword_confidence = 0.2

            # IMPROVED: Sample size bonus (up to 10%)
            sample_size_bonus = min(0.1, (len(analysis_txs) - 2) * 0.01)

            # IMPROVED: New weights emphasize consistency
            # Old: (keyword*0.4) + (amount*0.3) + (type*0.3)
            # New: (keyword*0.35) + (type*0.35) + (amount*0.20) + sample_bonus(0.10)
            overall_confidence = (
                (keyword_confidence * 0.35) +
                (type_confidence * 0.35) +
                (amount_confidence * 0.20) +
                sample_size_bonus
            )

            # Cap at 0.99 to avoid overconfidence
            overall_confidence = min(0.99, overall_confidence)

            logger.info(
                f"[{language.upper()}] '{category.name}' (via {strategy_used}): "
                f"confidence={overall_confidence:.2f} "
                f"(keyword={keyword_confidence:.2f}, type={type_confidence:.2f}, amount={amount_confidence:.2f}, samples={len(analysis_txs)})"
            )

            suggestion = {
                'category_id': category.id,
                'category_name': category.name,
                'keyword': most_common_keyword or '',
                'confidence': overall_confidence,
                'transaction_count': len(analysis_txs),
                'strategy': strategy_used,
            }
            suggestions.append(suggestion)

            # Create rule if confidence exceeds threshold
            if overall_confidence > confidence_threshold:
                logger.info(
                    f"[{language.upper()}] Creating rule: '{category.name}' "
                    f"(confidence={overall_confidence:.2f}, strategy={strategy_used})"
                )

                from .models import Rule

                # Build conditions JSONField
                conditions = {}
                if most_common_keyword:
                    conditions['description_contains'] = most_common_keyword
                if type_confidence > 0.6:
                    conditions['type'] = most_common_type

                rule = Rule.objects.create(
                    user_id=user_id,
                    name=f"Auto: {category.name}",
                    category=category,
                    conditions=conditions,
                    priority=int((overall_confidence * 100)),
                    active=True,
                )

                logger.info(f"[{language.upper()}] Rule created: {rule.name} (ID={rule.id})")
                created_rules.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'category': category.name,
                    'confidence': overall_confidence,
                    'strategy': strategy_used,
                })
            else:
                logger.debug(
                    f"[{language.upper()}] Confidence {overall_confidence:.2f} < {confidence_threshold}. Skipping."
                )

        result = {
            'suggestions_count': len(suggestions),
            'created_count': len(created_rules),
            'insufficient_data': False,
            'created_rules': created_rules,
        }

        logger.info(
            f"[{language.upper()}] ✓ COMPLETE: {len(suggestions)} analyzed, {len(created_rules)} rules created"
        )
        return result

    except Exception as e:
        logger.error(f"[ERROR] Rule generation failed for user {user_id}: {str(e)}", exc_info=True)
        raise


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def fetch_exchange_rates_task(self):
    """
    Fetch USD-based exchange rates from OpenExchangeRates API hourly.

    Stores rates in ExchangeRate model with last_updated timestamp.
    If API fails, continues working with cached rates (graceful degradation).

    Environment Variables:
    - API_OPEN_EXCHANGE_RATES_KEY_URL: Full URL to OpenExchangeRates API with app_id
    - SYSTEM_DEFAULT_CURRENCY: Fallback currency if user's currency not in rates
    """
    import requests
    from django.conf import settings

    logger.info("Starting fetch_exchange_rates_task")

    try:
        api_url = settings.API_OPEN_EXCHANGE_RATES_KEY_URL
        if not api_url:
            logger.error("API_OPEN_EXCHANGE_RATES_KEY_URL not configured")
            return {"success": False, "error": "API URL not configured"}

        # Fetch rates from API
        logger.info(f"Fetching exchange rates from {api_url[:50]}...")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract rates (API returns {"rates": {"EUR": 0.92, ...}})
        rates = data.get("rates", {})

        if not rates:
            logger.warning("API returned empty rates object")
            return {"success": False, "error": "Empty rates in API response"}

        # Update or create ExchangeRate record
        from .models import ExchangeRate
        from django.utils import timezone

        rate_obj, created = ExchangeRate.objects.update_or_create(
            pk=1,
            defaults={
                'rates': rates,
                'last_updated': timezone.now(),
                'api_url': api_url[:500],  # Store URL for reference
                'error_message': '',  # Clear any previous error
            }
        )

        logger.info(f"Exchange rates updated successfully. {len(rates)} currencies cached. "
                   f"Updated: {rate_obj.last_updated}")

        return {
            "success": True,
            "currencies_count": len(rates),
            "timestamp": rate_obj.last_updated.isoformat(),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")

        # Update error message but keep existing rates
        from .models import ExchangeRate
        try:
            rate_obj = ExchangeRate.get_rates()
            rate_obj.error_message = str(e)
            rate_obj.save(update_fields=['error_message'])
            logger.info("Error logged, keeping cached rates")
        except Exception as save_err:
            logger.error(f"Failed to update error message: {save_err}")

        return {
            "success": False,
            "error": str(e),
            "using_cached_rates": True,
        }

    except Exception as e:
        logger.error(f"Unexpected error in fetch_exchange_rates_task: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }

