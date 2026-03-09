from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Index, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


GB_18218_2018 = "GB 18218-2018"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=True, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user/admin
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    company_name = db.Column(db.String(200), nullable=True)
    contact_name = db.Column(db.String(80), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Chemical(db.Model):
    __tablename__ = "chemicals"

    id = db.Column(db.Integer, primary_key=True)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    cas_no = db.Column(db.String(50), nullable=True)
    critical_quantity = db.Column(db.Float, nullable=False)  # 临界量
    unit = db.Column(db.String(20), nullable=False, default="t")
    source_standard = db.Column(db.String(100), nullable=False, default="GB 18218")
    hazard_category_symbol = db.Column(db.String(20), nullable=True)  # 表 3/4 类别符号（示例）
    beta = db.Column(db.Float, nullable=True)  # β（可由类别推导）
    beta_source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("name", "cas_no", name="uq_chem_name_cas"),
        Index("ix_chem_name", "name"),
    )


class StorageRecord(db.Model):
    __tablename__ = "storage_records"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    enterprise_name = db.Column(db.String(200), nullable=False)
    chemical_id = db.Column(db.Integer, db.ForeignKey("chemicals.id"), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="t")
    unit_name = db.Column(db.String(120), nullable=True)  # 重大危险源单元名称（装置/罐区/库区等）
    unit_type = db.Column(db.String(50), nullable=True)  # 单元类型
    qty_basis = db.Column(db.String(30), nullable=True)  # 数量口径（储存/生产/使用等）
    material_type = db.Column(db.String(30), nullable=True)  # single/mixture
    mixture_name = db.Column(db.String(120), nullable=True)
    mixture_category_symbol = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)  # 场所
    storage_method = db.Column(db.String(100), nullable=True)  # 方式
    properties = db.Column(db.String(200), nullable=True)  # 属性/备注

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner = db.relationship("User", backref=db.backref("storage_records", lazy=True))
    chemical = db.relationship("Chemical")


class RuleSet(db.Model):
    __tablename__ = "rule_sets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    # levels: [{min:1, max:10, level:'四级'}, ...]
    levels = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EvaluationResult(db.Model):
    __tablename__ = "evaluation_results"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    enterprise_name = db.Column(db.String(200), nullable=False)

    rule_set_id = db.Column(db.Integer, db.ForeignKey("rule_sets.id"), nullable=False)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    s_value = db.Column(db.Float, nullable=False, default=0.0)  # 式(1) S
    exposure_people_500m = db.Column(db.Integer, nullable=False, default=0)  # 500m 暴露人口
    alpha_used = db.Column(db.Float, nullable=False, default=1.0)  # 表 5 α
    r_value = db.Column(db.Float, nullable=False)
    is_major_hazard = db.Column(db.Boolean, nullable=False)
    level = db.Column(db.String(20), nullable=True)
    level_by_gb = db.Column(db.String(20), nullable=True)  # 表 6 等级（GB 18218）
    basis = db.Column(db.JSON, nullable=False)  # per-chemical computation snapshot

    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending/approved/rejected
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_remark = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    rule_set = db.relationship("RuleSet")

    __table_args__ = (Index("ix_eval_enterprise", "enterprise_name"),)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.String(500), nullable=True)
    ip = db.Column(db.String(60), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")


class AlphaRule(db.Model):
    __tablename__ = "alpha_rules"

    id = db.Column(db.Integer, primary_key=True)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    min_people = db.Column(db.Integer, nullable=False)
    max_people = db.Column(db.Integer, nullable=True)
    alpha = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False, default=GB_18218_2018)
    note = db.Column(db.String(255), nullable=True)

    __table_args__ = (Index("ix_alpha_rules_range", "min_people", "max_people"),)


class LevelRule(db.Model):
    __tablename__ = "level_rules"

    id = db.Column(db.Integer, primary_key=True)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    min_r = db.Column(db.Float, nullable=False)
    max_r = db.Column(db.Float, nullable=True)
    level = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(100), nullable=False, default=GB_18218_2018)
    note = db.Column(db.String(255), nullable=True)


class CategoryThreshold(db.Model):
    __tablename__ = "category_thresholds"

    id = db.Column(db.Integer, primary_key=True)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    category_symbol = db.Column(db.String(20), nullable=False)
    threshold_quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="t")
    source = db.Column(db.String(100), nullable=False, default=GB_18218_2018)
    note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("gb_version", "category_symbol", name="uq_cat_threshold"),
        Index("ix_cat_threshold_symbol", "category_symbol"),
    )


class CategoryBeta(db.Model):
    __tablename__ = "category_betas"

    id = db.Column(db.Integer, primary_key=True)
    gb_version = db.Column(db.String(30), nullable=False, default=GB_18218_2018)
    category_symbol = db.Column(db.String(20), nullable=False)
    beta = db.Column(db.Float, nullable=False)
    beta_source = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(100), nullable=False, default=GB_18218_2018)
    note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("gb_version", "category_symbol", name="uq_cat_beta"),
        Index("ix_cat_beta_symbol", "category_symbol"),
    )
