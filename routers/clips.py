from datetime import datetime, timezone
from uuid import uuid4
from flask import Blueprint, request, jsonify
from auth import require_device
from database import get_conn

clips_bp = Blueprint("clips", __name__)


@clips_bp.route("/v1/clips", methods=["GET"])
@require_device
def list_clips():
    limit = min(int(request.args.get("limit", 50)), 200)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, device_id, device_name, content, created_at FROM clips ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@clips_bp.route("/v1/clips", methods=["POST"])
@require_device
def create_clip():
    body = request.get_json()
    clip_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO clips (id, device_id, device_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (clip_id, request.device["device_id"], request.device["device_name"], body["content"], now),
        )
    return jsonify({"id": clip_id, "created_at": now}), 201


@clips_bp.route("/v1/clips/<clip_id>", methods=["DELETE"])
@require_device
def delete_clip(clip_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
    return "", 204


@clips_bp.route("/v1/clips", methods=["DELETE"])
@require_device
def bulk_delete_clips():
    body = request.get_json() or {}
    with get_conn() as conn:
        if body.get("all"):
            conn.execute("DELETE FROM clips")
        elif body.get("ids"):
            ids = body["ids"]
            conn.execute(f"DELETE FROM clips WHERE id IN ({','.join('?'*len(ids))})", ids)
    return "", 204
