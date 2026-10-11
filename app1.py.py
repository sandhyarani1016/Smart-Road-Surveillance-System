```python
import os
import uuid

from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from vehicle import count_vehicles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "js"), filename)


@app.route("/images/<path:filename>")
def image_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "images"), filename)


@app.route("/uploads/<path:filename>")
def uploaded_video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/analyze", methods=["POST"])
def analyze():
    video = request.files.get("video")

    if not video or not video.filename:
        return "Please select a video first.", 400

    original_name = secure_filename(video.filename)
    extension = os.path.splitext(original_name)[1].lower()

    if extension not in {".mp4", ".avi", ".mov", ".mkv"}:
        return "Please upload MP4, AVI, MOV or MKV video.", 400

    filename = f"{uuid.uuid4().hex}{extension}"
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    video.save(video_path)

    try:
        vehicle_count, traffic_status = count_vehicles(video_path)
    except Exception:
        app.logger.exception("Video analysis failed")
        return (
            "Video analysis failed. Check the VS Code terminal.",
            500,
        )

    mime_types = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
    }

    result_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>Vehicle Analysis Results</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f3f6fb;
                color: #183153;
            }

            header {
                background: #102746;
                color: white;
                padding: 22px 7%;
                font-size: 22px;
                font-weight: bold;
            }

            header span {
                color: #53d8c2;
            }

            main {
                max-width: 1000px;
                width: 92%;
                margin: 35px auto;
            }

            .subtitle {
                color: #64748b;
                line-height: 1.6;
            }

            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 25px 0;
            }

            .card {
                background: white;
                border: 1px solid #e1e8f2;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 5px 20px #1831530c;
            }

            .label {
                color: #64748b;
                font-size: 14px;
                margin-bottom: 18px;
            }

            .count {
                font-size: 54px;
                font-weight: bold;
                color: #176b87;
            }

            .status {
                display: inline-block;
                font-size: 24px;
                font-weight: bold;
                padding: 12px 18px;
                border-radius: 9px;
            }

            .low {
                background: #e5f7ed;
                color: #167547;
            }

            .medium {
                background: #fff3d6;
                color: #986000;
            }

            .high {
                background: #fee9e7;
                color: #b42318;
            }

            .video-card h2 {
                margin-top: 0;
            }

            .filename {
                color: #64748b;
                overflow-wrap: anywhere;
                font-size: 14px;
            }

            video {
                display: block;
                width: 100%;
                max-height: 480px;
                background: #101828;
                border-radius: 10px;
                margin-top: 18px;
            }

            .button {
                display: inline-block;
                margin: 22px 10px 0 0;
                padding: 13px 20px;
                border-radius: 8px;
                background: #176b87;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }

            .button:hover {
                background: #10556d;
            }

            footer {
                text-align: center;
                padding: 25px;
                color: #718096;
                font-size: 13px;
            }

            @media (max-width: 650px) {
                .grid {
                    grid-template-columns: 1fr;
                }

                .count {
                    font-size: 44px;
                }

                .button {
                    display: block;
                    text-align: center;
                    margin-right: 0;
                }
            }
        </style>
    </head>

    <body>
        <header>
            Smart Road <span>Surveillance</span>
        </header>

        <main>
            <p style="color:#168a83;font-weight:bold;">
                ANALYSIS COMPLETE
            </p>

            <h1>Vehicle Analysis Results</h1>

            <p class="subtitle">
                Your traffic video has been processed successfully.
                View your vehicle count and estimated traffic density below.
            </p>

            <section class="grid">
                <div class="card">
                    <p class="label">Total Vehicles Counted</p>
                    <div class="count">{{ vehicle_count }}</div>
                    <p class="subtitle">
                        Vehicles counted by the detection algorithm
                    </p>
                </div>

                <div class="card">
                    <p class="label">Traffic Density</p>
                    <div class="status {{ traffic_class }}">
                        {{ traffic_status }}
                    </div>
                    <p class="subtitle">
                        Estimated traffic level
                    </p>
                </div>
            </section>

            <section class="card video-card">
                <h2>Analyzed Traffic Video</h2>
                <p class="filename">File: {{ original_name }}</p>

                <video controls preload="metadata">
                    <source src="/uploads/{{ filename }}"
                            type="{{ mime_type }}">
                    Your browser cannot play this video.
                </video>
            </section>

            <a class="button" href="/">&#8592; Back to Home</a>
            <a class="button" href="/">Analyze Another Video</a>
        </main>

        <footer>Smart Road Surveillance System</footer>
    </body>
    </html>
    """

    traffic_class = traffic_status.lower()

    return render_template_string(
        result_html,
        filename=filename,
        original_name=original_name,
        mime_type=mime_types.get(extension, "video/mp4"),
        vehicle_count=vehicle_count,
        traffic_status=traffic_status,
        traffic_class=traffic_class,
    )


@app.errorhandler(413)
def too_large(error):
    return "Video is too large. Maximum size is 200 MB.", 413


if __name__ == "__main__":
    app.run(debug=True)
```
