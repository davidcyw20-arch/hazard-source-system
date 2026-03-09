from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models import RuleSet, StorageRecord


@dataclass(frozen=True)
class EvaluationOutput:
    enterprise_name: str
    r_value: float
    is_major_hazard: bool
    level: str | None
    basis: dict[str, Any]
    rule_set_id: int


def compute_r(records: list[StorageRecord]) -> tuple[float, list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    r_total = 0.0
    for rec in records:
        critical = float(rec.chemical.critical_quantity)
        amount = float(rec.amount)
        ratio = amount / critical if critical > 0 else 0.0
        r_total += ratio
        items.append(
            {
                "chemical": rec.chemical.name,
                "category": rec.chemical.category,
                "cas_no": rec.chemical.cas_no,
                "amount": amount,
                "amount_unit": rec.unit,
                "critical_quantity": critical,
                "critical_unit": rec.chemical.unit,
                "ratio": ratio,
                "location": rec.location,
                "storage_method": rec.storage_method,
            }
        )
    return r_total, items


def pick_level(rule_set: RuleSet, r_value: float) -> str | None:
    for rule in rule_set.levels:
        rule_min = float(rule.get("min", 0))
        rule_max = rule.get("max", None)
        if rule_max is None:
            if r_value >= rule_min:
                return str(rule.get("level"))
        else:
            if r_value >= rule_min and r_value < float(rule_max):
                return str(rule.get("level"))
    return None


def evaluate_enterprise(
    *,
    enterprise_name: str,
    records: list[StorageRecord],
    rule_set: RuleSet,
) -> EvaluationOutput:
    r_value, items = compute_r(records)
    is_major_hazard = r_value >= 1.0
    level = pick_level(rule_set, r_value) if is_major_hazard else None
    basis = {
        "standard": "GB 18218",
        "formula": "R = Σ(Qi / Q0i)",
        "items": items,
        "note": "当 R ≥ 1 判定为重大危险源；等级区间可在管理端维护。",
    }
    return EvaluationOutput(
        enterprise_name=enterprise_name,
        r_value=r_value,
        is_major_hazard=is_major_hazard,
        level=level,
        basis=basis,
        rule_set_id=rule_set.id,
    )
