import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from flask import Flask, request, send_file, jsonify, render_template_string
from rembg import new_session, remove
from PIL import Image
import io
import zipfile
import threading
import time
import uuid

app = Flask(__name__)

# GLOBAL
session = new_session("isnet-general-use")
jobs = {}

print("Ecommerce AI loaded! Background processing enabled.")

@app.route("/")
def home():
    return """
    <div style="text-align:center;font-family:Arial;margin-top:50px">
        <h1 style="color:#e74c3c">Ecommerce Background Remover</h1>
        <p><strong>Upload up to 100 clothing photos</strong></p>
        <form id="form" enctype="multipart/form-data">
            <input type="file" name="files" multiple accept="image/*" required><br><br>
            <button type="submit" style="padding:15px 30px;font-size:18px;background:#27ae60;color:white;border:none;border-radius:8px">Upload & Process</button>
        </form>
        <div id="status" style="margin-top:20px"></div>
        <script>
            document.getElementById('form').onsubmit = async (e) => {
                e.preventDefault();
                const form = new FormData(e.target);
                const res = await fetch('/upload', { method: 'POST', body: form });
                const data = await res.json();
                document.getElementById('status').innerHTML = `Processing... ID: ${data.job_id}<br><span id="progress">0%</span>`;
                poll(data.job_id);
            };
            function poll(job_id) {
                setTimeout(async () => {
                    const res = await fetch(`/status/${job_id}`);
                    const data = await res.json();
                    if (data.status === 'done') {
                        window.location = `/download/${job_id}`;
                    } else if (data.status === 'processing') {
                        document.getElementById('progress').innerText = `${data.progress}%`;
                        poll(job_id);
                    }
                }, 1000);
            }
        </script>
    </div>
    """

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not 1 <= len(files) <= 100:
        return jsonify({"error": "1–100 images"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"files": files, "status": "processing", "progress": 0, "result": None}

    # Run in background
    threading.Thread(target=process_job, args=(job_id,)).start()

    return jsonify({"job_id": job_id})

def process_job(job_id):
    job = jobs[job_id]
    files = job["files"]
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile
