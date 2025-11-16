import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from flask import Flask, request, send_file, jsonify
from rembg import new_session, remove
from PIL import Image
import io
import zipfile
import threading
import uuid

app = Flask(__name__)

# LOAD MODEL ONCE
print("Loading ECOMMERCE AI (isnet-general-use)...")
session = new_session("isnet-general-use")
print("Model loaded! 100 items = <1.5GB RAM.")

jobs = {}

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
        <div id="status" style="margin-top:20px;font-weight:bold"></div>
        <script>
            document.getElementById('form').onsubmit = async (e) => {
                e.preventDefault();
                const form = new FormData(e.target);
                const res = await fetch('/upload', { method: 'POST', body: form });
                const data = await res.json();
                document.getElementById('status').innerHTML = `Processing... <span id="progress">0%</span>`;
                poll(data.job_id);
            };
            function poll(job_id) {
                setTimeout(async () => {
                    const res = await fetch(`/status/${job_id}`);
                    const data = await res.json();
                    if (data.status === 'done') {
                        window.location = `/download/${job_id}`;
                    } else {
                        document.getElementById('progress').innerText = data.progress + '%';
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

    threading.Thread(target=process_job, args=(job_id,)).start()
    return jsonify({"job_id": job_id})

def process_job(job_id):
    job = jobs[job_id]
    files = job["files"]
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:  # <-- COLON FIXED
        for i, file in enumerate(files):
            try:
                img = Image.open(file.stream).convert("RGBA")
                output = remove(img, session=session, alpha_matting=False)
                img_io = io.BytesIO()
                output.save(img_io, 'PNG')
                img_io.seek(0)
                name = os.path.splitext(file.filename)[0] + ".png"
                zf.writestr(name, img_io.getvalue())
                job["progress"] = int((i + 1) / len(files) * 100)
            except Exception as e:
                print(f"Error: {e}")

    zip_buffer.seek(0)
    job["result"] = zip_buffer.getvalue()
    job["status"] = "done"

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id, {})
    return jsonify({
        "status": job.get("status", "not_found"),
        "progress": job.get("progress", 0)
    })

@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id, {})
    if job.get("status") != "done":
        return "Not ready", 400
    return send_file(
        io.BytesIO(job["result"]),
        mimetype='application/zip',
        as_attachment=True,
        download_name='clean-clothing.zip'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
