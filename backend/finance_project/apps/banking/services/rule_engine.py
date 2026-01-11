from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, Any
from ..models import Transaction, Rule, Category


@dataclass
class RuleContext:
    description: str
    amount: Decimal
    date: date
    type: str
    category_id: int | None


class RuleEngine:
    """Apply first-match user rules to a transaction.

    Supported conditions keys: description_contains, amount_min, amount_max, date_from, date_to, type, has_category
    """

    def matches(self, rule: Rule, ctx: RuleContext) -> bool:
        c: Dict[str, Any] = rule.conditions or {}
        if not rule.active:
            return False
        desc = c.get("description_contains")
        if desc and desc.lower() not in (ctx.description or "").lower():
            return False
        amin = c.get("amount_min")
        if amin is not None and ctx.amount < Decimal(str(amin)):
            return False
        amax = c.get("amount_max")
        if amax is not None and ctx.amount > Decimal(str(amax)):
            return False
        dfrom = c.get("date_from")
        if dfrom and ctx.date < date.fromisoformat(dfrom):
            return False
        dto = c.get("date_to")
        if dto and ctx.date > date.fromisoformat(dto):
            return False
        t = c.get("type")
        if t and ctx.type != t:
            return False
        has_cat = c.get("has_category")
        if has_cat is True and not ctx.category_id:
            return False
        if has_cat is False and ctx.category_id:
            return False
        return True

    def apply_rules(self, user_id: int, tx: Transaction) -> bool:
        ctx = RuleContext(
            description=tx.description,
            amount=tx.amount,
            date=tx.date,
            type=tx.type,
            category_id=tx.category_id,
        )
        for rule in Rule.objects.filter(user_id=user_id, active=True).order_by("priority", "id"):
            if self.matches(rule, ctx):
                tx.category_id = rule.category_id
                tx.save(update_fields=["category"])
                return True
        return False

