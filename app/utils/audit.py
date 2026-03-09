from __future__ import annotations

from flask import request
from flask_login import current_user

from ..extensions import db
from ..models import AuditLog


def log_action(action: str, detail: str | None = None) -> None:
    try:
        user_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        db.session.add(AuditLog(user_id=user_id, action=action, detail=detail, ip=ip))
        db.session.commit()
    except Exception:
        db.session.rollback()
