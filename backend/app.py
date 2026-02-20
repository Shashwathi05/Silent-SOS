import os
from flask import Flask, request, jsonify, send_from_directory
from detection import process_video

app = Flask(__name__, static_folder="../frontend")

UPLOAD_FOLDER = "backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

alerts_log = []
last_analysis = {
    "status": "idle",
    "result": None
}

# Serve dashboard
@app.route("/")
def serve_dashboard():
    return send_from_directory(app.static_folder, "dashboard.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Upload + Analyze
@app.route("/upload", methods=["POST"])
def upload():

    global last_analysis

    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files["video"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    last_analysis["status"] = "processing"

    result = process_video(file_path)

    last_analysis["status"] = "done"
    last_analysis["result"] = result

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
        return jsonify(alert_entry)

    return jsonify(result)

# Return all alerts
@app.route("/alerts", methods=["GET"])
def get_alerts():
    return jsonify(alerts_log)

# Return latest analysis status
@app.route("/latest", methods=["GET"])
def get_latest():
    return jsonify(last_analysis)

# Acknowledge alert
@app.route("/acknowledge/<int:alert_id>", methods=["POST"])
def acknowledge(alert_id):
    for alert in alerts_log:
        if alert["id"] == alert_id:
            alert["status"] = "ACKNOWLEDGED"
            return jsonify(alert)

    return jsonify({"error": "Alert not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
