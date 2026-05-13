import os
import shutil
import zipfile
import subprocess
from flask import Blueprint, request, jsonify
from config import settings

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/deploy", methods=["POST"])
def deploy():
    token = request.args.get("token") or request.form.get("token")
    if token != settings.webhook_secret:
        return jsonify({"status": "error", "detail": "Invalid Secret"}), 403

    if 'file' not in request.files:
        return jsonify({"status": "error", "detail": "No file provided"}), 400
    
    file = request.files['file']
    LIVE_DIR = "/home2/bhavyaai/public_html/bhavyaai.com"
    temp_zip_path = os.path.join(LIVE_DIR, "raw_code.zip")

    output = ""
    try:
        file.save(temp_zip_path)
        
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(LIVE_DIR)
        output += "[Success] Raw code extracted.\n"
        os.remove(temp_zip_path)

        output += "\n--- Running NPM Install ---\n"
        install_res = subprocess.run("npm install", shell=True, cwd=LIVE_DIR, capture_output=True, text=True)
        output += install_res.stdout + install_res.stderr

        output += "\n--- Running NPM Build ---\n"
        build_res = subprocess.run("npm run build", shell=True, cwd=LIVE_DIR, capture_output=True, text=True)
        output += build_res.stdout + build_res.stderr

    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500

    restart_path = os.path.join(LIVE_DIR, "tmp", "restart.txt")
    os.makedirs(os.path.dirname(restart_path), exist_ok=True)
    with open(restart_path, "w") as f: 
        f.write("Raw Deploy & Build Complete")

    return jsonify({"status": "success", "msg": "Raw code deployed and built on server!", "output": output})
