import os
from datetime import datetime, timezone
from uuid import uuid4
from flask import Blueprint, request, jsonify
from auth import require_admin, create_admin_token
from config import settings
from database import get_conn

admin_bp = Blueprint("admin", __name__)

PANEL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClipX Admin</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;background:#0f0f0f;color:#e0e0e0;min-height:100vh}
  .login{display:flex;align-items:center;justify-content:center;min-height:100vh}
  .card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:40px;width:360px}
  .card h1{font-size:22px;margin-bottom:6px}
  .card p{color:#888;font-size:13px;margin-bottom:24px}
  input{width:100%;background:#111;border:1px solid #333;border-radius:8px;padding:10px 14px;color:#e0e0e0;font-size:14px;margin-bottom:12px;outline:none}
  input:focus{border-color:#555}
  button{width:100%;background:#fff;color:#000;border:none;border-radius:8px;padding:11px;font-size:14px;font-weight:600;cursor:pointer}
  button:hover{background:#ddd}
  .err{color:#f87171;font-size:13px;margin-top:10px}
  header{background:#1a1a1a;border-bottom:1px solid #2a2a2a;padding:14px 28px;display:flex;align-items:center;justify-content:space-between}
  header h1{font-size:18px;font-weight:700}
  .logout{background:transparent;color:#888;border:1px solid #333;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:13px;width:auto}
  .logout:hover{color:#e0e0e0;border-color:#555}
  .tabs{display:flex;gap:4px;padding:20px 28px 0}
  .tab{padding:8px 18px;border-radius:8px 8px 0 0;cursor:pointer;font-size:14px;background:#1a1a1a;border:1px solid #2a2a2a;border-bottom:none;color:#888}
  .tab.active{color:#e0e0e0;background:#222}
  .panel{background:#1a1a1a;border:1px solid #2a2a2a;margin:0 28px 28px;border-radius:0 12px 12px 12px;padding:24px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;padding:8px 12px;color:#666;border-bottom:1px solid #2a2a2a;font-weight:500}
  td{padding:8px 12px;border-bottom:1px solid #1e1e1e;vertical-align:middle}
  .content-cell{max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .del{background:transparent;color:#f87171;border:1px solid #3a1a1a;border-radius:5px;padding:3px 10px;cursor:pointer;font-size:12px;width:auto}
  .del:hover{background:#3a1a1a}
  .meta{color:#666;font-size:12px}
  .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
  .stat{background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:14px 20px;display:inline-block}
  .stat .n{font-size:24px;font-weight:700}
  .stat .l{font-size:12px;color:#666;margin-top:2px}
  .btn-sm{background:#222;color:#e0e0e0;border:1px solid #333;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:13px;width:auto}
  .btn-sm:hover{background:#2a2a2a}
  .btn-primary{background:#e0e0e0;color:#000;border:none;border-radius:6px;padding:7px 16px;cursor:pointer;font-size:13px;font-weight:600;width:auto}
  .btn-primary:hover{background:#fff}
  .empty{color:#555;padding:24px;text-align:center}
  #app{display:none}
  .overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);align-items:center;justify-content:center;z-index:100}
  .overlay.show{display:flex}
  .modal{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:32px;width:420px}
  .modal h2{font-size:17px;margin-bottom:20px}
  .modal input{margin-bottom:16px}
  .modal-actions{display:flex;gap:10px}
  .modal-actions button{flex:1}
  .btn-cancel{background:#222;color:#e0e0e0;border:1px solid #333;border-radius:8px;padding:10px;font-size:14px;cursor:pointer;width:auto}
  .btn-cancel:hover{background:#2a2a2a}
  .secret-box{background:#111;border:1px solid #2e4a2e;border-radius:8px;padding:14px 16px;margin:16px 0;font-family:monospace;font-size:13px;word-break:break-all;color:#4ade80;position:relative}
  .secret-box .copy-btn{position:absolute;top:8px;right:8px;background:#2a2a2a;border:1px solid #333;color:#e0e0e0;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;width:auto}
  .secret-note{color:#888;font-size:12px;margin-bottom:16px}
  .key-cell{font-family:monospace;font-size:12px;color:#888;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style>
</head>
<body>
<div class="login" id="loginView">
  <div class="card">
    <h1>ClipX Admin</h1>
    <p>Sign in to manage your clipboard sync</p>
    <input type="email" id="email" placeholder="Email" />
    <input type="password" id="password" placeholder="Password" onkeydown="if(event.key==='Enter')login()" />
    <button onclick="login()">Sign in</button>
    <div class="err" id="loginErr"></div>
  </div>
</div>
<div id="app">
  <header>
    <h1>ClipX</h1>
    <button class="logout" onclick="logout()">Sign out</button>
  </header>
  <div class="tabs">
    <div class="tab active" onclick="switchTab('clips',this)">Clips</div>
    <div class="tab" onclick="switchTab('files',this)">Files</div>
    <div class="tab" onclick="switchTab('devices',this)">Devices</div>
  </div>
  <div class="panel" id="tabContent"></div>
</div>
<div class="overlay" id="addDeviceOverlay">
  <div class="modal">
    <h2>Add Device</h2>
    <input type="text" id="newDeviceName" placeholder="Device name (e.g. MacBook, iPhone)" />
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeAddDevice()">Cancel</button>
      <button class="btn-primary" onclick="submitAddDevice()">Create</button>
    </div>
  </div>
</div>
<div class="overlay" id="secretOverlay">
  <div class="modal">
    <h2>Device Created</h2>
    <p class="secret-note">Copy this secret key now — it won't be shown again in full.</p>
    <div class="secret-box" id="secretValue">
      <button class="copy-btn" onclick="copySecret()">Copy</button>
      <span id="secretText"></span>
    </div>
    <button class="btn-primary" style="width:100%;margin-top:4px" onclick="closeSecret()">Done</button>
  </div>
</div>
<script>
let token = localStorage.getItem('clipx_token') || '';
const BASE = '/v1';

async function api(path, opts={}) {
  const r = await fetch(BASE + path, {
    ...opts,
    headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', ...(opts.headers||{}) }
  });
  if (r.status === 401) { logout(); return null; }
  if (!r.ok) return null;
  if (r.status === 204) return true;
  return r.json();
}

async function login() {
  const r = await fetch('/v1/admin/login', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email: document.getElementById('email').value, password: document.getElementById('password').value})
  });
  if (!r.ok) { document.getElementById('loginErr').textContent = 'Invalid credentials'; return; }
  token = (await r.json()).token;
  localStorage.setItem('clipx_token', token);
  showApp();
}

function logout() {
  localStorage.removeItem('clipx_token');
  token = '';
  document.getElementById('loginView').style.display = 'flex';
  document.getElementById('app').style.display = 'none';
}

function showApp() {
  document.getElementById('loginView').style.display = 'none';
  document.getElementById('app').style.display = 'block';
  switchTab('clips', document.querySelector('.tab'));
}

function switchTab(name, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  loadTab(name);
}

async function loadTab(name) {
  document.getElementById('tabContent').innerHTML = '<div class="empty">Loading...</div>';
  if (name === 'clips') await renderClips();
  if (name === 'files') await renderFiles();
  if (name === 'devices') await renderDevices();
}

function fmt(iso) { return iso ? new Date(iso).toLocaleString() : 'Never'; }
function trunc(s, n=80) { return s && s.length > n ? s.slice(0,n)+'...' : (s||''); }
function maskKey(k) { return k ? k.slice(0,8)+'...' : ''; }

async function renderClips() {
  const data = await api('/admin/clips');
  const c = document.getElementById('tabContent');
  if (!data) { c.innerHTML = '<div class="empty">Failed to load</div>'; return; }
  c.innerHTML = `<div class="top"><div class="stat"><div class="n">${data.total}</div><div class="l">Total clips</div></div><button class="btn-sm" onclick="bulkDeleteClips()">Delete all</button></div>
    ${data.clips.length === 0 ? '<div class="empty">No clips yet</div>' : `<table><tr><th>Content</th><th>Device</th><th>Created</th><th></th></tr>
    ${data.clips.map(c=>`<tr><td class="content-cell" title="${c.content.replace(/"/g,'&quot;')}">${trunc(c.content)}</td><td class="meta">${c.device_name||c.device_id}</td><td class="meta">${fmt(c.created_at)}</td><td><button class="del" onclick="deleteClip('${c.id}')">Delete</button></td></tr>`).join('')}</table>`}`;
}

async function deleteClip(id) { await api('/admin/clips/'+id,{method:'DELETE'}); renderClips(); }
async function bulkDeleteClips() { if(!confirm('Delete ALL clips?'))return; await api('/admin/clips',{method:'DELETE'}); renderClips(); }

async function renderFiles() {
  const data = await api('/admin/files');
  const c = document.getElementById('tabContent');
  if (!data) { c.innerHTML = '<div class="empty">Failed to load</div>'; return; }
  c.innerHTML = `<div class="top"><div class="stat"><div class="n">${data.total}</div><div class="l">Active files</div></div></div>
    ${data.files.length === 0 ? '<div class="empty">No active files</div>' : `<table><tr><th>Filename</th><th>Size</th><th>Device</th><th>Expires</th><th></th></tr>
    ${data.files.map(f=>`<tr><td>${f.filename}</td><td class="meta">${(f.size/1024).toFixed(1)} KB</td><td class="meta">${f.device_name||f.device_id}</td><td class="meta">${fmt(f.expires_at)}</td><td><button class="del" onclick="deleteFile('${f.id}')">Delete</button></td></tr>`).join('')}</table>`}`;
}

async function deleteFile(id) { await api('/admin/files/'+id,{method:'DELETE'}); renderFiles(); }

async function renderDevices() {
  const data = await api('/admin/devices');
  const c = document.getElementById('tabContent');
  if (!data) { c.innerHTML = '<div class="empty">Failed to load</div>'; return; }
  c.innerHTML = `<div class="top"><div class="stat"><div class="n">${data.devices.length}</div><div class="l">Devices</div></div><button class="btn-primary" onclick="openAddDevice()">+ Add Device</button></div>
    ${data.devices.length === 0 ? '<div class="empty">No devices yet. Add one to get started.</div>' : `<table><tr><th>Name</th><th>Secret Key</th><th>Created</th><th>Last Seen</th><th></th></tr>
    ${data.devices.map(d=>`<tr><td>${d.device_name}</td><td class="key-cell" title="${d.secret_key}">${maskKey(d.secret_key)}</td><td class="meta">${fmt(d.created_at)}</td><td class="meta">${fmt(d.last_seen)}</td><td><button class="del" onclick="removeDevice('${d.device_id}')">Remove</button></td></tr>`).join('')}</table>`}`;
}

async function removeDevice(id) { if(!confirm('Remove this device?'))return; await api('/admin/devices/'+id,{method:'DELETE'}); renderDevices(); }

function openAddDevice() {
  document.getElementById('newDeviceName').value = '';
  document.getElementById('addDeviceOverlay').classList.add('show');
  setTimeout(()=>document.getElementById('newDeviceName').focus(),50);
}
function closeAddDevice() { document.getElementById('addDeviceOverlay').classList.remove('show'); }

async function submitAddDevice() {
  const name = document.getElementById('newDeviceName').value.trim();
  if (!name) return;
  const data = await api('/admin/devices', {method:'POST', body: JSON.stringify({name})});
  if (!data) return;
  closeAddDevice();
  document.getElementById('secretText').textContent = data.secret_key;
  document.getElementById('secretOverlay').classList.add('show');
  renderDevices();
}

function copySecret() {
  navigator.clipboard.writeText(document.getElementById('secretText').textContent);
  document.querySelector('.copy-btn').textContent = 'Copied!';
  setTimeout(()=>document.querySelector('.copy-btn').textContent='Copy',2000);
}
function closeSecret() { document.getElementById('secretOverlay').classList.remove('show'); }

document.addEventListener('keydown', e => { if(e.key==='Escape'){closeAddDevice();closeSecret();} });
if (token) showApp();
</script>
</body>
</html>"""


# ── Panel ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_bp.route("/admin")
def admin_panel():
    from flask import make_response
    return make_response(PANEL_HTML, 200, {"Content-Type": "text/html"})


# ── Login ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/v1/admin/login", methods=["POST"])
def admin_login():
    body = request.get_json()
    if body.get("email") != settings.admin_email or body.get("password") != settings.admin_password:
        return jsonify({"detail": "Invalid credentials"}), 401
    return jsonify({"token": create_admin_token()})


# ── Devices ───────────────────────────────────────────────────────────────────

@admin_bp.route("/v1/admin/devices", methods=["POST"])
@require_admin
def create_device():
    body = request.get_json()
    device_id = str(uuid4())
    secret_key = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO devices (device_id, device_name, secret_key, created_at) VALUES (?, ?, ?, ?)",
            (device_id, body["name"], secret_key, now),
        )
    return jsonify({"device_id": device_id, "device_name": body["name"], "secret_key": secret_key, "created_at": now}), 201


@admin_bp.route("/v1/admin/devices", methods=["GET"])
@require_admin
def admin_list_devices():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT device_id, device_name, secret_key, created_at, last_seen FROM devices ORDER BY created_at DESC"
        ).fetchall()
    return jsonify({"devices": [dict(r) for r in rows]})


@admin_bp.route("/v1/admin/devices/<device_id>", methods=["DELETE"])
@require_admin
def admin_remove_device(device_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
    return "", 204


# ── Clips ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/v1/admin/clips", methods=["GET"])
@require_admin
def admin_clips():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
        rows = conn.execute(
            "SELECT id, device_id, device_name, content, created_at FROM clips ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return jsonify({"total": total, "clips": [dict(r) for r in rows]})


@admin_bp.route("/v1/admin/clips/<clip_id>", methods=["DELETE"])
@require_admin
def admin_delete_clip(clip_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
    return "", 204


@admin_bp.route("/v1/admin/clips", methods=["DELETE"])
@require_admin
def admin_delete_all_clips():
    with get_conn() as conn:
        conn.execute("DELETE FROM clips")
    return "", 204


# ── Files ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/v1/admin/files", methods=["GET"])
@require_admin
def admin_files():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM files WHERE expires_at > ?", (now,)).fetchone()[0]
        rows = conn.execute(
            "SELECT id, device_id, device_name, filename, size, created_at, expires_at FROM files WHERE expires_at > ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (now, limit, offset),
        ).fetchall()
    return jsonify({"total": total, "files": [dict(r) for r in rows]})


@admin_bp.route("/v1/admin/files/<file_id>", methods=["DELETE"])
@require_admin
def admin_delete_file(file_id):
    with get_conn() as conn:
        row = conn.execute("SELECT filepath FROM files WHERE id = ?", (file_id,)).fetchone()
        if row and os.path.exists(row["filepath"]):
            os.remove(row["filepath"])
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    return "", 204
