import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from flask import Blueprint, request, jsonify, send_file
from auth import require_device
from config import settings
from database import get_conn

files_bp = Blueprint("files", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, settings.files_dir)


def _cleanup_expired():
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        expired = conn.execute(
            "SELECT id, filepath FROM files WHERE expires_at <= ?", (now,)
        ).fetchall()
        for row in expired:
            if os.path.exists(row["filepath"]):
                os.remove(row["filepath"])
        if expired:
            ids = [r["id"] for r in expired]
            conn.execute(f"DELETE FROM files WHERE id IN ({','.join('?'*len(ids))})", ids)


def _file_path(file_id: str, filename: str) -> str:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    return os.path.normpath(os.path.join(UPLOADS_DIR, f"{file_id}_{filename}"))


@files_bp.route("/v1/files", methods=["POST"])
@require_device
def upload_file():
    if "file" not in request.files:
        return jsonify({"detail": "No file provided"}), 400
    f = request.files["file"]
    file_id = str(uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.file_ttl_minutes)
    filepath = _file_path(file_id, f.filename)
    f.save(filepath)
    size = os.path.getsize(filepath)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO files (id, device_id, device_name, filename, filepath, size, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, request.device["device_id"], request.device["device_name"], f.filename, filepath, size, now.isoformat(), expires_at.isoformat()),
        )
    return jsonify({"id": file_id, "filename": f.filename, "expires_at": expires_at.isoformat()}), 201


@files_bp.route("/v1/files", methods=["GET"])
@require_device
def list_files():
    _cleanup_expired()
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, device_id, device_name, filename, size, created_at, expires_at FROM files WHERE expires_at > ? ORDER BY created_at DESC",
            (now,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@files_bp.route("/v1/files/<file_id>/download", methods=["GET"])
@require_device
def download_file(file_id):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT filepath, filename, expires_at FROM files WHERE id = ?", (file_id,)
        ).fetchone()
    if not row or row["expires_at"] <= now:
        return jsonify({"detail": "File not found or expired"}), 404
    return send_file(row["filepath"], download_name=row["filename"], as_attachment=True)


@files_bp.route("/v1/files/<file_id>", methods=["DELETE"])
@require_device
def delete_file(file_id):
    with get_conn() as conn:
        row = conn.execute("SELECT filepath FROM files WHERE id = ?", (file_id,)).fetchone()
        if row and os.path.exists(row["filepath"]):
            os.remove(row["filepath"])
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    return "", 204
