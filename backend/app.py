import os
from flask import Flask, request, jsonify, send_from_directory
from detection import process_video

app = Flask(__name__, static_folder="../frontend")

UPLOAD_FOLDER = "backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

alerts_log = []
last_analysis = {
    "distress": None,
    "risk": "NONE",
    "timestamp": None,
    "camera_id": "CAM_01",
    "confidence": 0.0
}


@app.route("/")
def serve_dashboard():
    return send_from_directory(app.static_folder, "dashboard.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)
@app.route("/upload", methods=["POST"])
def upload():

    global last_analysis

    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files["video"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    result = process_video(file_path)

    # Always update last analysis
    last_analysis = result

    # If distress detected → log it
    if result["distress"]:
        alert_entry = {
            "id": len(alerts_log) + 1,
            "distress": result["distress"],
            "risk": result["risk"],
            "timestamp": result["timestamp"],
            "camera_id": result["camera_id"],
            "confidence": result["confidence"],
            "status": "ACTIVE"
        }

        alerts_log.append(alert_entry)

    # Always return full result (not just alert_entry)
    return jsonify(result)


@app.route("/acknowledge/<int:alert_id>", methods=["POST"])
def acknowledge(alert_id):
    for alert in alerts_log:
        if alert["id"] == alert_id:
            alert["status"] = "ACKNOWLEDGED"
            return jsonify(alert)

    return jsonify({"error": "Alert not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
@app.route("/latest", methods=["GET"])
def get_latest():
    return jsonify(last_analysis)
