import os
os.environ["ONNXRUNTIME_EXECUTION_PROVID.....

import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "[CPUExecutionProvider]"

from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io
import zipfile

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1 style="font-family:Arial;color:#2c3e50">Background Remover by @cracksellington</h1>
    <p>Upload up to <strong>100 images</strong> → Get ZIP with transparent backgrounds!</p>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="files" multiple accept="image/*" required><br><br>
        <button type="submit" style="padding:10px 20px;font-size:16px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer">Remove Backgrounds</button>
    </form>
    <br>
    <small>Live on Render • <a href="https://x.com/cracksellington">@cracksellington</a></small>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return "No files uploaded", 400

    files = request.files.getlist("files")
    if not 1 <= len(files) <= 100:
        return "Please upload 1 to 100 images", 400

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
                print(f"Error processing {file.filename}: {e}")

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='nobg-by-cracksellington.zip'
    )

# THIS IS THE KEY LINE
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
