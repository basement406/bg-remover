import os
# FORCE CPU ONLY — NO GPU
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io
import zipfile

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1 style="font-family:Arial;color:#2c3e50;text-align:center">Background Remover by @cracksellington</h1>
    <p style="text-align:center">Upload up to <strong>100 images</strong> → Get ZIP with transparent PNGs!</p>
    <form action="/upload" method="post" enctype="multipart/form-data" style="text-align:center">
        <input type="file" name="files" multiple accept="image/*" required style="padding:10px"><br><br>
        <button type="submit" style="padding:12px 24px;font-size:18px;background:#e74c3c;color:white;border:none;border-radius:8px;cursor:pointer">Remove Backgrounds</button>
    </form>
    <br>
    <small style="display:block;text-align:center">Free • Open Source • <a href="https://x.com/cracksellington">@cracksellington</a></small>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return "<h3>No files uploaded</h3>", 400

    files = request.files.getlist("files")
    if not 1 <= len(files) <= 100:
        return "<h3>Upload 1 to 100 images</h3>", 400

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

# RENDER FIX: Use $PORT
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
