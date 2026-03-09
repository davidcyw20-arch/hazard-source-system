from __future__ import annotations

import json

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    FloatField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6, max=128)])


class RegisterForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField("邮箱", validators=[Optional(), Email(), Length(max=120)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6, max=128)])


class ProfileForm(FlaskForm):
    company_name = StringField("企业/单位名称", validators=[Optional(), Length(max=200)])
    contact_name = StringField("联系人", validators=[Optional(), Length(max=80)])
    phone = StringField("联系电话", validators=[Optional(), Length(max=40)])
    address = StringField("地址", validators=[Optional(), Length(max=255)])


class UserAdminForm(FlaskForm):
    role = SelectField(
        "角色",
        choices=[("user", "普通用户"), ("admin", "管理员")],
        validators=[DataRequired()],
    )
    is_active = BooleanField("启用状态")
    reset_password = PasswordField("重置密码（可选）", validators=[Optional(), Length(min=6, max=128)])


class ChemicalForm(FlaskForm):
    name = StringField("化学品名称", validators=[DataRequired(), Length(max=120)])
    category = StringField("类别", validators=[Optional(), Length(max=80)])
    cas_no = StringField("CAS 号", validators=[Optional(), Length(max=50)])
    critical_quantity = FloatField("临界量", validators=[DataRequired()])
    unit = StringField("单位", validators=[DataRequired(), Length(max=20)])
    source_standard = StringField("标准来源", validators=[DataRequired(), Length(max=100)])
    gb_version = StringField("标准版本", validators=[Optional(), Length(max=30)], default="GB 18218-2018")
    hazard_category_symbol = StringField("类别符号", validators=[Optional(), Length(max=20)])
    beta = FloatField("β 系数（可选）", validators=[Optional()])
    beta_source = StringField("β 来源（可选）", validators=[Optional(), Length(max=100)])


class StorageForm(FlaskForm):
    enterprise_name = StringField("企业名称", validators=[DataRequired(), Length(max=200)])
    chemical_id = SelectField("化学品", coerce=int, validators=[DataRequired()])
    amount = FloatField("储存量", validators=[DataRequired()])
    unit = StringField("单位", validators=[DataRequired(), Length(max=20)], default="t")
    unit_name = StringField("单元名称（可选）", validators=[Optional(), Length(max=120)])
    unit_type = SelectField(
        "单元类型（可选）",
        choices=[
            ("", "未填写"),
            ("装置", "装置"),
            ("罐区", "罐区"),
            ("库区", "库区"),
            ("仓库", "仓库"),
            ("管廊", "管廊"),
            ("其他", "其他"),
        ],
        validators=[Optional()],
    )
    qty_basis = SelectField(
        "数量口径（可选）",
        choices=[("", "未填写"), ("储存", "储存"), ("生产", "生产"), ("使用", "使用"), ("运输", "运输")],
        validators=[Optional()],
    )
    material_type = SelectField(
        "物质类型（可选）",
        choices=[("", "未填写"), ("single", "单一物质"), ("mixture", "混合物")],
        validators=[Optional()],
    )
    mixture_name = StringField("混合物名称（可选）", validators=[Optional(), Length(max=120)])
    mixture_category_symbol = StringField("混合物类别符号（可选）", validators=[Optional(), Length(max=20)])
    location = StringField("储存场所", validators=[Optional(), Length(max=200)])
    storage_method = StringField("储存方式", validators=[Optional(), Length(max=100)])
    properties = StringField("相关属性/备注", validators=[Optional(), Length(max=200)])


class RuleSetForm(FlaskForm):
    name = StringField("规则名称", validators=[DataRequired(), Length(max=120)])
    is_active = BooleanField("设为启用")
    levels_json = TextAreaField("等级区间（JSON）", validators=[DataRequired()])

    def parse_levels(self):
        return json.loads(self.levels_json.data)
