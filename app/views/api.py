from __future__ import annotations

from dataclasses import asdict, dataclass

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ..extensions import db
from ..models import (
    GB_18218_2018,
    AlphaRule,
    CategoryBeta,
    CategoryThreshold,
    Chemical,
    EvaluationResult,
    RuleSet,
    StorageRecord,
)
from ..services.identify import identify_gb18218
from ..utils.decorators import admin_required

bp = Blueprint("api", __name__, url_prefix="/api/v1")


@dataclass(frozen=True)
class AlphaRuleHit:
    id: int
    min_people: int
    max_people: int | None
    alpha: float
    source: str
    note: str | None


def _json_error(message: str, *, status: int = 400):
    return jsonify({"error": message}), status


def _to_int(v, *, default: int | None = None) -> int | None:
    if v is None or v == "":
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return default
        if f.is_integer():
            return int(f)
        return default


def _to_float(v, *, default: float | None = None) -> float | None:
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _pick_alpha_rule(gb_version: str, people: int) -> AlphaRuleHit | None:
    rule = (
        AlphaRule.query.filter_by(gb_version=gb_version)
        .filter(AlphaRule.min_people <= people)
        .filter((AlphaRule.max_people.is_(None)) | (people <= AlphaRule.max_people))
        .order_by(AlphaRule.min_people.desc())
        .first()
    )
    if not rule:
        return None
    return AlphaRuleHit(
        id=int(rule.id),
        min_people=int(rule.min_people),
        max_people=int(rule.max_people) if rule.max_people is not None else None,
        alpha=float(rule.alpha),
        source=str(rule.source),
        note=str(rule.note) if rule.note else None,
    )


def _beta_for_symbol(gb_version: str, symbol: str | None) -> tuple[float | None, str | None]:
    if not symbol:
        return None, None
    row = CategoryBeta.query.filter_by(gb_version=gb_version, category_symbol=symbol).first()
    if not row:
        return None, None
    return float(row.beta), row.beta_source or row.source


def _threshold_for_symbol(
    gb_version: str, symbol: str | None
) -> tuple[float | None, str | None, str | None]:
    if not symbol:
        return None, None, None
    row = CategoryThreshold.query.filter_by(gb_version=gb_version, category_symbol=symbol).first()
    if not row:
        return None, None, None
    return float(row.threshold_quantity), row.unit, row.source


@bp.get("/chemicals")
@login_required
def chemicals():
    q = request.args.get("q", "").strip()
    query = Chemical.query
    if q:
        query = query.filter(Chemical.name.like(f"%{q}%"))
    items = query.order_by(Chemical.name).limit(200).all()
    return jsonify(
        [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "cas_no": c.cas_no,
                "critical_quantity": c.critical_quantity,
                "unit": c.unit,
                "source_standard": c.source_standard,
                "gb_version": c.gb_version,
                "hazard_category_symbol": c.hazard_category_symbol,
                "beta": c.beta,
                "beta_source": c.beta_source,
            }
            for c in items
        ]
    )


