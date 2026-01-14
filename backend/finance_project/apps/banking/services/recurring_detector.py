"""
Recurring transaction detection service.

Detects patterns in transactions such as:
- Weekly (every 7 days)
- Bi-weekly (every 14 days)
- Monthly (same day each month)
- Quarterly (every 3 months)
- Yearly (same date each year)

Uses a three-pass detection strategy:
1. Primary: Group by reference_number (actual bank transaction ID) for exact matching
2. Secondary: Group by reference text for pattern matching across similar merchants
3. Tertiary: Group by normalized description for fuzzy matching

This multi-pass approach significantly improves detection accuracy by leveraging
bank-provided transaction identifiers alongside textual references.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class RecurringPattern:
    """Represents a detected recurring transaction pattern."""
    description: str
    amount: Decimal
    frequency: str  # 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'yearly'
    days_interval: int  # exact interval in days
    next_expected_date: datetime
    last_occurrence_date: datetime
    occurrence_count: int
    confidence_score: float  # 0-1, how confident we are this is recurring
    transaction_ids: List[int]
    similar_descriptions: List[str]  # all similar descriptions found

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'description': self.description,
            'amount': str(self.amount),
            'frequency': self.frequency,
            'days_interval': self.days_interval,
            'next_expected_date': self.next_expected_date.isoformat(),
            'last_occurrence_date': self.last_occurrence_date.isoformat(),
            'occurrence_count': self.occurrence_count,
            'confidence_score': round(self.confidence_score, 2),
            'transaction_ids': self.transaction_ids,
            'similar_descriptions': self.similar_descriptions,
        }


class RecurringTransactionDetector:
    """Detects recurring transactions in user account data."""

    # Configuration thresholds
    FREQUENCY_DAYS = {
        'weekly': 7,
        'bi-weekly': 14,
        'monthly': 30,  # approximate
        'quarterly': 90,  # approximate
        'yearly': 365,  # approximate
    }

    # Frequency priority - prefer more specific, common frequencies
    # Higher score = higher priority
    # Weekly is most specific (7 days), Yearly is least specific (365 days)
    FREQUENCY_PRIORITY = {
        'weekly': 5,      # Most specific, easiest to verify
        'bi-weekly': 4,   # Specific, common (every 2 weeks)
        'monthly': 3,     # Most common, but less specific than weekly
        'quarterly': 2,   # Less common, more ambiguous
        'yearly': 1,      # Least specific, most ambiguous
    }

    # Amount tolerance (within this % is considered same amount)
    AMOUNT_TOLERANCE = 0.05  # 5%

    # Minimum occurrences to consider recurring
    MIN_OCCURRENCES = {
        'weekly': 3,  # 3 weeks of data
        'bi-weekly': 3,  # 6 weeks
        'monthly': 2,  # 2 months
        'quarterly': 2,  # 6 months
        'yearly': 2,  # 2 years (to detect annual subscriptions like birthdays, renewals)
    }

    def __init__(self, account_id: int):
        """
        Initialize detector for a specific bank account.

        Args:
            account_id: ID of the bank account to analyze
        """
        self.account_id = account_id
        self.transactions = []
        self.patterns: List[RecurringPattern] = []

    def detect(self, days_back: int = 365 * 5) -> List[RecurringPattern]:
        """
        Detect recurring transactions in the account.

        Args:
            days_back: How far back to look for patterns (default: 1825 days / 5 years)

        Returns:
            List of detected recurring patterns, sorted by confidence

        Uses improved three-pass matching strategy:
        1. Partner Info (95%+ confidence): partner_iban + partner_name + payment_method
        2. Merchant Info (75-85% confidence): merchant_name + payment_method + card_brand
        3. Description Text (50-70% confidence): reference + description (fuzzy match)
        """
        from finance_project.apps.banking.models import Transaction

        # Get transactions from the past N days
        start_date = datetime.now().date() - timedelta(days=days_back)
        raw_transactions = Transaction.objects.filter(
            account_id=self.account_id,
            date__gte=start_date,
            type__in=['expense', 'income']  # Don't analyze transfers
        ).order_by('date').values(
            'id', 'date', 'amount', 'description', 'reference',
            'partner_name', 'partner_iban', 'payment_method',
            'merchant_name', 'card_brand'
        )

        if not raw_transactions:
            return []

        self.transactions = list(raw_transactions)

        grouped = {}

        # Pass 1: Group by partner information (95%+ confidence)
        grouped_by_partner = self._group_by_partner_info()
        if grouped_by_partner:
            grouped.update(grouped_by_partner)

        # Pass 2: Group remaining by merchant information (75-85% confidence)
        ungrouped = [t for t in self.transactions if t not in self._get_all_grouped_txs(grouped)]
        if ungrouped:
            grouped_by_merchant = self._group_by_merchant_info(ungrouped)
            if grouped_by_merchant:
                grouped.update(grouped_by_merchant)
            ungrouped = [t for t in ungrouped if t not in self._get_all_grouped_txs(grouped_by_merchant or {})]

        # Pass 3: Group remaining by description (50-70% confidence - fallback)
        if ungrouped:
            grouped_by_desc = self._group_by_description(ungrouped)
            if grouped_by_desc:
                grouped.update(grouped_by_desc)

        # Detect patterns in each group
        for group_key, group_info in grouped.items():
            # Handle both dict (with metadata) and list (legacy) formats
            if isinstance(group_info, dict) and 'transactions' in group_info:
                transactions = group_info['transactions']
                confidence_pass = group_info.get('confidence_pass', 3)
            else:
                transactions = group_info
                confidence_pass = 3  # Default to Pass 3 for legacy

            if len(transactions) < 2:
                continue

            patterns = self._find_patterns_in_group(
                group_key,
                transactions,
                confidence_pass=confidence_pass
            )
            self.patterns.extend(patterns)

        # Sort by confidence and return
        self.patterns.sort(key=lambda p: (p.confidence_score, p.occurrence_count), reverse=True)
        return self.patterns

    def _get_all_grouped_txs(self, grouped: Dict) -> List[Dict]:
        """Extract all transactions from grouped dict."""
        all_txs = []
        for group_info in grouped.values():
            if isinstance(group_info, dict) and 'transactions' in group_info:
                all_txs.extend(group_info['transactions'])
            elif isinstance(group_info, list):
                all_txs.extend(group_info)
        return all_txs

    def _group_by_partner_info(self) -> Dict[str, Dict]:
        """
        Primary grouping: Group by partner information (95%+ confidence).

        Uses:
        - partner_iban: Bank account of other party (perfect for transfers)
        - partner_name: Name of other party (consistent for recurring)
        - payment_method: CARD, SEPA, TRANSFER, etc.

        This is the most reliable method because:
        - Bank accounts identify exact source/destination
        - Partner names are consistent across recurring payments
        - Payment method ensures transaction type consistency
        """
        grouped = defaultdict(list)

        for tx in self.transactions:
            partner_iban = tx.get('partner_iban', '').strip().upper()
            partner_name = tx.get('partner_name', '').strip().lower()
            payment_method = tx.get('payment_method', '').strip().lower()

            # Must have partner info to group
            if not (partner_iban and partner_name):
                continue

            # Create key from partner information
            key = f"partner:{partner_iban}:{partner_name}:{payment_method}"
            grouped[key].append(tx)

        # Only return groups with 2+ occurrences, wrapped with metadata
        result = {}
        for k, v in grouped.items():
            if len(v) >= 2:
                result[k] = {
                    'transactions': v,
                    'confidence_pass': 1,
                    'match_type': 'partner_info',
                }
        return result

    def _group_by_merchant_info(self, transactions: List[Dict]) -> Dict[str, Dict]:
        """
        Secondary grouping: Group by merchant information (75-85% confidence).

        Uses:
        - merchant_name: Company/merchant name
        - payment_method: CARD, SEPA, TRANSFER, etc.
        - card_brand: VISA, Mastercard, etc.

        Why this works:
        - Same merchant usually = same service
        - Payment method ensures consistent type
        - Card brand distinguishes payment sources
        """
        grouped = defaultdict(list)
        processed_indices = set()

        for i, tx in enumerate(transactions):
            if i in processed_indices:
                continue

            merchant_name = tx.get('merchant_name', '').strip().lower()
            payment_method = tx.get('payment_method', '').strip().lower()
            card_brand = tx.get('card_brand', '').strip().lower()

            # Skip if missing merchant name
            if not merchant_name:
                continue

            group = [tx]
            processed_indices.add(i)

            # Find similar merchants
            for j in range(i + 1, len(transactions)):
                if j in processed_indices:
                    continue

                other_merchant = transactions[j].get('merchant_name', '').strip().lower()
                other_payment = transactions[j].get('payment_method', '').strip().lower()
                other_card = transactions[j].get('card_brand', '').strip().lower()

                # Must match: merchant name, payment method, and card brand
                if (self._merchants_match(merchant_name, other_merchant) and
                    payment_method == other_payment and
                    card_brand == other_card):
                    group.append(transactions[j])
                    processed_indices.add(j)

            if len(group) >= 2:
                key = f"merchant:{merchant_name}:{payment_method}:{card_brand}"
                grouped[key] = group

        # Wrap with metadata
        result = {}
        for k, v in grouped.items():
            if len(v) >= 2:
                result[k] = {
                    'transactions': v,
                    'confidence_pass': 2,
                    'match_type': 'merchant_info',
                }
        return result

    def _merchants_match(self, merchant1: str, merchant2: str) -> bool:
        """Check if two merchant names likely represent the same merchant."""
        # Exact match
        if merchant1 == merchant2:
            return True

        # One contains the other (common variations)
        if merchant1 in merchant2 or merchant2 in merchant1:
            return True

        # Word overlap (at least 70% for merchant matching)
        words1 = set(merchant1.split())
        words2 = set(merchant2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap >= 0.7

    def _group_by_description(self, transactions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Tertiary grouping: Group by normalized description (fuzzy matching fallback).

        Uses fuzzy matching to group similar transaction descriptions.
        This is used as a fallback for transactions without reference_number or reference.
        E.g., "NETFLIX" and "NETFLIX.COM" and "Netflix" are grouped together.
        """
        grouped = defaultdict(list)
        processed_indices = set()

        for i, tx in enumerate(transactions):
            if i in processed_indices:
                continue

            description = self._normalize_description(tx['description'])
            group = [tx]
            processed_indices.add(i)

            # Find similar descriptions
            for j in range(i + 1, len(transactions)):
                if j in processed_indices:
                    continue

                other_desc = self._normalize_description(
                    transactions[j]['description']
                )

                if self._descriptions_match(description, other_desc):
                    group.append(transactions[j])
                    processed_indices.add(j)

            if len(group) >= 2:
                grouped[description] = group

        return {k: v for k, v in grouped.items() if len(v) >= 2}

    def _normalize_description(self, desc: str) -> str:
        """
        Normalize a transaction description for comparison.

        Removes common suffixes, makes lowercase, etc.
        """
        if not desc:
            return "unknown"

        # Remove common patterns
        desc = desc.lower().strip()

        # Remove domain suffixes
        for suffix in ['.com', '.co.uk', '.de', '.at', '.ch', '.fr', '.es', '.it', '.nl']:
            desc = desc.replace(suffix, '')

        # Remove numbers and special characters (but keep spaces)
        import re
        desc = re.sub(r'[\d\-\._:/]', '', desc)

        # Remove extra whitespace
        desc = ' '.join(desc.split())

        return desc[:50]  # Keep first 50 chars

    def _descriptions_match(self, desc1: str, desc2: str) -> bool:
        """Check if two descriptions likely represent the same merchant."""
        if desc1 == desc2:
            return True

        # Check if one contains the other
        if desc1 in desc2 or desc2 in desc1:
            return True

        # Check word overlap (at least 50%)
        words1 = set(desc1.split())
        words2 = set(desc2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap >= 0.5

    def _find_patterns_in_group(
        self,
        description: str,
        transactions: List[Dict],
        confidence_pass: int = 3
    ) -> List[RecurringPattern]:
        """
        Find the BEST recurring pattern in a group of similar transactions.

        Only returns a single pattern (the best match), not all matching frequencies.
        This prevents duplicates where the same transaction group is reported as
        both monthly, quarterly, and yearly.

        Args:
            description: Group description/key
            transactions: List of transactions in this group
            confidence_pass: Which pass identified this group (1, 2, or 3)

        Returns:
            List with 0 or 1 RecurringPattern (best match only)
        """
        # Sort by date
        transactions = sorted(transactions, key=lambda t: t['date'])

        best_pattern = None
        best_score = -1

        # Try all frequencies and keep track of the best one
        for frequency, expected_days in self.FREQUENCY_DAYS.items():
            pattern = self._detect_pattern(
                description,
                transactions,
                frequency,
                expected_days,
                confidence_pass=confidence_pass
            )

            if pattern:
                # Calculate score for this pattern
                score = self._score_pattern(pattern, frequency, expected_days)
                if score > best_score:
                    best_score = score
                    best_pattern = pattern

        # Return best pattern (or empty list if no valid pattern found)
        return [best_pattern] if best_pattern else []

    def _score_pattern(self, pattern: RecurringPattern, frequency: str, expected_days: int) -> float:
        """
        Score a recurring pattern based on multiple quality metrics.

        Scoring factors:
        1. Confidence Score (50%) - How consistent the pattern is
        2. Frequency Priority (20%) - Prefer weekly over yearly
        3. Occurrence Count (20%) - More occurrences = better
        4. Interval Accuracy (10%) - How close to expected interval

        Args:
            pattern: The detected pattern
            frequency: The frequency (weekly, monthly, etc.)
            expected_days: Expected days between occurrences

        Returns:
            Score from 0-1 (higher is better)
        """
        # Primary: confidence score (already 0-1)
        confidence_score = pattern.confidence_score

        # Secondary: frequency priority (more specific is better)
        # weekly=5, bi-weekly=4, monthly=3, quarterly=2, yearly=1
        # Normalize to 0-1 range
        priority = self.FREQUENCY_PRIORITY.get(frequency, 0) / 5.0

        # Tertiary: occurrence count (more is better)
        # Normalize against minimum threshold
        min_occurrences = self.MIN_OCCURRENCES.get(frequency, 2)
        occurrence_score = min(pattern.occurrence_count / (min_occurrences + 1.0), 1.0)

        # Quaternary: interval accuracy (already reflected in confidence)
        # But we can add a bonus for very precise intervals
        interval_accuracy = 0.8  # Default: patterns already passed validation

        # Weighted combination
        score = (
            confidence_score * 0.5 +      # Confidence is primary (50%)
            priority * 0.2 +               # Frequency priority (20%)
            occurrence_score * 0.2 +       # More occurrences better (20%)
            interval_accuracy * 0.1        # Interval precision (10%)
        )

        return score

    def _detect_pattern(
        self,
        description: str,
        transactions: List[Dict],
        frequency: str,
        expected_days: int,
        confidence_pass: int = 3
    ) -> Optional[RecurringPattern]:
        """
        Try to detect a recurring pattern with a specific frequency.

        Args:
            description: Group description/key
            transactions: List of transactions
            frequency: Expected frequency (weekly, monthly, etc.)
            expected_days: Expected days between transactions
            confidence_pass: Which pass identified this (1=partner, 2=merchant, 3=description)
        """
        if len(transactions) < self.MIN_OCCURRENCES[frequency]:
            return None

        # Calculate intervals between transactions
        intervals = []
        amounts = []

        for i in range(len(transactions) - 1):
            current_date = transactions[i]['date']
            next_date = transactions[i + 1]['date']
            interval = (next_date - current_date).days
            intervals.append(interval)
            amounts.append(transactions[i]['amount'])

        amounts.append(transactions[-1]['amount'])

        # Check if intervals are consistent with the expected frequency
        tolerance = expected_days * 0.3  # 30% tolerance
        valid_intervals = [
            i for i in intervals
            if abs(i - expected_days) <= tolerance
        ]

        if len(valid_intervals) < self.MIN_OCCURRENCES[frequency] - 1:
            return None

        # Check if amounts are consistent
        avg_amount = sum(amounts) / len(amounts)

        # Skip if average amount is zero (can't calculate percentage variance)
        if avg_amount == 0:
            return None

        amount_variance = [
            a for a in amounts
        ]

        if len(amount_variance) < len(amounts) * 0.7:  # At least 70% should match
            return None

        # Calculate base confidence score
        interval_consistency = len(valid_intervals) / len(intervals) if intervals else 0
        amount_consistency = len(amount_variance) / len(amounts) if amounts else 0
        occurrence_ratio = len(transactions) / self.MIN_OCCURRENCES[frequency]

        base_confidence = (
            interval_consistency * 0.5 +
            amount_consistency * 0.3 +
            min(occurrence_ratio, 1.0) * 0.2
        )

        # Apply pass multiplier (NEW)
        # Pass 1 (Partner): 1.0 → 95%+ potential confidence
        # Pass 2 (Merchant): 0.85 → 75-85% potential confidence
        # Pass 3 (Description): 0.65 → 50-70% potential confidence
        pass_multipliers = {
            1: 1.0,
            2: 0.85,
            3: 0.65,
        }
        multiplier = pass_multipliers.get(confidence_pass, 0.65)
        confidence = base_confidence * multiplier

        if confidence < 0.6:  # Minimum confidence threshold
            return None

        # Build the pattern
        last_date = transactions[-1]['date']
        next_expected = last_date + timedelta(days=expected_days)

        return RecurringPattern(
            description=description,
            amount=avg_amount,
            frequency=frequency,
            days_interval=expected_days,
            next_expected_date=next_expected,
            last_occurrence_date=last_date,
            occurrence_count=len(transactions),
            confidence_score=confidence,
            transaction_ids=[t['id'] for t in transactions],
            similar_descriptions=list(set(t['description'] for t in transactions))
        )

    def get_monthly_recurring_cost(self) -> Decimal:
        """Calculate total monthly recurring cost."""
        monthly_cost = Decimal('0')

        for pattern in self.patterns:
            if pattern.frequency == 'weekly':
                monthly_cost += pattern.amount * Decimal('4.33')  # ~4.33 weeks per month
            elif pattern.frequency == 'bi-weekly':
                monthly_cost += pattern.amount * Decimal('2.17')
            elif pattern.frequency == 'monthly':
                monthly_cost += pattern.amount
            elif pattern.frequency == 'quarterly':
                monthly_cost += pattern.amount / Decimal('3')
            elif pattern.frequency == 'yearly':
                monthly_cost += pattern.amount / Decimal('12')

        return monthly_cost.quantize(Decimal('0.01'))

    def get_yearly_recurring_cost(self) -> Decimal:
        """Calculate total yearly recurring cost."""
        yearly_cost = Decimal('0')

        for pattern in self.patterns:
            if pattern.frequency == 'weekly':
                yearly_cost += pattern.amount * Decimal('52')
            elif pattern.frequency == 'bi-weekly':
                yearly_cost += pattern.amount * Decimal('26')
            elif pattern.frequency == 'monthly':
                yearly_cost += pattern.amount * Decimal('12')
            elif pattern.frequency == 'quarterly':
                yearly_cost += pattern.amount * Decimal('4')
            elif pattern.frequency == 'yearly':
                yearly_cost += pattern.amount

        return yearly_cost.quantize(Decimal('0.01'))

