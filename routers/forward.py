import requests as http_requests
from flask import Blueprint, request, Response, jsonify

forward_bp = Blueprint("forward", __name__)

HOP_BY_HOP = {
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "upgrade",
}


@forward_bp.route("/rqfarward", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"])
def forward_request():
    target_url = request.args.get("url")
    if not target_url:
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP}

    kwargs = {
        "method": request.method,
        "url": target_url,
        "headers": headers,
        "stream": True,
        "timeout": 60,
    }

    if request.files:
        kwargs["files"] = {k: (v.filename, v.stream, v.mimetype) for k, v in request.files.items()}
        kwargs["data"] = request.form
        if "Content-Type" in kwargs["headers"]:
            del kwargs["headers"]["Content-Type"]
    elif request.form:
        kwargs["data"] = request.form
    else:
        kwargs["data"] = request.get_data()

    try:
        resp = http_requests.request(**kwargs)

        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP}

        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk

        return Response(generate(), status=resp.status_code, headers=resp_headers)

    except Exception as e:
        return jsonify({"error": f"Gateway Error: {str(e)}"}), 502
