from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/upload", methods=["POST"])
def upload():
    # TEMPORARY DUMMY RESPONSE
    return jsonify({
        "distress": "collapse",
        "risk": "HIGH",
        "timestamp": 2.8,
        "camera_id": "CAM_01"
    })

if __name__ == "__main__":
    app.run(debug=True)