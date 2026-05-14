import os
import zipfile
import subprocess
from flask import Blueprint, request, jsonify
from config import settings

webhook_bp = Blueprint("webhook", __name__)
LIVE_DIR = "/home2/bhavyaai/public_html/bhavyaai.com"


@webhook_bp.route("/deploy", methods=["POST"])
def deploy():
    token = request.args.get("token") or request.form.get("token")
    if token != settings.webhook_secret:
        return jsonify({"status": "error", "detail": "Invalid Secret"}), 403

    if 'file' not in request.files:
        return jsonify({"status": "error", "detail": "No file provided"}), 400

    file = request.files['file']
    temp_zip = os.path.join(LIVE_DIR, "deploy.zip")

    try:
        file.save(temp_zip)

        with zipfile.ZipFile(temp_zip, 'r') as zf:
            zf.extractall(LIVE_DIR)
        os.remove(temp_zip)

        pip = subprocess.run(
            "pip install -r backend/requirements.txt --quiet",
            shell=True, capture_output=True, text=True, cwd=LIVE_DIR, timeout=120,
        )
        output = "[Success] Extracted.\n" + pip.stdout + pip.stderr

    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500

    restart = os.path.join(LIVE_DIR, "tmp", "restart.txt")
    os.makedirs(os.path.dirname(restart), exist_ok=True)
    with open(restart, "w") as f:
        f.write("Deploy complete")

    return jsonify({"status": "success", "msg": "Backend deployed!", "output": output})