@bp.post("/storage_records/preview")
@login_required
def storage_preview():
    payload = request.get_json(silent=True) or {}

    gb_version = (payload.get("gb_version") or GB_18218_2018).strip() or GB_18218_2018
    enterprise_name = (payload.get("enterprise_name") or "").strip()
    chemical_id = _to_int(payload.get("chemical_id"))
    qty_t = _to_float(payload.get("qty_t"))
    exposed_people = _to_int(payload.get("exposed_people"), default=0)
    is_mixture = bool(payload.get("is_mixture") or False)
    mixture_symbol = (payload.get("mixture_symbol") or "").strip() or None

    unit_name = (payload.get("unit_name") or "").strip() or None
    unit_type = (payload.get("unit_type") or "").strip() or None
    qty_basis = (payload.get("qty_basis") or "").strip() or None
    location = (payload.get("location") or "").strip() or None
    storage_method = (payload.get("storage_method") or "").strip() or None

    warnings: list[dict] = []

    if not enterprise_name:
        return _json_error("企业名称不能为空")
    if chemical_id is None:
        return _json_error("请选择化学品")
    if qty_t is None or qty_t <= 0:
        return _json_error("储存量必须为大于 0 的数值")
    if exposed_people is None or exposed_people < 0:
        return _json_error("暴露人口必须为非负整数")

    chemical = Chemical.query.get(chemical_id)
    if not chemical:
        return _json_error("化学品不存在")

    people = int(exposed_people)
    alpha_hit = _pick_alpha_rule(gb_version, people)
    if not alpha_hit:
        return _json_error("未找到匹配的 α 规则区间（请先维护 α 规则表）")
    alpha = float(alpha_hit.alpha)

    hazard_symbol_used = (
        ((mixture_symbol or (chemical.hazard_category_symbol or "").strip()) if is_mixture else (chemical.hazard_category_symbol or "").strip())
        or None
    )
    if is_mixture and not mixture_symbol:
        warnings.append(
            {"level": "warning", "code": "MIXTURE_SYMBOL_MISSING", "message": "物质类型为混合物时，请填写混合物类别符号（如 J3/W2/W5.3）。"}
        )

    q0 = float(chemical.critical_quantity) if chemical.critical_quantity else 0.0
    q0_unit = chemical.unit or "t"
    q0_source = chemical.source_standard or ""
    q0_source_tag = "CHEMICAL"

    if is_mixture and mixture_symbol:
        cat_q0, cat_unit, cat_source = _threshold_for_symbol(gb_version, mixture_symbol)
        if cat_q0 is not None:
            q0 = float(cat_q0)
            q0_unit = cat_unit or q0_unit
            q0_source = cat_source or q0_source
            q0_source_tag = "CATEGORY_THRESHOLD"
        else:
            warnings.append(
                {"level": "warning", "code": "MIXTURE_THRESHOLD_MISSING", "message": f"未在类别临界量表中找到 {mixture_symbol} 的临界量(Q0)，请先导入表2参数。", "block_submit": True}
            )

    if not q0 or q0 <= 0:
        warnings.append(
            {"level": "warning", "code": "Q0_MISSING", "message": "临界量(Q0)缺失，无法计算；请先维护化学品临界量或类别临界量。", "block_submit": True}
        )

    beta_source = chemical.beta_source
    if chemical.beta is not None:
        beta = float(chemical.beta)
        beta_source = beta_source or "CHEMICAL_SPECIAL"
    else:
        cat_beta, cat_beta_source = _beta_for_symbol(gb_version, hazard_symbol_used)
        if cat_beta is None:
            beta = 1.0
            beta_source = "DEFAULT"
            warnings.append(
                {"level": "warning", "code": "BETA_DEFAULT", "message": "β 未配置，已使用默认值 1.0（可能低估风险），建议完善类别符号/β 参数表。"}
            )
        else:
            beta = float(cat_beta)
            beta_source = cat_beta_source or "CATEGORY_BETA"

    if not hazard_symbol_used:
        warnings.append(
            {"level": "warning", "code": "HAZARD_SYMBOL_MISSING", "message": "该化学品未填写类别符号(hazard_category_symbol)，β 将使用默认值或无法按表4取值。"}
        )

    qi_q0 = float(qty_t) / float(q0) if q0 and q0 > 0 else 0.0

    # Preview should reflect "this input + existing enterprise records"
    records = (
        StorageRecord.query.filter_by(owner_id=current_user.id, enterprise_name=enterprise_name).all()
    )
    draft = StorageRecord(
        owner_id=current_user.id,
        enterprise_name=enterprise_name,
        chemical_id=chemical.id,
        amount=float(qty_t),
        unit="t",
        unit_name=unit_name,
        unit_type=unit_type,
        qty_basis=qty_basis,
        material_type="mixture" if is_mixture else "single",
        mixture_name=(payload.get("mixture_name") or "").strip() or None,
        mixture_category_symbol=mixture_symbol,
        location=location,
        storage_method=storage_method,
        properties=(payload.get("properties") or "").strip() or None,
    )
    draft.chemical = chemical
    records_with_draft = [*records, draft]

    rule_set = RuleSet.query.filter_by(is_active=True).first()
    out = identify_gb18218(
        enterprise_name=enterprise_name,
        records=records_with_draft,
        exposure_people_500m=people,
        gb_version=gb_version,
        rule_set=rule_set,
    )

    blocked = any(bool(w.get("block_submit")) for w in warnings)
    return jsonify(
        {
            "gb_version": gb_version,
            "enterprise_name": enterprise_name,
            "chemical_id": chemical.id,
            "chemical_name": chemical.name,
            "chemical_category": chemical.category,
            "chemical_cas_no": chemical.cas_no,
            "q0": q0,
            "q0_unit": q0_unit,
            "q0_source": q0_source,
            "q0_source_tag": q0_source_tag,
            "beta": beta,
            "beta_source": beta_source,
            "hazard_category_symbol_used": hazard_symbol_used,
            "qty_t": float(qty_t),
            "qi_q0": qi_q0,
            "alpha": alpha,
            "alpha_rule_hit": asdict(alpha_hit) if alpha_hit else None,
            "S": out.s_value,
            "R": out.r_value,
            "judgement": {
                "is_major_hazard": out.is_major_hazard,
                "level_by_gb": out.level_by_gb or ("重大危险源" if out.is_major_hazard else "非重大危险源"),
                "level_compat": out.level_compat,
            },
            "warnings": warnings,
            "blocked": blocked,
        }
    )


