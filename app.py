
import os
import uuid

from flask import (
    Flask,
    request,
    send_from_directory,
    render_template_string,
    url_for,
)
from werkzeug.utils import secure_filename

from vehicle import count_vehicles
from helmet_detection import detect_helmet


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

latest_helmet_result = {
    "rider_count": 0,
    "helmet_count": 0,
    "no_helmet_count": 0,
    "plate_count": 0,
    "helmet_status": "Not Analyzed"
}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


# ---------------- HOME AND STATIC FILES ----------------

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "css"), filename
    )


@app.route("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "js"), filename
    )


@app.route("/images/<path:filename>")
def image_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "images"), filename
    )


@app.route("/uploads/<path:filename>")
def uploaded_video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



# Store the latest traffic analysis result
latest_traffic_result = {
    "vehicle_count": None,
    "traffic_status": "Not Analyzed"
}



@app.route("/api/traffic-result")
def traffic_result():
    return latest_traffic_result


@app.route("/api/helmet-result")
def helmet_result():
    return latest_helmet_result
# ---------------- CAR COUNTING ----------------

@app.route("/analyze", methods=["POST"])
def analyze():
    video = request.files.get("video")

    if not video or not video.filename:
        return "Please select a video first.", 400

    original_name = secure_filename(video.filename)
    extension = os.path.splitext(original_name)[1].lower()

    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv"}

    if extension not in allowed_extensions:
        return "Please upload MP4, AVI, MOV or MKV video.", 400

    filename = f"{uuid.uuid4().hex}{extension}"
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    video.save(video_path)

    try:
        vehicle_count, traffic_status = count_vehicles(video_path)
        latest_traffic_result["vehicle_count"] = vehicle_count
        latest_traffic_result["traffic_status"] = traffic_status
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

    traffic_class = str(traffic_status).lower()

    if traffic_class not in {"low", "medium", "high"}:
        traffic_class = "medium"

    result_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>Vehicle Analysis Results</title>
        <style>
            * { box-sizing: border-box; }
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
            header span { color: #53d8c2; }
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
            .low { background: #e5f7ed; color: #167547; }
            .medium { background: #fff3d6; color: #986000; }
            .high { background: #fee9e7; color: #b42318; }
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
            .button:hover { background: #10556d; }
            footer {
                text-align: center;
                padding: 25px;
                color: #718096;
                font-size: 13px;
            }
            @media (max-width: 650px) {
                .grid { grid-template-columns: 1fr; }
                .count { font-size: 44px; }
                .button {
                    display: block;
                    text-align: center;
                    margin-right: 0;
                }
            }
        </style>
    </head>
    <body>
        <header>Smart Road <span>Surveillance</span></header>
        <main>
            <p style="color:#168a83;font-weight:bold;">
                ANALYSIS COMPLETE
            </p>
            <h1>Vehicle Analysis Results</h1>
            <p class="subtitle">
                Your traffic video has been processed.
                View the vehicle count and estimated traffic density below.
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
                    <p class="subtitle">Estimated traffic level</p>
                </div>
            </section>
            <section class="card">
                <h2>Analyzed Traffic Video</h2>
                <p class="filename">File: {{ original_name }}</p>
                <video controls preload="metadata">
                    <source src="{{ video_url }}" type="{{ mime_type }}">
                    Your browser cannot play this video.
                </video>
            </section>
            <a class="button" href="/">Back to Home</a>
            <a class="button" href="/">Analyze Another Video</a>
        </main>
        <footer>Smart Road Surveillance System</footer>
    </body>
    </html>
    """

    return render_template_string(
        result_html,
        filename=filename,
        video_url=url_for("uploaded_video", filename=filename),
        original_name=original_name,
        mime_type=mime_types[extension],
        vehicle_count=vehicle_count,
        traffic_status=traffic_status,
        traffic_class=traffic_class,
    )


# ---------------- HELMET DETECTION ----------------

@app.route("/helmet-detection", methods=["GET", "POST"])
def helmet_detection_route():

    if request.method == "GET":
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1">
            <title>Helmet Detection</title>
            <style>
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    padding: 35px 16px;
                    font-family: Arial, sans-serif;
                    background: #f3f6fb;
                    color: #183153;
                }
                .card {
                    max-width: 620px;
                    margin: 25px auto;
                    padding: 30px;
                    background: white;
                    border: 1px solid #e1e8f2;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px #18315312;
                }
                input {
                    width: 100%;
                    margin: 20px 0;
                }
                button, a {
                    display: inline-block;
                    padding: 12px 18px;
                    background: #176b87;
                    color: white;
                    border: 0;
                    border-radius: 8px;
                    text-decoration: none;
                    cursor: pointer;
                }
                .note { color: #64748b; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Helmet Detection</h1>
                <p class="note">
                    Upload a road image to detect riders, helmets
                    and other objects recognized by the model.
                </p>
                <form method="POST" enctype="multipart/form-data">
                    <input type="file" name="file"
                           accept=".jpg,.jpeg,.png" required>
                    <button type="submit">Analyze Image</button>
                </form>
                <a href="/">Back to Home</a>
            </div>
        </body>
        </html>
        """)

    uploaded_file = request.files.get("image")

    if not uploaded_file or not uploaded_file.filename:
        return "Please select an image first.", 400

    original_name = secure_filename(uploaded_file.filename)
    extension = os.path.splitext(original_name)[1].lower()

    if extension not in {".jpg", ".jpeg", ".png"}:
        return "Please upload a JPG, JPEG or PNG image.", 400

    unique_name = f"{uuid.uuid4().hex}{extension}"
    input_path = os.path.join(UPLOAD_FOLDER, unique_name)
    output_name = f"result_{uuid.uuid4().hex}.jpg"
    output_path = os.path.join(UPLOAD_FOLDER, output_name)

    uploaded_file.save(input_path)

    try:
        result = detect_helmet(input_path, output_path)
        global latest_helmet_result
        latest_helmet_result = {
            "rider_count": result["rider_count"],
            "helmet_count": result["helmet_count"],
            "no_helmet_count": result["no_helmet_count"],
            "plate_count": result["plate_count"],
            "helmet_status": result["helmet_status"]
        }

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1">
            <title>Helmet Detection Results</title>
            <style>
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    padding: 30px 16px;
                    font-family: Arial, sans-serif;
                    background: #f3f6fb;
                    color: #183153;
                }
                .card {
                    max-width: 850px;
                    margin: 20px auto;
                    padding: 25px;
                    background: white;
                    border: 1px solid #e1e8f2;
                    border-radius: 15px;
                }
                .summary {
                    display: grid;
                    grid-template-columns: repeat(
                        auto-fit, minmax(150px, 1fr)
                    );
                    gap: 12px;
                }
                .item {
                    padding: 15px;
                    background: #f3f6fb;
                    border-radius: 10px;
                }
                .item strong {
                    display: block;
                    font-size: 26px;
                    margin-top: 8px;
                    color: #176b87;
                }
                img {
                    display: block;
                    width: 100%;
                    height: auto;
                    border-radius: 10px;
                }
                li { margin: 10px 0; overflow-wrap: anywhere; }
                a {
                    display: inline-block;
                    margin: 10px 8px 0 0;
                    padding: 12px 18px;
                    background: #176b87;
                    color: white;
                    border-radius: 8px;
                    text-decoration: none;
                }
                .note { color: #64748b; line-height: 1.6; }
            </style>
        </head>
        <body>
            <section class="card">
                <h1>Helmet Detection Results</h1>
                <p class="note">
                    File: {{ original_name }}
                </p>

                <div class="summary">
                    <div class="item">
                        Riders
                        <strong>{{ result["rider_count"] }}</strong>
                    </div>
                    <div class="item">
                        Helmet detections
                        <strong>{{ result["helmet_count"] }}</strong>
                    </div>
                    <div class="item">
                        No Helmet detections
                        <strong>{{ result["no_helmet_count"] }}</strong>
                    </div>
                    <div class="item">
                        Number plate detections
                        <strong>{{ result["plate_count"] }}</strong>
                    </div>
                </div>

                <h2>Helmet Status</h2>
                <p>{{ result["helmet_status"] }}</p>

                <h2>Detected Objects</h2>
                {% if result["detections"] %}
                    <ul>
                    {% for item in result["detections"] %}
                        <li>
                            {{ item["class"] }} —
                            confidence {{ item["confidence"] }}
                        </li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <p>No objects were detected by the model.</p>
                {% endif %}

                <h2>Processed Image</h2>
                <img
                    src="{{ url_for(
                        'uploaded_video',
                        filename=output_name
                    ) }}"
                    alt="Image with model detections">

                <p class="note">
                    Results depend on model predictions and may be inaccurate.
                </p>

                <a href="/helmet-detection">Analyze Another Image</a>
                <a href="/">Back to Home</a>
            </section>
        </body>
        </html>
        """,
        result=result,
        original_name=original_name,
        output_name=output_name)

    except Exception:
        app.logger.exception("Helmet detection failed")
        return (
            "Helmet detection failed. Check the VS Code terminal "
            "for the error details.",
            500,
        )


# ---------------- ERROR HANDLER ----------------

@app.errorhandler(413)
def too_large(error):
    return "Uploaded file is too large. Maximum size is 200 MB.", 413


if __name__ == "__main__":
    app.run(debug=True)