from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ProfileForm, StorageForm
from ..models import AuditLog, Chemical, EvaluationResult, RuleSet, StorageRecord
from ..models import GB_18218_2018
from ..services.identify import identify_gb18218
from ..services.pdf import render_pdf_bytes
from ..utils.audit import log_action

bp = Blueprint("user", __name__)


@bp.get("/")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    storage_count = StorageRecord.query.filter_by(owner_id=current_user.id).count()
    results_count = EvaluationResult.query.filter_by(owner_id=current_user.id).count()
    return render_template(
        "user/dashboard.html", storage_count=storage_count, results_count=results_count
    )


@bp.get("/profile")
@bp.post("/profile")
@login_required
def profile():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        log_action("profile_update")
        flash("资料已更新", "success")
        return redirect(url_for("user.profile"))
    return render_template("user/profile.html", form=form)


@bp.get("/storage")
@login_required
def storage_list():
    if current_user.is_admin:
        return redirect(url_for("admin.storage_all"))
    records = (
        StorageRecord.query.filter_by(owner_id=current_user.id)
        .order_by(StorageRecord.updated_at.desc())
        .all()
    )
    return render_template("user/storage_list.html", records=records)


@bp.get("/storage/new")
@bp.post("/storage/new")
@login_required
def storage_new():
    if current_user.is_admin:
        return redirect(url_for("admin.storage_all"))
    form = StorageForm()
    chemicals = Chemical.query.order_by(Chemical.name).all()
    if not chemicals:
        flash("系统暂无化学品临界量数据，请联系管理员维护", "warning")
        return redirect(url_for("user.storage_list"))
    if not form.unit.data:
        form.unit.data = "t"
    form.chemical_id.choices = [
        (c.id, f"{c.name}（临界量 {c.critical_quantity}{c.unit}）") for c in chemicals
    ]
    if form.validate_on_submit():
        rec = StorageRecord(owner_id=current_user.id)
        form.populate_obj(rec)
        db.session.add(rec)
        db.session.commit()
        log_action("storage_create", f"id={rec.id}")
        flash("已新增储存信息", "success")
        return redirect(url_for("user.storage_list"))
    return render_template("user/storage_form.html", form=form, mode="new")


@bp.get("/storage/<int:record_id>/edit")
@bp.post("/storage/<int:record_id>/edit")
@login_required
def storage_edit(record_id: int):
    rec = StorageRecord.query.get_or_404(record_id)
    if rec.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    if current_user.is_admin and rec.owner_id != current_user.id:
        return redirect(url_for("admin.storage_edit", record_id=record_id))
    form = StorageForm(obj=rec)
    chemicals = Chemical.query.order_by(Chemical.name).all()
    if not chemicals:
        flash("系统暂无化学品临界量数据，请联系管理员维护", "warning")
        return redirect(url_for("user.storage_list"))
    if not form.unit.data:
        form.unit.data = "t"
    form.chemical_id.choices = [
        (c.id, f"{c.name}（临界量 {c.critical_quantity}{c.unit}）") for c in chemicals
    ]
    if form.validate_on_submit():
        form.populate_obj(rec)
        db.session.commit()
        log_action("storage_update", f"id={rec.id}")
        flash("已保存", "success")
        return redirect(url_for("user.storage_list"))
    return render_template("user/storage_form.html", form=form, mode="edit")


@bp.post("/storage/<int:record_id>/delete")
@login_required
def storage_delete(record_id: int):
    rec = StorageRecord.query.get_or_404(record_id)
    if rec.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    if current_user.is_admin and rec.owner_id != current_user.id:
        return redirect(url_for("admin.storage_all"))
    db.session.delete(rec)
    db.session.commit()
    log_action("storage_delete", f"id={record_id}")
    flash("已删除", "success")
    return redirect(url_for("user.storage_list"))


@bp.post("/evaluate")
@login_required
def evaluate():
    enterprise_name = (request.form.get("enterprise_name", "") or "").strip()
    if not enterprise_name:
        flash("请选择企业名称", "warning")
        return redirect(url_for("user.storage_list"))
    exposure_people_500m = int(request.form.get("exposure_people_500m", "0") or 0)
    records = (
        StorageRecord.query.filter_by(owner_id=current_user.id, enterprise_name=enterprise_name)
        .all()
    )
    if not records:
        flash("该企业暂无储存记录", "warning")
        return redirect(url_for("user.storage_list"))
    rule_set = RuleSet.query.filter_by(is_active=True).first()
    if not rule_set:
        flash("系统尚未配置评估规则，请联系管理员", "danger")
        return redirect(url_for("user.storage_list"))

    out = identify_gb18218(
        enterprise_name=enterprise_name,
        records=records,
        exposure_people_500m=exposure_people_500m,
        gb_version=GB_18218_2018,
        rule_set=rule_set,
    )
    result = EvaluationResult(
        owner_id=current_user.id,
        enterprise_name=enterprise_name,
        rule_set_id=rule_set.id,
        gb_version=out.gb_version,
        s_value=out.s_value,
        exposure_people_500m=out.exposure_people_500m,
        alpha_used=out.alpha_used,
        r_value=out.r_value,
        is_major_hazard=out.is_major_hazard,
        level=out.level_compat,
        level_by_gb=out.level_by_gb,
        basis=out.basis,
        status="pending",
    )
    db.session.add(result)
    db.session.commit()
    log_action("evaluate", f"enterprise={enterprise_name}, result_id={result.id}")
    flash("已生成辨识与评估结果（待审核）", "success")
    return redirect(url_for("user.results_detail", result_id=result.id))


@bp.get("/results")
@login_required
def results_list():
    if current_user.is_admin:
        return redirect(url_for("admin.results_all"))
    results = (
        EvaluationResult.query.filter_by(owner_id=current_user.id)
        .order_by(EvaluationResult.created_at.desc())
        .all()
    )
    return render_template("user/results_list.html", results=results)


@bp.get("/results/<int:result_id>")
@login_required
def results_detail(result_id: int):
    result = EvaluationResult.query.get_or_404(result_id)
    if result.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("user/results_detail.html", result=result)


@bp.get("/results/<int:result_id>/report")
@login_required
def report_html(result_id: int):
    result = EvaluationResult.query.get_or_404(result_id)
    if result.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("report/report.html", result=result, user=result.owner)


@bp.get("/results/<int:result_id>/report.pdf")
@login_required
def report_pdf(result_id: int):
    result = EvaluationResult.query.get_or_404(result_id)
    if result.owner_id != current_user.id and not current_user.is_admin:
        abort(403)
    pdf_bytes = render_pdf_bytes("report/report.html", {"result": result, "user": result.owner})
    filename = f"重大危险源评估报告_{result.enterprise_name}_{result.id}.pdf"
    return send_file(
        pdf_bytes,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@bp.get("/history")
@login_required
def history():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    logs = (
        AuditLog.query.filter_by(user_id=current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("user/history.html", logs=logs)
