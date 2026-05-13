from flask import Flask, request, jsonify
from database import init_db
from routers.clips import clips_bp
from routers.files import files_bp
from routers.devices import devices_bp
from routers.admin import admin_bp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

app.register_blueprint(clips_bp)
app.register_blueprint(files_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(admin_bp)

ALLOWED_ORIGINS = {"https://clipx.bhavyaai.com", "http://localhost:3000"}


@app.after_request
def cors(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or origin.startswith("chrome-extension://"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Device-Secret"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return app.make_default_options_response()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


with app.app_context():
    init_db()

# WSGI entry point
application = app
