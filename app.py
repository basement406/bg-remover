import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from flask import Flask, request, send_file
from rembg import new_session, remove
from PIL import Image
import io
import zipfile

app = Flask(__name__)

# BEST MODEL FOR CLOTHING
print("Loading ECOMMERCE AI (isnet-general-use)...")
session = new_session("isnet-general-use")
print("Model loaded! Ready for 100 clothing items.")

@app.route("/")
def home():
    return """
    <div style="text-align:center;font-family:Arial;margin-top:50px">
        <h1 style="color:#e74c3c">Ecommerce Background Remover</h1>
        <p><strong>Upload up to 100 clothing photos</strong> → Get clean PNGs!</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="files" multiple accept="image/*" required style="padding:10px"><br><br>
            <button type="submit" style="padding:15px 30px;font-size:18px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer">Remove Backgrounds</button>
        </form>
        <p style="color:green">Auto-detects clothing • Razor-sharp edges • No clicks</p>
        <br>
        <small>Made by <a href="https://x.com/cracksellington">@cracksellington</a></small>
    </div>
    """

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not 1 <= len(files) <= 100:
        return "1–100 images only", 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            try:
                img = Image.open(file.stream).convert("RGBA")
                output = remove(img, session=session, alpha_matting=True)
                img_io = io.BytesIO()
                output.save(img_io, 'PNG')
                img_io.seek(0)
                name = os.path.splitext(file.filename)[0] + ".png"
                zf.writestr(name, img_io.getvalue())
            except Exception as e:
                print(f"Error: {e}")

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', download_name='clean-clothing.zip')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
