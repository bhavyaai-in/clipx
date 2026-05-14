import os
import zipfile
import subprocess
from flask import Blueprint, request, jsonify
from config import settings

webhook_bp = Blueprint("webhook", __name__)
LIVE_DIR = settings.repo_path


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


@webhook_bp.route("/git-reset-force", methods=["GET"])
def git_reset_force():
    # Aapki repository ka path (jahan .git folder hai)
    repo_path = settings.repo_path
    
    try:
        # 1. Pehle us folder mein jao
        os.chdir(repo_path)
        
        # 2. Saari manual edits ko clean karo (Untracked files bhi uda dega)
        # -f matlab force, -d matlab directories bhi
        subprocess.run(["git", "clean", "-fd"], capture_output=True, text=True)
        
        # 3. Files ko pichle commit par reset karo (Manual changes hat jayengi)
        result = subprocess.run(["git", "reset", "--hard", "HEAD"], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "message": "Bhai, manual edits saaf ho gayi! Ab aap 'git pull' kar sakte ho.",
                "details": result.stdout
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Git reset fail ho gaya.",
                "details": result.stderr
            })
            
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})