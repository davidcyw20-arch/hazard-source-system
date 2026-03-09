from __future__ import annotations

import io
from datetime import datetime
import json

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import ChemicalForm, RuleSetForm, UserAdminForm
from ..models import Chemical, EvaluationResult, RuleSet, StorageRecord, User
from ..services.backup import (
    dumps_json,
    export_db_to_json,
    export_db_to_xlsx,
    import_db_from_json,
    loads_json,
)
from ..services.chemicals import dedup_chemicals_keep_latest
from ..services.gb18218_import import import_gb18218_full_seed_sql, validate_gb18218_full_seed_sql
from ..services.gb18218_params_update import apply_gb18218_table2_table3_table4_updates
from ..utils.audit import log_action
from ..utils.decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@login_required
@admin_required
def dashboard():
    approved_count = EvaluationResult.query.filter_by(status="approved").count()
    rejected_count = EvaluationResult.query.filter_by(status="rejected").count()
    return render_template(
        "admin/dashboard.html",
        user_count=User.query.count(),
        chemical_count=Chemical.query.count(),
        storage_count=StorageRecord.query.count(),
        result_count=EvaluationResult.query.count(),
        pending_count=EvaluationResult.query.filter_by(status="pending").count(),
        approved_count=approved_count,
        rejected_count=rejected_count,
        server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@bp.get("/users")
@login_required
@admin_required
def users_list():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(User.username.like(f"%{q}%"))
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users_list.html", users=users, q=q)


@bp.get("/users/<int:user_id>/edit")
@bp.post("/users/<int:user_id>/edit")
@login_required
@admin_required
def users_edit(user_id: int):
    user = User.query.get_or_404(user_id)
    form = UserAdminForm(obj=user)
    is_protected_admin_self = user.username == "admin" and user.id == current_user.id
    if form.validate_on_submit():
        if is_protected_admin_self:
            # Protect the built-in admin account from locking itself out.
            user.role = "admin"
            user.is_active = True
        else:
            user.role = form.role.data
            user.is_active = bool(form.is_active.data)
        if form.reset_password.data:
            user.set_password(form.reset_password.data)
        db.session.commit()
        log_action("admin_user_update", f"user_id={user_id}")
        if is_protected_admin_self:
            flash("admin 账号不能修改自身角色或停用自身账号（已强制保持管理员且启用）", "warning")
        flash("已保存", "success")
        return redirect(url_for("admin.users_list"))
    if request.method == "GET":
        form.is_active.data = user.is_active
    return render_template(
        "admin/users_edit.html",
        form=form,
        user=user,
        is_protected_admin_self=is_protected_admin_self,
    )


@bp.get("/chemicals")
@login_required
@admin_required
def chemicals_list():
    q = request.args.get("q", "").strip()
    query = Chemical.query
    if q:
        query = query.filter((Chemical.name.like(f"%{q}%")) | (Chemical.cas_no.like(f"%{q}%")))
    chemicals = query.order_by(Chemical.name).all()
    chemical_ids = [c.id for c in chemicals]
    usage_counts: dict[int, int] = {}
    if chemical_ids:
        rows = (
            db.session.query(StorageRecord.chemical_id, func.count(StorageRecord.id))
            .filter(StorageRecord.chemical_id.in_(chemical_ids))
            .group_by(StorageRecord.chemical_id)
            .all()
        )
        usage_counts = {int(cid): int(cnt) for cid, cnt in rows}
    return render_template(
        "admin/chemicals_list.html",
        chemicals=chemicals,
        q=q,
        usage_counts=usage_counts,
    )


@bp.post("/chemicals/import-gb18218")
@login_required
@admin_required
def chemicals_import_gb18218():
    file = request.files.get("file")
    if not file:
        flash("请选择 GB18218_full_seed.sql 文件", "warning")
        return redirect(url_for("admin.chemicals_list"))
    text = file.read().decode("utf-8", errors="replace")
    try:
        summary = import_gb18218_full_seed_sql(text, replace_rules=True)
        db.session.commit()
        log_action(
            "admin_gb18218_import",
            f"chemicals={summary.chemicals}, alpha={summary.alpha_rules}, level={summary.level_rules}",
        )
        flash(
            f"导入完成：化学品 {summary.chemicals} 条，α规则 {summary.alpha_rules} 条，等级规则 {summary.level_rules} 条",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"导入失败：{e}", "danger")
    return redirect(url_for("admin.chemicals_list"))


@bp.post("/chemicals/validate-gb18218")
@login_required
@admin_required
def chemicals_validate_gb18218():
    file = request.files.get("file")
    if not file:
        flash("请选择 GB18218_full_seed.sql 文件", "warning")
        return redirect(url_for("admin.chemicals_list"))
    text = file.read().decode("utf-8", errors="replace")
    report = validate_gb18218_full_seed_sql(text)
    chemicals = Chemical.query.order_by(Chemical.name).all()
    flash(
        f"校验完成：化学品 INSERT {report.chemicals_total_inserts} 条，可导入 {report.chemicals_importable} 条，跳过 {report.chemicals_skipped} 条",
        "info",
    )
    return render_template(
        "admin/chemicals_list.html",
        chemicals=chemicals,
        q="",
        validation_report=report,
    )


@bp.post("/chemicals/dedup")
@login_required
@admin_required
def chemicals_dedup():
    summary = dedup_chemicals_keep_latest()
    db.session.commit()
    log_action(
        "admin_chemical_dedup",
        f"groups={summary.groups}, merged={summary.merged_rows}, storage_updated={summary.updated_storage_records}",
    )
    flash(
        f"去重完成：处理 {summary.groups} 组重复，合并 {summary.merged_rows} 条，更新储存记录 {summary.updated_storage_records} 条",
        "success",
    )
    return redirect(url_for("admin.chemicals_list"))



@bp.post("/chemicals/update-gb18218-params")
@login_required
@admin_required
def chemicals_update_gb18218_params():
    summary = apply_gb18218_table2_table3_table4_updates()
    db.session.commit()
    log_action(
        "admin_gb18218_params_update",
        f"cat_beta={summary.category_betas_upserted}, cat_threshold={summary.category_thresholds_upserted}, "
        f"chem_beta={summary.chemicals_beta_updated}",
    )
    flash(
        "已更新 GB 18218 参数："
        f"类别β upsert={summary.category_betas_upserted}，"
        f"类别临界量 upsert={summary.category_thresholds_upserted}，"
        f"化学品表3β更新={summary.chemicals_beta_updated}",
        "success",
    )
    return redirect(url_for("admin.chemicals_list"))


@bp.get("/chemicals/new")
@bp.post("/chemicals/new")
@login_required
@admin_required
def chemicals_new():
    form = ChemicalForm()
    if form.validate_on_submit():
        chem = Chemical()
        form.populate_obj(chem)
        _normalize_chemical_optional_fields(chem)
        conflict = _find_chemical_conflict(chem, exclude_id=None)
        if conflict:
            flash(
                f"保存失败：检测到重复数据（ID={conflict.id}）。请修改标准版本/CAS/临界量/单位，或使用“去重”合并。",
                "warning",
            )
            return render_template("admin/chemicals_form.html", form=form, mode="new")
        db.session.add(chem)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash(_format_chem_integrity_error(e), "warning")
            return render_template("admin/chemicals_form.html", form=form, mode="new")
        log_action("admin_chemical_create", f"id={chem.id}")
        flash("已新增化学品", "success")
        return redirect(url_for("admin.chemicals_list"))
    return render_template("admin/chemicals_form.html", form=form, mode="new")


@bp.get("/chemicals/<int:chem_id>/edit")
@bp.post("/chemicals/<int:chem_id>/edit")
@login_required
@admin_required
def chemicals_edit(chem_id: int):
    chem = Chemical.query.get_or_404(chem_id)
    form = ChemicalForm(obj=chem)
    if form.validate_on_submit():
        form.populate_obj(chem)
        _normalize_chemical_optional_fields(chem)
        conflict = _find_chemical_conflict(chem, exclude_id=chem.id)
        if conflict:
            flash(
                f"保存失败：检测到重复数据（ID={conflict.id}）。请修改标准版本/CAS/临界量/单位，或使用“去重”合并。",
                "warning",
            )
            return render_template("admin/chemicals_form.html", form=form, mode="edit")
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash(_format_chem_integrity_error(e), "warning")
            return render_template("admin/chemicals_form.html", form=form, mode="edit")
        log_action("admin_chemical_update", f"id={chem_id}")
        flash("已保存", "success")
        return redirect(url_for("admin.chemicals_list"))
    return render_template("admin/chemicals_form.html", form=form, mode="edit")


def _normalize_chemical_optional_fields(chem: Chemical) -> None:
    # Optional text inputs often submit empty string; store as NULL to avoid accidental "duplicate ''".
    for attr in [
        "category",
        "cas_no",
        "hazard_category_symbol",
        "beta_source",
        "gb_version",
        "unit",
        "source_standard",
    ]:
        if not hasattr(chem, attr):
            continue
        val = getattr(chem, attr)
        if isinstance(val, str):
            val = val.strip()
            if val == "":
                setattr(chem, attr, None)
            else:
                setattr(chem, attr, val)


def _find_chemical_conflict(chem: Chemical, *, exclude_id: int | None) -> Chemical | None:
    query = Chemical.query
    if exclude_id is not None:
        query = query.filter(Chemical.id != exclude_id)

    # Also check our logical uniqueness (name + cas_no) to keep UX consistent.
    if chem.name:
        q2 = query.filter(Chemical.name == chem.name)
        if chem.cas_no is None:
            q2 = q2.filter(Chemical.cas_no.is_(None))
        else:
            q2 = q2.filter(Chemical.cas_no == chem.cas_no)
        conflict2 = q2.order_by(Chemical.id.desc()).first()
        if conflict2:
            return conflict2

    return None


def _format_chem_integrity_error(e: IntegrityError) -> str:
    msg = str(getattr(e, "orig", e))
    if "uq_chem_cas" in msg:
        return (
            "保存失败：触发唯一约束 uq_chem_cas（gb_version+CAS+临界量+单位）。"
            "该约束会阻止 GB18218 表1中“同 CAS 同临界量但名称不同”的合法条目；建议删除该唯一索引后再导入。"
        )
    if "uq_chem_name_cas" in msg or "uq_chem_name_cas".lower() in msg.lower():
        return "保存失败：化学品名称+CAS 组合已存在（唯一约束）。请修改名称或 CAS。"
    if "Duplicate entry" in msg:
        return f"保存失败：数据重复（{msg}）。"
    return f"保存失败：{msg}"


@bp.post("/chemicals/<int:chem_id>/delete")
@login_required
@admin_required
def chemicals_delete(chem_id: int):
    chem = Chemical.query.get_or_404(chem_id)
    ref_count = StorageRecord.query.filter_by(chemical_id=chem_id).count()
    if ref_count > 0:
        flash(
            f"无法删除：该化学品已被 {ref_count} 条储存记录引用，请先修改/删除相关储存记录或使用“去重”合并。",
            "warning",
        )
        return redirect(url_for("admin.chemicals_list"))

    try:
        db.session.delete(chem)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("无法删除：该化学品存在关联数据（外键约束），请先处理关联记录。", "warning")
        return redirect(url_for("admin.chemicals_list"))

    log_action("admin_chemical_delete", f"id={chem_id}")
    flash("已删除", "success")
    return redirect(url_for("admin.chemicals_list"))


@bp.get("/rules")
@login_required
@admin_required
def rules_list():
    rules = RuleSet.query.order_by(RuleSet.updated_at.desc()).all()
    return render_template("admin/rules_list.html", rules=rules)


@bp.get("/rules/new")
@bp.post("/rules/new")
@login_required
@admin_required
def rules_new():
    form = RuleSetForm()
    if form.validate_on_submit():
        try:
            levels = form.parse_levels()
        except Exception:
            flash("等级区间 JSON 格式不正确", "warning")
            return render_template("admin/rules_form.html", form=form, mode="new")
        rule = RuleSet(name=form.name.data, is_active=bool(form.is_active.data), levels=levels)
        if rule.is_active:
            RuleSet.query.update({"is_active": False})
        db.session.add(rule)
        db.session.commit()
        log_action("admin_rule_create", f"id={rule.id}")
        flash("已新增规则", "success")
        return redirect(url_for("admin.rules_list"))
    return render_template("admin/rules_form.html", form=form, mode="new")


@bp.get("/rules/<int:rule_id>/edit")
@bp.post("/rules/<int:rule_id>/edit")
@login_required
@admin_required
def rules_edit(rule_id: int):
    rule = RuleSet.query.get_or_404(rule_id)
    form = RuleSetForm()
    if request.method == "GET":
        form.name.data = rule.name
        form.is_active.data = rule.is_active
        form.levels_json.data = json.dumps(rule.levels, ensure_ascii=False, indent=2)
    if form.validate_on_submit():
        rule.name = form.name.data
        try:
            rule.levels = form.parse_levels()
        except Exception:
            flash("等级区间 JSON 格式不正确", "warning")
            return render_template("admin/rules_form.html", form=form, mode="edit")
        rule.is_active = bool(form.is_active.data)
        if rule.is_active:
            RuleSet.query.filter(RuleSet.id != rule_id).update({"is_active": False})
        db.session.commit()
        log_action("admin_rule_update", f"id={rule_id}")
        flash("已保存", "success")
        return redirect(url_for("admin.rules_list"))
    return render_template("admin/rules_form.html", form=form, mode="edit")


@bp.get("/storage")
@login_required
@admin_required
def storage_all():
    records = StorageRecord.query.order_by(StorageRecord.updated_at.desc()).limit(500).all()
    return render_template("admin/storage_all.html", records=records)


@bp.get("/storage/<int:record_id>/edit")
@bp.post("/storage/<int:record_id>/edit")
@login_required
@admin_required
def storage_edit(record_id: int):
    rec = StorageRecord.query.get_or_404(record_id)
    from ..forms import StorageForm

    form = StorageForm(obj=rec)
    form.chemical_id.choices = [
        (c.id, f"{c.name}（临界量 {c.critical_quantity}{c.unit}）")
        for c in Chemical.query.order_by(Chemical.name).all()
    ]
    if form.validate_on_submit():
        form.populate_obj(rec)
        db.session.commit()
        log_action("admin_storage_update", f"id={record_id}")
        flash("已保存", "success")
        return redirect(url_for("admin.storage_all"))
    return render_template("admin/storage_form.html", form=form, rec=rec)


@bp.post("/storage/<int:record_id>/delete")
@login_required
@admin_required
def storage_delete(record_id: int):
    rec = StorageRecord.query.get_or_404(record_id)
    db.session.delete(rec)
    db.session.commit()
    log_action("admin_storage_delete", f"id={record_id}")
    flash("已删除", "success")
    return redirect(url_for("admin.storage_all"))


@bp.get("/results")
@login_required
@admin_required
def results_all():
    status = request.args.get("status", "").strip()
    query = EvaluationResult.query
    if status:
        query = query.filter_by(status=status)
    results = query.order_by(EvaluationResult.created_at.desc()).limit(500).all()
    return render_template("admin/results_all.html", results=results, status=status)


@bp.post("/results/<int:result_id>/review")
@login_required
@admin_required
def results_review(result_id: int):
    result = EvaluationResult.query.get_or_404(result_id)
    action = request.form.get("action", "")
    remark = request.form.get("remark", "").strip()[:255] or None
    if action not in {"approve", "reject"}:
        flash("无效操作", "warning")
        return redirect(url_for("admin.results_all"))
    result.status = "approved" if action == "approve" else "rejected"
    result.reviewer_id = current_user.id
    result.review_remark = remark
    result.reviewed_at = datetime.utcnow()
    db.session.commit()
    log_action("admin_result_review", f"id={result_id}, action={action}")
    flash("已提交审核", "success")
    return redirect(url_for("admin.results_all", status="pending"))


@bp.get("/backup")
@login_required
@admin_required
def backup_page():
    return render_template("admin/backup.html")


@bp.get("/backup/export.json")
@login_required
@admin_required
def backup_export():
    payload = export_db_to_json()
    text = dumps_json(payload)
    buf = io.BytesIO(text.encode("utf-8"))
    log_action("admin_backup_export")
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name="backup.json")


@bp.get("/backup/export.xlsx")
@login_required
@admin_required
def backup_export_xlsx():
    buf = export_db_to_xlsx()
    log_action("admin_backup_export_xlsx")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"backup_{ts}.xlsx",
    )


@bp.post("/backup/import")
@login_required
@admin_required
def backup_import():
    file = request.files.get("file")
    if not file:
        flash("请选择备份文件", "warning")
        return redirect(url_for("admin.backup_page"))
    try:
        payload = loads_json(file.read().decode("utf-8"))
        import_db_from_json(payload, truncate_first=True)
        log_action("admin_backup_import")
        flash("已恢复备份", "success")
        return redirect(url_for("admin.dashboard"))
    except Exception as e:
        flash(f"恢复失败：{e}", "danger")
        return redirect(url_for("admin.backup_page"))
