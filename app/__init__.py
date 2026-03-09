from __future__ import annotations

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from config import DevelopmentConfig

from .cli import register_cli
from .extensions import csrf, db, login_manager
from .views import admin, api, auth, user
from .utils.i18n import label_action, label_review_status


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(DevelopmentConfig)
    app.config.from_envvar("HAZARD_SETTINGS", silent=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)

    register_cli(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _auto_prepare_sqlite(app)
    return app


def _register_template_helpers(app: Flask) -> None:
    @app.context_processor
    def _ctx():
        return {"label_action": label_action, "label_review_status": label_review_status}


def _register_error_handlers(app: Flask):
    from flask import render_template
    from flask import flash, redirect, request, url_for
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_e):
        flash("表单已过期或校验失败，请刷新页面后重试。", "warning")
        return redirect(request.referrer or url_for("user.dashboard"))

    from sqlalchemy.exc import OperationalError

    @app.errorhandler(OperationalError)
    def handle_db_operational_error(e):
        msg = str(getattr(e, "orig", e))
        if "Access denied" in msg or "1045" in msg:
            flash(
                "MySQL 认证失败：请检查 .env 中 DATABASE_URL 的用户名/密码和数据库权限。",
                "danger",
            )
        elif "no such table" in msg:
            flash(
                "数据库尚未初始化，请先执行 `flask init-db`（或首次使用 SQLite 时重启应用自动建表）。",
                "warning",
            )
        elif "Could not parse SQLAlchemy URL" in msg:
            flash("DATABASE_URL 格式无效或为空，请在 .env 中配置正确连接串。", "danger")
        elif "Can't connect" in msg or "Connection refused" in msg:
            flash("数据库服务不可达，请确认数据库已启动且主机端口配置正确。", "danger")
        else:
            flash(f"数据库连接失败：{msg[:120]}。请检查 DATABASE_URL 配置。", "danger")
        return redirect(url_for("auth.login"))



def _auto_prepare_sqlite(app: Flask) -> None:
    uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    if not uri.startswith("sqlite"):
        return
    # Improve first-run experience: ensure SQLite tables exist to avoid login-time errors.
    with app.app_context():
        db.create_all()
