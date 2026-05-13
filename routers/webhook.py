import subprocess
import os
import shutil
from flask import Blueprint, request, jsonify
from config import settings

webhook_bp = Blueprint("webhook", __name__)

# APP_DIR aapka root folder hai (e.g., /public_html/clipx.bhavyaai.com)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@webhook_bp.route("/deploy", methods=["POST", "GET"])
def deploy():
    token = request.args.get("token")
    if token != settings.webhook_secret:
        return jsonify({"status": "error", "detail": "Invalid Secret"}), 403

    # URLs from settings
    authenticated_url = f"https://{settings.github_token}@{settings.repo_url}"
    clean_url = f"https://{settings.repo_url}"
    
    # Path of the standalone folder after pull
    # Isse settings.py mein 'build_folder/standalone' set kar dena
    subfolder_path = getattr(settings, 'subfolder_path', 'build_folder/standalone')
    source_dir = os.path.join(APP_DIR, subfolder_path)

    output = ""
    try:
        # 1. Set Token URL
        subprocess.run(
            ["git", "remote", "set-url", "origin", authenticated_url],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10,
        )

        # 2. Git Pull
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=APP_DIR, capture_output=True, text=True, timeout=30,
        )
        output = result.stdout + result.stderr

        # 3. Security: Reset to Clean URL immediately
        subprocess.run(
            ["git", "remote", "set-url", "origin", clean_url],
            cwd=APP_DIR, capture_output=True, text=True, timeout=10,
        )

        if result.returncode != 0:
            return jsonify({"status": "error", "output": output}), 500

        # 4. Smart Move Logic: Standalone content ko root mein move karna
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                s = os.path.join(source_dir, filename)
                d = os.path.join(APP_DIR, filename)
                
                # Agar purani file/folder hai toh use delete karke naya move karein
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                
                shutil.move(s, d)
            output += "\n[Success] Standalone files moved to root."
        else:
            output += f"\n[Warning] Subfolder {subfolder_path} not found. Check Git path."

    except Exception as e:
        # Emergency URL Reset
        subprocess.run(["git", "remote", "set-url", "origin", clean_url], cwd=APP_DIR)
        return jsonify({"status": "error", "output": str(e)}), 500

    # 5. Restart Trigger (cPanel/Passenger ke liye)
    touched = False
    restart_path = os.path.join(APP_DIR, "tmp", "restart.txt")
    os.makedirs(os.path.dirname(restart_path), exist_ok=True)
    try:
        with open(restart_path, "w") as f:
            f.write(output)
        # cPanel Passenger ko batane ke liye ki app restart karni hai
        restart_js = os.path.join(APP_DIR, "tmp", "restart.txt")
        os.utime(APP_DIR, None) # Folder touch karna bhi kabhi kaam karta hai
        touched = True
    except OSError:
        pass

    return jsonify({
        "status": "success",
        "msg": "Deployment complete",
        "output": output,
        "restart_triggered": touched,
    })