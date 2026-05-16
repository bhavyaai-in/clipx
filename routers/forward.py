import logging
import os
import requests as http_requests
from flask import Blueprint, request, Response, jsonify

forward_bp = Blueprint("forward", __name__)
logger = logging.getLogger("rqfarward")

if not logger.handlers:
    logger.setLevel(logging.INFO)
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forward.log")
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

HOP_BY_HOP = {
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "upgrade",
}


@forward_bp.route("/rqfarward", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"])
def forward_request():
    target_url = request.args.get("url")
    if not target_url:
        logger.warning("rqfarward - missing url param | remote=%s", request.remote_addr)
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    logger.info(
        "rqfarward IN  | method=%s url=%s content_type=%s content_length=%s | from=%s",
        request.method, target_url, request.content_type, request.content_length, request.remote_addr,
    )

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
        logger.info("rqfarward body | type=multipart files=%s form_keys=%s", list(request.files.keys()), list(request.form.keys()))
    elif request.form:
        kwargs["data"] = request.form
        logger.info("rqfarward body | type=form keys=%s", list(request.form.keys()))
    else:
        body = request.get_data()
        kwargs["data"] = body
        body_preview = body[:200] if body else b""
        logger.info("rqfarward body | type=raw size=%d preview=%s", len(body), body_preview)

    try:
        resp = http_requests.request(**kwargs)

        logger.info(
            "rqfarward OUT | status=%s content_type=%s content_length=%s",
            resp.status_code, resp.headers.get("Content-Type"), resp.headers.get("Content-Length"),
        )

        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP}

        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk

        return Response(generate(), status=resp.status_code, headers=resp_headers)

    except Exception as e:
        logger.error("rqfarward ERR | target=%s error=%s", target_url, str(e))
        return jsonify({"error": f"Gateway Error: {str(e)}"}), 502