@bp.post("/storage_records")
@login_required
def storage_create():
    payload = request.get_json(silent=True) or {}

    enterprise_name = (payload.get("enterprise_name") or "").strip()
    chemical_id = _to_int(payload.get("chemical_id"))
    amount = _to_float(payload.get("amount"))
    if not enterprise_name:
        return _json_error("企业名称不能为空")
    if chemical_id is None:
        return _json_error("请选择化学品")
    if amount is None or amount <= 0:
        return _json_error("储存量必须为大于 0 的数值")

    chemical = Chemical.query.get(chemical_id)
    if not chemical:
        return _json_error("化学品不存在")

    unit = (payload.get("unit") or "t").strip() or "t"
    if unit != "t":
        return _json_error("当前版本仅支持单位 t")

    material_type = (payload.get("material_type") or "").strip()
    is_mixture = material_type.lower() == "mixture" or bool(payload.get("is_mixture") or False)
    mixture_category_symbol = (payload.get("mixture_category_symbol") or "").strip() or None
    if is_mixture and not mixture_category_symbol:
        return _json_error("物质类型为混合物时，必须填写混合物类别符号")

    rec = StorageRecord(
        owner_id=current_user.id,
        enterprise_name=enterprise_name,
        chemical_id=chemical.id,
        amount=float(amount),
        unit="t",
        unit_name=(payload.get("unit_name") or "").strip() or None,
        unit_type=(payload.get("unit_type") or "").strip() or None,
        qty_basis=(payload.get("qty_basis") or "").strip() or None,
        material_type="mixture" if is_mixture else ("single" if material_type else None),
        mixture_name=(payload.get("mixture_name") or "").strip() or None,
        mixture_category_symbol=mixture_category_symbol,
        location=(payload.get("location") or "").strip() or None,
        storage_method=(payload.get("storage_method") or "").strip() or None,
        properties=(payload.get("properties") or "").strip() or None,
    )

    db.session.add(rec)
    db.session.commit()
    return jsonify({"ok": True, "id": rec.id})


@bp.get("/storage")
@login_required
@admin_required
def storage_all():
    items = StorageRecord.query.order_by(StorageRecord.updated_at.desc()).limit(500).all()
    return jsonify(
        [
            {
                "id": r.id,
                "owner_id": r.owner_id,
                "enterprise_name": r.enterprise_name,
                "chemical": r.chemical.name,
                "amount": r.amount,
                "unit": r.unit,
                "location": r.location,
                "storage_method": r.storage_method,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in items
        ]
    )


@bp.get("/results")
@login_required
@admin_required
def results_all():
    items = EvaluationResult.query.order_by(EvaluationResult.created_at.desc()).limit(500).all()
    return jsonify(
        [
            {
                "id": r.id,
                "owner_id": r.owner_id,
                "enterprise_name": r.enterprise_name,
                "r_value": r.r_value,
                "is_major_hazard": r.is_major_hazard,
                "level": r.level,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in items
        ]
    )
