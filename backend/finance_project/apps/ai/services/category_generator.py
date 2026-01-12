"""
Category Generator Service using AI to automatically create categories from transaction data.
"""
from __future__ import annotations
from typing import List, Dict, Any, Set


class CategoryGeneratorService:
    """
    Analyzes transaction descriptions and patterns to suggest/create categories.
    Uses AI provider for intelligent categorization when available.
    """

    def __init__(self, provider=None):
        """
        Args:
            provider: Optional AI provider (Ollama/Mock) for enhanced categorization
        """
        self.provider = provider

    def analyze_transactions(self, user_id: int, language: str = 'en') -> List[Dict[str, Any]]:
        """
        Analyze user's transactions and suggest categories.

        Args:
            user_id: User ID
            language: Language code ('en', 'de', etc.) for AI-generated category names

        Returns:
            List of suggested categories with metadata:
            [
                {
                    'name': 'Groceries',
                    'color': '#22c55e',
                    'confidence': 0.85,
                    'transaction_count': 45,
                    'keywords': ['supermarket', 'grocery', 'food']
                }
            ]
        """
        from ...banking.models import Transaction, Category

        # Get all transactions for user (uncategorized or all)
        transactions = Transaction.objects.filter(
            account__user_id=user_id
        ).values('description', 'amount', 'type', 'partner_name', 'merchant_name')

        if not transactions:
            return []

        # Get existing categories to avoid duplicates
        existing_categories = set(
            Category.objects.filter(user_id=user_id).values_list('name', flat=True)
        )

        # Extract patterns from descriptions
        suggestions = self._extract_category_patterns(transactions, existing_categories)

        # Enhance with AI if provider available
        if self.provider and suggestions:
            suggestions = self._enhance_with_ai(user_id, suggestions, transactions, language)

        return suggestions

    def create_categories(self, user_id: int, suggestions: List[Dict[str, Any]], auto_approve: bool = False) -> List[Dict[str, Any]]:
        """
        Create categories from suggestions.

        Args:
            user_id: User ID
            suggestions: List of category suggestions
            auto_approve: If True, automatically create all suggestions with confidence > 0.7

        Returns:
            List of created categories with success status
        """
        from ...banking.models import Category

        created = []

        for suggestion in suggestions:
            # Auto-approve high confidence suggestions or if flag is set
            if auto_approve and suggestion.get('confidence', 0) < 0.7:
                continue

            try:
                category, is_new = Category.objects.get_or_create(
                    user_id=user_id,
                    name=suggestion['name'],
                    defaults={'color': suggestion.get('color', self._default_color())}
                )

                created.append({
                    'name': category.name,
                    'color': category.color,
                    'created': is_new,
                    'id': category.id
                })
            except Exception as e:
                created.append({
                    'name': suggestion['name'],
                    'error': str(e),
                    'created': False
                })

        return created

    def _extract_category_patterns(self, transactions, existing_categories: Set[str]) -> List[Dict[str, Any]]:
        """
        Extract category patterns from transaction descriptions using keyword analysis.
        """
        # Common category patterns with keywords and colors
        patterns = {
            'Groceries': {
                'keywords': ['supermarket', 'grocery', 'lebensmittel', 'market', 'food', 'edeka', 'rewe', 'aldi', 'lidl', 'hofer', 'billa', 'spar'],
                'color': '#22c55e'
            },
            'Restaurants': {
                'keywords': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald', 'burger', 'pizza', 'kebab', 'bistro', 'bar'],
                'color': '#f97316'
            },
            'Transportation': {
                'keywords': ['uber', 'taxi', 'fuel', 'gas', 'tankstelle', 'parking', 'train', 'bus', 'railway', 'metro', 'oebb', 'db bahn'],
                'color': '#3b82f6'
            },
            'Shopping': {
                'keywords': ['amazon', 'ebay', 'shop', 'store', 'retail', 'kaufhaus', 'online'],
                'color': '#ec4899'
            },
            'Entertainment': {
                'keywords': ['netflix', 'spotify', 'cinema', 'kino', 'theater', 'concert', 'ticket', 'event'],
                'color': '#8b5cf6'
            },
            'Utilities': {
                'keywords': ['electric', 'strom', 'gas', 'water', 'wasser', 'internet', 'phone', 'telekom', 'vodafone'],
                'color': '#eab308'
            },
            'Healthcare': {
                'keywords': ['pharmacy', 'apotheke', 'doctor', 'arzt', 'hospital', 'krankenhaus', 'medical', 'health'],
                'color': '#ef4444'
            },
            'Subscriptions': {
                'keywords': ['subscription', 'membership', 'abo', 'monthly fee', 'jahresbeitrag'],
                'color': '#06b6d4'
            },
            'Salary': {
                'keywords': ['salary', 'gehalt', 'lohn', 'wage', 'payment', 'income'],
                'color': '#10b981'
            },
            'ATM': {
                'keywords': ['atm', 'cash', 'withdrawal', 'bankomat', 'geldautomat', 'abhebung'],
                'color': '#64748b'
            }
        }

        # Count matches for each pattern
        pattern_matches = {}

        for transaction in transactions:
            description = (transaction.get('description') or '').lower()
            partner = (transaction.get('partner_name') or '').lower()
            merchant = (transaction.get('merchant_name') or '').lower()

            combined_text = f"{description} {partner} {merchant}"

            for category_name, pattern in patterns.items():
                # Skip if category already exists
                if category_name in existing_categories:
                    continue

                # Check if any keyword matches
                for keyword in pattern['keywords']:
                    if keyword.lower() in combined_text:
                        if category_name not in pattern_matches:
                            pattern_matches[category_name] = {
                                'count': 0,
                                'keywords': set(),
                                'color': pattern['color']
                            }
                        pattern_matches[category_name]['count'] += 1
                        pattern_matches[category_name]['keywords'].add(keyword)
                        break

        # Convert to suggestions (min 3 transactions to suggest)
        suggestions = []
        total_transactions = len(transactions)

        for category_name, data in pattern_matches.items():
            if data['count'] >= 3:
                confidence = min(0.95, data['count'] / total_transactions * 5)  # Scale confidence
                suggestions.append({
                    'name': category_name,
                    'color': data['color'],
                    'confidence': round(confidence, 2),
                    'transaction_count': data['count'],
                    'keywords': list(data['keywords'])[:5]  # Top 5 keywords
                })

        # Sort by transaction count (most common first)
        suggestions.sort(key=lambda x: x['transaction_count'], reverse=True)

        return suggestions

    def _enhance_with_ai(self, user_id: int, suggestions: List[Dict], transactions, language: str = 'en') -> List[Dict]:
        """
        Use AI provider (Ollama GEMMA3) to generate intelligent category suggestions
        based on transaction descriptions and income/expense types.

        Args:
            user_id: User ID
            suggestions: Pattern-based suggestions to enhance
            transactions: Transaction data
            language: Language code for AI-generated category names
        """
        if not self.provider:
            return suggestions

        try:
            # Prepare transaction data for AI analysis
            transaction_samples = []
            for tx in transactions[:200]:  # Analyze up to 200 transactions
                description = tx.get('description', '') or ''
                amount = tx.get('amount', 0)
                tx_type = tx.get('type', 'expense')

                # Determine if income or expense based on amount and type
                direction = 'income' if (amount > 0 or tx_type == 'income') else 'expense'

                transaction_samples.append({
                    'description': description[:500],  # Limit length
                    'type': direction
                })

            # Build prompt for Ollama with language specification
            prompt = self._build_ai_prompt(transaction_samples, suggestions, language)

            # Call Ollama provider
            ai_result = self._call_ollama(prompt)

            # Parse AI response and merge with pattern-based suggestions
            ai_suggestions = self._parse_ai_categories(ai_result)

            # Merge AI suggestions with pattern-based ones (avoid duplicates)
            merged = self._merge_suggestions(suggestions, ai_suggestions)

            return merged

        except Exception as e:
            # Log but don't fail - fallback to pattern-based suggestions
            import logging
            logging.warning(f"AI enhancement failed: {e}, using pattern-based suggestions")
            return suggestions

    def _build_ai_prompt(self, transaction_samples: List[Dict], existing_suggestions: List[Dict], language: str = 'en') -> str:
        """
        Build a structured prompt for Ollama to generate categories in the specified language.

        Args:
            transaction_samples: Sample transactions to analyze
            existing_suggestions: Existing pattern-based suggestions
            language: Language code ('en', 'de', etc.)
        """
        lang_instruction = self._get_language_instruction(language)

        prompt = f"""Analyze these financial transactions and suggest meaningful categories for organizing them.

{lang_instruction}

Sample transactions:
"""
        for i, tx in enumerate(transaction_samples[:30], 1):
            prompt += f"{i}. [{tx['type'].upper()}] {tx['description']}\n"

        prompt += f"""

Current pattern-based suggestions: {', '.join([s['name'] for s in existing_suggestions[:10]])}

Based on the transaction descriptions and types (income/expense), suggest 5-10 additional meaningful categories that would help organize these transactions. 

For each category, provide:
- Category name (concise, 1-2 words)
- A brief reason why this category is useful

Format your response as:
CATEGORY: <name>
REASON: <brief explanation>

Focus on practical categories that reflect the user's actual spending and income patterns."""

        return prompt

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama service directly for category generation."""
        import requests
        import os
        import logging

        logger = logging.getLogger(__name__)

        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ollama_model = os.environ.get("OLLAMA_MODEL", "gemma2")

        try:
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )

            if response.ok:
                data = response.json()
                return data.get("response", "")
            elif response.status_code == 404:
                # Model not found - provide helpful error message
                logger.error(
                    f"Ollama model '{ollama_model}' not found. "
                    f"Please pull the model first: docker compose exec ollama ollama pull {ollama_model}"
                )
                raise Exception(
                    f"Model '{ollama_model}' not found. Pull it with: ollama pull {ollama_model}"
                )
            else:
                error_detail = response.text[:200] if response.text else "Unknown error"
                raise Exception(f"Ollama API error {response.status_code}: {error_detail}")

        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Cannot connect to Ollama at {ollama_host}. Is the service running?")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Ollama request timed out after 30 seconds")
        except Exception as e:
            if "Model" in str(e) and "not found" in str(e):
                raise  # Re-raise our custom 404 message
            raise Exception(f"Failed to call Ollama: {e}")

    def _parse_ai_categories(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract category suggestions."""
        categories = []
        lines = ai_response.split('\n')

        current_category = None
        current_reason = None

        for line in lines:
            line = line.strip()
            if line.startswith('CATEGORY:'):
                if current_category:
                    # Save previous category
                    categories.append({
                        'name': current_category.strip("*"),
                        'color': self._default_color(),
                        'confidence': 0.75,  # AI-generated have medium-high confidence
                        'transaction_count': 0,  # Unknown from AI
                        'keywords': [],
                        'source': 'ai'
                    })
                current_category = line.replace('CATEGORY:', '').strip()
                current_reason = None
            elif line.startswith('REASON:'):
                current_reason = line.replace('REASON:', '').strip()

        # Don't forget the last category
        if current_category:
            categories.append({
                'name': current_category,
                'color': self._default_color(),
                'confidence': 0.75,
                'transaction_count': 0,
                'keywords': [],
                'source': 'ai'
            })

        return categories

    def _merge_suggestions(self, pattern_based: List[Dict], ai_based: List[Dict]) -> List[Dict]:
        """Merge pattern-based and AI-based suggestions, avoiding duplicates."""
        merged = list(pattern_based)  # Start with pattern-based (higher priority)

        # Get existing category names (case-insensitive)
        existing_names = {s['name'].lower() for s in pattern_based}

        # Add AI suggestions that don't duplicate
        for ai_cat in ai_based:
            if ai_cat['name'].lower() not in existing_names:
                merged.append(ai_cat)
                existing_names.add(ai_cat['name'].lower())

        return merged

    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction for AI category generation."""
        language_instructions = {
            'en': 'Generate category names in English. Use simple, clear category names.',
            'de': 'Generiere Kategorienamen auf Deutsch. Verwende einfache, klare Kategorienamen.',
        }
        return language_instructions.get(language, language_instructions['en'])

    def _default_color(self) -> str:
        """Return a random default color."""
        colors = ['#3b82f6', '#22c55e', '#f97316', '#ec4899', '#8b5cf6', '#eab308']
        import random
        return random.choice(colors)

