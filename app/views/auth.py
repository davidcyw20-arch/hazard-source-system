from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db, login_manager
from ..forms import LoginForm, RegisterForm
from ..models import User
from ..utils.audit import log_action

bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


@bp.get("/login")
@bp.post("/login")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if User.query.count() == 0:
            flash(
                "系统尚未初始化用户数据：请先执行 `flask init-db`，或使用 SQLite 重新启动后再登录。",
                "warning",
            )
            return render_template("auth/login.html", form=form)
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash("用户名或密码错误", "danger")
            return render_template("auth/login.html", form=form)
        if not user.is_active:
            flash("账号已被停用，请联系管理员", "warning")
            return render_template("auth/login.html", form=form)
        login_user(user)
        log_action("login", f"ua={request.headers.get('User-Agent')}")
        return redirect(url_for("admin.dashboard") if user.is_admin else url_for("user.dashboard"))
    return render_template("auth/login.html", form=form)


@bp.get("/register")
@bp.post("/register")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = (form.username.data or "").strip()
        email = (form.email.data or "").strip() or None
        if not username:
            flash("用户名不能为空", "warning")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "warning")
            return render_template("auth/register.html", form=form)
        if email and User.query.filter_by(email=email).first():
            flash("邮箱已被使用", "warning")
            return render_template("auth/register.html", form=form)
        user = User(username=username, email=email, role="user", is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("注册失败：用户名或邮箱已存在，请更换后重试", "warning")
            return render_template("auth/register.html", form=form)
        log_action("register", f"username={user.username}")
        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.get("/logout")
@login_required
def logout():
    log_action("logout")
    logout_user()
    return redirect(url_for("auth.login"))
