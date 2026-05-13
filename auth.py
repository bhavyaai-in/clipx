from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from jose import jwt, JWTError
from config import settings
from database import get_conn

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72


def create_admin_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": settings.admin_email, "exp": expire}, settings.jwt_secret, algorithm=ALGORITHM)


def require_device(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get("X-Device-Secret")
        if not secret:
            return jsonify({"detail": "Missing X-Device-Secret header"}), 422
        now = datetime.now(timezone.utc).isoformat()
        with get_conn() as conn:
            row = conn.execute(
                "SELECT device_id, device_name FROM devices WHERE secret_key = ?", (secret,)
            ).fetchone()
            if not row:
                return jsonify({"detail": "Unknown device secret"}), 401
            conn.execute("UPDATE devices SET last_seen = ? WHERE device_id = ?", (now, row["device_id"]))
        request.device = {"device_id": row["device_id"], "device_name": row["device_name"]}
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"detail": "Missing Bearer token"}), 401
        try:
            jwt.decode(auth[7:], settings.jwt_secret, algorithms=[ALGORITHM])
        except JWTError:
            return jsonify({"detail": "Invalid or expired admin token"}), 401
        return f(*args, **kwargs)
    return decorated
