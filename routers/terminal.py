import os
import subprocess
import shlex
from flask import Blueprint, request, jsonify
from config import settings

terminal_bp = Blueprint("terminal", __name__)


def check_token():
    token = request.args.get("token")
    if token != settings.webhook_secret:
        return False
    return True


@terminal_bp.route("/terminal", methods=["GET"])
def terminal_ui():
    if not check_token():
        return "Invalid token", 403
    return HTML_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"}


@terminal_bp.route("/terminal/exec", methods=["POST"])
def terminal_exec():
    if not check_token():
        return jsonify({"error": "Invalid token"}), 403

    data = request.get_json(silent=True)
    if not data or "cmd" not in data:
        return jsonify({"error": "Missing 'cmd'"}), 400

    cmd = data["cmd"].strip()
    cwd = data.get("cwd", os.getcwd())

    if not cmd:
        return jsonify({"output": ""}), 200

    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=60,
        )
        output = result.stdout + result.stderr
        return jsonify({
            "output": output if output else "(no output)",
            "code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Command timed out (60s)", "code": -1})
    except Exception as e:
        return jsonify({"output": f"Error: {e}", "code": -1})


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web Terminal</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0d0d0d;color:#00ff41;font-family:'DejaVu Sans Mono','Fira Code','Consolas',monospace;font-size:14px;height:100vh;display:flex;flex-direction:column}
  #output{flex:1;overflow-y:auto;padding:12px;white-space:pre-wrap;word-break:break-all;line-height:1.5}
  #output::-webkit-scrollbar{width:6px}
  #output::-webkit-scrollbar-track{background:#0d0d0d}
  #output::-webkit-scrollbar-thumb{background:#00ff4144;border-radius:3px}
  .prompt-line{display:flex;align-items:center;padding:6px 12px;border-top:1px solid #00ff4122;background:#111}
  .prompt{color:#00ff41;margin-right:8px;white-space:nowrap}
  #cmd{flex:1;background:transparent;border:none;color:#00ff41;font:inherit;outline:none;caret-color:#00ff41}
  #cmd::placeholder{color:#00ff4144}
  .error{color:#ff5555}
  .info{color:#888}
  .cd{color:#ffaa00}
</style>
</head>
<body>
<div id="output"><span class="info">Web Terminal v1.0 | Type 'help' for commands</span></div>
<div class="prompt-line">
  <span class="prompt" id="prompt">$</span>
  <input type="text" id="cmd" placeholder="type a command..." autofocus spellcheck="false" autocomplete="off">
</div>
<script>
const output=document.getElementById('output');
const input=document.getElementById('cmd');
const promptSpan=document.getElementById('prompt');
let cwd='/';

function print(text,cls=''){
  const line=document.createElement('div');
  line.textContent=text;
  if(cls)line.className=cls;
  output.appendChild(line);
  output.scrollTop=output.scrollHeight;
}

async function exec(cmd){
  if(!cmd.trim())return;
  print(`$ ${cmd}`,'cd');
  try{
    const res=await fetch('/terminal/exec?token='+encodeURIComponent(new URLSearchParams(location.search).get('token')),{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({cmd,cwd}),
    });
    const data=await res.json();
    if(data.output)print(data.output,data.code===0?'':'error');
    if(data.code!==0&&data.code!==undefined)print(`Exit code: ${data.code}`,'error');
  }catch(e){
    print(`Connection error: ${e.message}`,'error');
  }
}

input.addEventListener('keydown',async(e)=>{
  if(e.key==='Enter'){
    const cmd=input.value;
    input.value='';
    await exec(cmd);
    if(cmd.startsWith('cd ')){
      try{
        const r=await fetch('/terminal/exec?token='+encodeURIComponent(new URLSearchParams(location.search).get('token')),{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({cmd:'pwd',cwd}),
        });
        const d=await r.json();
        cwd=d.output.trim();
        promptSpan.textContent=cwd+' $';
      }catch(_){}
    }
  }
});
</script>
</body>
</html>"""
