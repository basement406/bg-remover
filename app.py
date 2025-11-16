import os
# FORCE CPU ONLY — THIS IS THE KEY
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"
os.environ["REMGB_MODEL"] = "u2net"  # lightweight model

from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io
import zipfile

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <div style="text-align:center;font-family:Arial;margin-top:50px">
        <h1 style="color:#e74c3c">Background Remover</h1>
        <p><strong>Upload up to 100 images</strong> → Get transparent PNGs!</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="files" multiple accept="image/*" required style="padding:10px"><br><br>
            <button type="submit" style="padding:15px 30px;font-size:18px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer">Remove Backgrounds</button>
        </form>
        <br>
        <small>Made by <a href="https://x.com/cracksellington">@cracksellington</a> • Free & Open Source</small>
    </div>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return "<h3>No files</h3>", 400

    files = request.files.getlist("files")
    if not 1 <= len(files) <= 100:
        return "<h3>1–100 images only</h3>", 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            try:
                img = Image.open(file.stream).convert("RGBA")
                output = remove(img)
                img_io = io.BytesIO()
                output.save(img_io, 'PNG')
                img_io.seek(0)
                name = os.path.splitext(file.filename)[0] + ".png"
                zf.writestr(name, img_io.getvalue())
            except Exception as e:
                print(f"Error: {e}")

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='nobg-cracksellington.zip'
    )

# RENDER AUTO-DETECTS THIS
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
