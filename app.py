import os
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

from flask import Flask, request, send_file, render_template_string
from PIL import Image
import io
import zipfile
import numpy as np
import torch
from segment_anything import sam_model_registry, SamPredictor

app = Flask(__name__)

# LOAD SAM MODEL ON STARTUP
print("Loading Segment Anything Model (SAM)...")
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
predictor = SamPredictor(sam)
print("SAM loaded! Click to remove clothing.")

# Download model if not exists (Render will cache)
import urllib.request
if not os.path.exists("sam_vit_h_4b8939.pth"):
    print("Downloading SAM model (~2.4GB)...")
    urllib.request.urlretrieve(
        "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
        "sam_vit_h_4b8939.pth"
    )

@app.route("/")
def home():
    return """
    <div style="text-align:center;font-family:Arial;margin-top:30px">
        <h1 style="color:#e74c3c">Click-to-Remove Clothing</h1>
        <p>Upload image → <strong>Click on the shirt</strong> → Get transparent PNG</p>
        <canvas id="canvas" width="800" height="600" style="border:2px solid #ccc; cursor: crosshair;"></canvas><br><br>
        <button onclick="undo()" style="padding:10px 20px">Undo Click</button>
        <button onclick="process()" style="padding:15px 30px;font-size:18px;background:#27ae60;color:white;border:none;border-radius:8px">Remove Background</button>
        <input type="file" id="file" accept="image/*" style="display:none">
        <script>
            let img = new Image();
            let clicks = [];
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');

            document.getElementById('file').onchange = (e) => {
                const file = e.target.files[0];
                const reader = new FileReader();
                reader.onload = (ev) => {
                    img.src = ev.target.result;
                    img.onload = () => {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.drawImage(img, 0, 0);
                        clicks = [];
                    };
                };
                reader.readAsDataURL(file);
            };

            canvas.onclick = (e) => {
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                clicks.push([x, y]);
                ctx.fillStyle = 'red';
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, 2*Math.PI);
                ctx.fill();
            };

            function undo() {
                clicks.pop();
                ctx.drawImage(img, 0, 0);
                clicks.forEach(([x, y]) => {
                    ctx.fillStyle = 'red';
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2*Math.PI);
                    ctx.fill();
                });
            }

            function process() {
                if (clicks.length === 0) return alert("Click on the clothing first!");
                const form = new FormData();
                form.append('image', document.getElementById('file').files[0]);
                form.append('clicks', JSON.stringify(clicks));
                fetch('/upload', { method: 'POST', body: form })
                    .then(r => r.blob())
                    .then(blob => {
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'clean-clothing.png';
                        a.click();
                    });
            }

            // Auto-open file picker
            document.getElementById('file').click();
        </script>
        <br><br>
        <small>Made by <a href="https://x.com/cracksellington">@cracksellington</a> • Click → Remove</small>
    </div>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if 'image' not in request.files:
        return "No image", 400

    img_file = request.files['image']
    clicks = request.form.get('clicks')
    if not clicks:
        return "No clicks", 400

    clicks = eval(clicks)  # [[x, y], ...]

    # Load image
    img = Image.open(img_file.stream).convert("RGB")
    img_np = np.array(img)

    # Set image in predictor
    predictor.set_image(img_np)

    # Convert clicks to input points
    input_points = np.array(clicks)
    input_labels = np.ones(len(clicks))  # 1 = foreground

    # Predict mask
    masks, _, _ = predictor.predict(
        point_coords=input_points,
        point_labels=input_labels,
        multimask_output=False
    )

    mask = masks[0]  # First mask

    # Apply mask
    rgba = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rgb = img.convert("RGB")
    rgba.paste(rgb, (0, 0), Image.fromarray((mask * 255).astype(np.uint8)))

    # Save to buffer
    buf = io.BytesIO()
    rgba.save(buf, 'PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png', download_name='clean-clothing.png')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
