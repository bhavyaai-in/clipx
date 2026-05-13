import subprocess
import os
from flask import Blueprint, request, jsonify
from config import settings

webhook_bp = Blueprint("webhook", __name__)

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@webhook_bp.route("/deploy", methods=["POST","GET"])
def deploy():
    token = request.args.get("token")
    if token != settings.webhook_secret:
        return jsonify({"status": "error", "detail": "Invalid Secret"}), 403

    authenticated_url = f"https://{settings.github_token}@{settings.repo_url}"
    clean_url = f"https://{settings.repo_url}"

    try:
        subprocess.run(
            ["git", "remote", "set-url", "origin", authenticated_url],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10,
        )

        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=30,
        )
        output = result.stdout + result.stderr

        subprocess.run(
            ["git", "remote", "set-url", "origin", clean_url],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10,
        )

        if result.returncode != 0:
            return jsonify({"status": "error", "output": output}), 500

    except Exception as e:
        subprocess.run(
            ["git", "remote", "set-url", "origin", clean_url],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10,
        )
        return jsonify({"status": "error", "output": str(e)}), 500

    touched = False
    restart_path = os.path.join(APP_DIR, "tmp", "restart.txt")
    os.makedirs(os.path.dirname(restart_path), exist_ok=True)
    try:
        with open(restart_path, "w") as f:
            f.write(output)
        touched = True
    except OSError:
        pass

    return jsonify({
        "status": "success",
        "msg": "Repo updated",
        "output": output,
        "restart_triggered": touched,
    })
