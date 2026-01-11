from finance_project.apps.banking.services.rule_engine import RuleEngine, RuleContext
from decimal import Decimal
from datetime import date


def test_rule_engine_matches_description():
    engine = RuleEngine()
    class R: pass
    r = R(); r.active=True; r.conditions={"description_contains":"uber"}
    ctx = RuleContext(description="Uber ride", amount=Decimal('10.00'), date=date.today(), type='expense', category_id=None)
    assert engine.matches(r, ctx)

