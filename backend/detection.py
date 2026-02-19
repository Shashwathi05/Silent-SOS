import cv2
import mediapipe as mp

def process_video(video_path):

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {
            "distress": None,
            "risk": "NONE",
            "timestamp": None,
            "camera_id": "CAM_01",
            "confidence": 0.0
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    collapse_frames = 0
    horizontal_frames = 0
    threshold_frames = 10
    frame_number = 0

    collapse_detected = False
    collapse_timestamp = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]

            h, w, _ = frame.shape
            y1 = int(left_shoulder.y * h)
            y2 = int(left_hip.y * h)

            vertical_diff = abs(y2 - y1)

            # Horizontal detection
            if vertical_diff < 100:
                horizontal_frames += 1
            else:
                horizontal_frames = 0

            # Initial collapse confirmation
            if horizontal_frames > threshold_frames and not collapse_detected:
                collapse_detected = True
                collapse_timestamp = frame_number / fps

            # If collapse already detected, continue counting inactivity
            if collapse_detected:
                inactivity_seconds = horizontal_frames / fps

                if inactivity_seconds > 5:
                    risk = "CRITICAL"
                    confidence = 0.95
                elif inactivity_seconds > 3:
                    risk = "HIGH"
                    confidence = 0.9
                else:
                    risk = "MEDIUM"
                    confidence = 0.75

                cap.release()

                return {
                    "distress": "collapse",
                    "risk": risk,
                    "timestamp": round(collapse_timestamp, 2),
                    "camera_id": "CAM_01",
                    "confidence": confidence
                }

    cap.release()

    return {
        "distress": None,
        "risk": "NONE",
        "timestamp": None,
        "camera_id": "CAM_01",
        "confidence": 0.0
    }
