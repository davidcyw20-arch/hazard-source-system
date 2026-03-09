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
