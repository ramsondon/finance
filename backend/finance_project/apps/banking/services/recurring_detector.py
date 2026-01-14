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
        """
        from finance_project.apps.banking.models import Transaction

        # Get transactions from the past N days
        start_date = datetime.now().date() - timedelta(days=days_back)
        raw_transactions = Transaction.objects.filter(
            account_id=self.account_id,
            date__gte=start_date,
            type__in=['expense', 'income']  # Don't analyze transfers
        ).order_by('date').values(
            'id', 'date', 'amount', 'description', 'reference', 'reference_number'
        )

        if not raw_transactions:
            return []

        self.transactions = list(raw_transactions)

        # Three-pass grouping strategy for improved accuracy:
        # 1. Primary: Group by reference_number (bank's actual transaction ID)
        # 2. Secondary: Group by reference text (textual reference/Verwendungszweck)
        # 3. Tertiary: Group by normalized description (fuzzy matching fallback)

        grouped = self._group_by_reference_number()

        # For transactions without reference_number, try grouping by reference text
        ungrouped = [t for t in self.transactions if t not in self._get_all_grouped_txs(grouped)]
        if ungrouped:
            grouped_by_ref = self._group_by_reference_text(ungrouped)
            grouped.update(grouped_by_ref)
            ungrouped = [t for t in ungrouped if t not in self._get_all_grouped_txs(grouped_by_ref)]

        # For remaining transactions, fall back to description matching
        if ungrouped:
            grouped_by_desc = self._group_by_description(ungrouped)
            grouped.update(grouped_by_desc)

        # Detect patterns in each group
        for group_key, transactions in grouped.items():
            if len(transactions) < 2:
                continue

            patterns = self._find_patterns_in_group(group_key, transactions)
            self.patterns.extend(patterns)

        # Sort by confidence and return
        self.patterns.sort(key=lambda p: (p.confidence_score, p.occurrence_count), reverse=True)
        return self.patterns

    def _get_all_grouped_txs(self, grouped: Dict) -> List[Dict]:
        """Extract all transactions from grouped dict."""
        all_txs = []
        for txs in grouped.values():
            all_txs.extend(txs)
        return all_txs

    def _group_by_reference_number(self) -> Dict[str, List[Dict]]:
        """
        Primary grouping: Group by reference_number (bank's transaction ID).

        This is the most accurate method as reference_number uniquely identifies
        a transaction from the bank's perspective. Identical reference_numbers
        across different dates indicate duplicates or recurring patterns.
        This is the first pass because it's the most reliable.
        """
        grouped = defaultdict(list)

        for tx in self.transactions:
            ref_num = tx.get('reference_number', '').strip()
            if ref_num:
                grouped[f"ref_num:{ref_num}"].append(tx)

        # Only return groups with 2+ occurrences
        return {k: v for k, v in grouped.items() if len(v) >= 2}

    def _group_by_reference_text(self, transactions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Secondary grouping: Group by reference text (Verwendungszweck).

        The reference field contains the textual reference/purpose from the bank.
        Similar reference texts indicate the same merchant or service.
        This is more reliable than description matching as reference is provided by the bank.
        """
        grouped = defaultdict(list)
        processed_indices = set()

        for i, tx in enumerate(transactions):
            if i in processed_indices:
                continue

            reference = tx.get('reference', '').strip().lower()
            if not reference:
                continue

            group = [tx]
            processed_indices.add(i)

            # Find similar references
            for j in range(i + 1, len(transactions)):
                if j in processed_indices:
                    continue

                other_ref = transactions[j].get('reference', '').strip().lower()
                if not other_ref:
                    continue

                if self._references_match(reference, other_ref):
                    group.append(transactions[j])
                    processed_indices.add(j)

            if len(group) >= 2:
                grouped[f"ref:{reference[:50]}"] = group

        return {k: v for k, v in grouped.items() if len(v) >= 2}

    def _references_match(self, ref1: str, ref2: str) -> bool:
        """Check if two reference texts likely represent the same merchant/service."""
        if ref1 == ref2:
            return True

        # Exact match is best
        if ref1 in ref2 or ref2 in ref1:
            return True

        # Check word overlap (at least 60% for reference matching - higher than description)
        words1 = set(ref1.split())
        words2 = set(ref2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap >= 0.6

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
        transactions: List[Dict]
    ) -> List[RecurringPattern]:
        """
        Find recurring patterns in a group of similar transactions.
        """
        patterns = []

        # Sort by date
        transactions = sorted(transactions, key=lambda t: t['date'])

        # Try to find patterns with different intervals
        for frequency, expected_days in self.FREQUENCY_DAYS.items():
            pattern = self._detect_pattern(
                description,
                transactions,
                frequency,
                expected_days
            )

            if pattern:
                patterns.append(pattern)

        return patterns

    def _detect_pattern(
        self,
        description: str,
        transactions: List[Dict],
        frequency: str,
        expected_days: int
    ) -> Optional[RecurringPattern]:
        """
        Try to detect a recurring pattern with a specific frequency.
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
            if abs(a - avg_amount) / avg_amount <= self.AMOUNT_TOLERANCE
        ]

        if len(amount_variance) < len(amounts) * 0.7:  # At least 70% should match
            return None

        # Calculate confidence score
        interval_consistency = len(valid_intervals) / len(intervals) if intervals else 0
        amount_consistency = len(amount_variance) / len(amounts) if amounts else 0
        occurrence_ratio = len(transactions) / self.MIN_OCCURRENCES[frequency]

        confidence = (
            interval_consistency * 0.5 +
            amount_consistency * 0.3 +
            min(occurrence_ratio, 1.0) * 0.2
        )

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

