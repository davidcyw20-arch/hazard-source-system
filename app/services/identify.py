from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ..models import (
    GB_18218_2018,
    AlphaRule,
    CategoryBeta,
    CategoryThreshold,
    LevelRule,
    RuleSet,
    StorageRecord,
)
from .evaluation import pick_level


@dataclass(frozen=True)
class Gb18218Result:
    gb_version: str
    enterprise_name: str
    exposure_people_500m: int
    alpha_used: float
    s_value: float
    r_value: float
    is_major_hazard: bool
    level_by_gb: str | None
    level_compat: str | None
    basis: dict[str, Any]


def _alpha_by_people(gb_version: str, people: int) -> float:
    rule = (
        AlphaRule.query.filter_by(gb_version=gb_version)
        .filter(AlphaRule.min_people <= people)
        .filter((AlphaRule.max_people.is_(None)) | (people <= AlphaRule.max_people))
        .order_by(AlphaRule.min_people.desc())
        .first()
    )
    return float(rule.alpha) if rule else 1.0


def _level_by_r(gb_version: str, r_value: float) -> str | None:
    rule = (
        LevelRule.query.filter_by(gb_version=gb_version)
        .filter(LevelRule.min_r <= r_value)
        .filter((LevelRule.max_r.is_(None)) | (r_value <= LevelRule.max_r))
        .order_by(LevelRule.min_r.desc())
        .first()
    )
    return str(rule.level) if rule else None


def _beta_for_symbol(gb_version: str, symbol: str | None) -> tuple[float | None, str | None]:
    if not symbol:
        return None, None
    row = CategoryBeta.query.filter_by(gb_version=gb_version, category_symbol=symbol).first()
    if not row:
        return None, None
    return float(row.beta), row.beta_source or row.source


def _threshold_for_symbol(gb_version: str, symbol: str | None) -> tuple[float | None, str | None, str | None]:
    if not symbol:
        return None, None, None
    row = CategoryThreshold.query.filter_by(gb_version=gb_version, category_symbol=symbol).first()
    if not row:
        return None, None, None
    return float(row.threshold_quantity), row.unit, row.source


def identify_gb18218(
    *,
    enterprise_name: str,
    records: list[StorageRecord],
    exposure_people_500m: int,
    gb_version: str = GB_18218_2018,
    rule_set: RuleSet | None = None,
) -> Gb18218Result:
    people = max(int(exposure_people_500m), 0)
    alpha_used = _alpha_by_people(gb_version, people)

    unit_groups: dict[tuple[str, str], list[StorageRecord]] = defaultdict(list)
    for rec in records:
        unit_name = (rec.unit_name or rec.location or "默认单元").strip()[:120]
        unit_type = (rec.unit_type or "").strip()[:50]
        unit_groups[(unit_type, unit_name)].append(rec)

    units_out: list[dict[str, Any]] = []
    max_r = 0.0
    max_s = 0.0
    max_level_by_gb: str | None = None
    max_level_compat: str | None = None
    max_major = False

    for (unit_type, unit_name), unit_records in unit_groups.items():
        items: list[dict[str, Any]] = []
        s_unit = 0.0
        r_raw = 0.0

        for rec in unit_records:
            chemical = rec.chemical
            is_mixture = (rec.material_type or "").lower() == "mixture"
            category_symbol = (
                (rec.mixture_category_symbol or "").strip() if is_mixture else (chemical.hazard_category_symbol or "").strip()
            ) or None

            qi = float(rec.amount)
            qi_unit = rec.unit

            threshold = float(chemical.critical_quantity)
            threshold_unit = chemical.unit
            threshold_source = chemical.source_standard

            if is_mixture and category_symbol:
                cat_threshold, cat_unit, cat_source = _threshold_for_symbol(gb_version, category_symbol)
                if cat_threshold:
                    threshold = float(cat_threshold)
                    threshold_unit = cat_unit or threshold_unit
                    threshold_source = cat_source or threshold_source

            ratio = qi / threshold if threshold > 0 else 0.0
            s_unit += ratio

            beta = chemical.beta
            beta_source = chemical.beta_source
            if beta is None:
                cat_beta, cat_beta_source = _beta_for_symbol(gb_version, category_symbol)
                beta = cat_beta if cat_beta is not None else 1.0
                beta_source = cat_beta_source
            beta = float(beta)

            contribution = beta * ratio
            r_raw += contribution

            items.append(
                {
                    "chemical": chemical.name,
                    "category": chemical.category,
                    "cas_no": chemical.cas_no,
                    "material_type": "mixture" if is_mixture else "single",
                    "mixture_name": rec.mixture_name,
                    "hazard_category_symbol": category_symbol,
                    "qi": qi,
                    "qi_unit": qi_unit,
                    "Qi": threshold,
                    "Qi_unit": threshold_unit,
                    "Qi_source": threshold_source,
                    "ratio": ratio,
                    "beta": beta,
                    "beta_source": beta_source,
                    "contribution": contribution,
                    "unit_name": unit_name,
                    "unit_type": unit_type,
                    "qty_basis": rec.qty_basis,
                    "location": rec.location,
                    "storage_method": rec.storage_method,
                }
            )

        r_unit = alpha_used * r_raw
        is_major = s_unit >= 1.0
        level_by_gb = _level_by_r(gb_version, r_unit) if is_major else "非重大危险源"
        level_compat = pick_level(rule_set, r_unit) if (rule_set and is_major) else None

        units_out.append(
            {
                "unit_type": unit_type or None,
                "unit_name": unit_name,
                "s_value": s_unit,
                "r_raw": r_raw,
                "alpha_used": alpha_used,
                "r_value": r_unit,
                "is_major_hazard": is_major,
                "level_by_gb": level_by_gb,
                "level_compat": level_compat,
                "items": items,
            }
        )

        if r_unit >= max_r:
            max_r = r_unit
            max_level_by_gb = level_by_gb
            max_level_compat = level_compat
        max_s = max(max_s, s_unit)
        max_major = max_major or is_major

    units_out.sort(key=lambda u: float(u.get("r_value", 0)), reverse=True)

    basis = {
        "standard": gb_version,
        "formula_s": "S = Σ(qi / Qi)",
        "formula_r": "R = α × Σ(β × qi / Qi)",
        "table_mapping": {
            "Qi": "表3/表4（临界量）",
            "alpha": "表5（暴露人口α）",
            "beta": "β（可由化学品或类别表提供）",
            "level": "表6（等级判定）",
        },
        "enterprise_name": enterprise_name,
        "exposure_people_500m": people,
        "alpha_used": alpha_used,
        "units": units_out,
        "totals": {
            "s_max": max_s,
            "r_max": max_r,
        },
        "compat_rule_set_levels": rule_set.levels if rule_set else None,
        "note": "本实现提供可配置参数表以对齐 GB 18218-2018；请将标准表格数据录入参数表后使用。",
    }

    return Gb18218Result(
        gb_version=gb_version,
        enterprise_name=enterprise_name,
        exposure_people_500m=people,
        alpha_used=alpha_used,
        s_value=max_s,
        r_value=max_r,
        is_major_hazard=max_major,
        level_by_gb=max_level_by_gb,
        level_compat=max_level_compat,
        basis=basis,
    )
