from flask import Blueprint, request, jsonify
from auth import require_device
from database import get_conn

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/v1/devices", methods=["GET"])
@require_device
def list_devices():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT device_id, device_name, created_at, last_seen FROM devices ORDER BY last_seen DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@devices_bp.route("/v1/devices/<device_id>", methods=["DELETE"])
@require_device
def remove_device(device_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
    return "", 204
