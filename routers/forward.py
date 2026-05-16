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

    # 1. Hop-by-hop headers ko filter karein
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP}

    # 2. Cloudflare/WAF bypass ke liye safe default headers (Agar client ne nahi bheje hain)
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    if "Accept" not in headers:
        headers["Accept"] = "application/json"

    # 3. Target URL ke asli query params filter karein (?url= wale proxy param ko hatakar)
    target_params = {k: v for k, v in request.args.items() if k != "url"}

    kwargs = {
        "method": request.method,
        "url": target_url,
        "headers": headers,
        "params": target_params,  # Target params yahan add kar diye
        "stream": True,
        "timeout": 60,
    }

    # 4. Method check karein (GET request me body force mat karein agar khali ho)
    if request.method == "GET" and not request.files and not request.form and not request.get_data():
        pass
    else:
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
        # Request forward karein
        resp = http_requests.request(**kwargs)

        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP}

        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk

        return Response(generate(), status=resp.status_code, headers=resp_headers)

    except Exception as e:
        return jsonify({"error": f"Gateway Error: {str(e)}"}), 502