# app/bootstrap.py
from sqlalchemy.orm import Session
from .models import User, Role
from .auth import hash_password
from .settings import get_settings


def ensure_admin(db: Session):
    s = get_settings()
    if not s.ADMIN_EMAIL:
        return
    u = db.query(User).filter_by(email=s.ADMIN_EMAIL).first()
    if not u:
        pw = s.ADMIN_PASSWORD or "change-me-now"
        u = User(email=s.ADMIN_EMAIL,
                 password_hash=hash_password(pw), role=Role.ADMIN)
        db.add(u)
        db.commit()
    else:
        u.role = Role.ADMIN
        db.commit()
