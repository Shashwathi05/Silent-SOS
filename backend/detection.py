import cv2
import mediapipe as mp
import numpy as np

def process_video(video_path):

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {
            "distress": None,
            "risk": "NONE",
            "timestamp": None,
            "camera_id": "CAM_01"
        }

    fps = cap.get(cv2.CAP_PROP_FPS)

    collapse_frames = 0
    threshold_frames = 10
    frame_number = 0

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

            if vertical_diff < 100:
                collapse_frames += 1
            else:
                collapse_frames = 0

            if collapse_frames > threshold_frames:
                timestamp = frame_number / fps

                cap.release()

                return {
                    "distress": "collapse",
                    "risk": "HIGH",
                    "timestamp": round(timestamp, 2),
                    "camera_id": "CAM_01"
                }

    cap.release()

    return {
        "distress": None,
        "risk": "NONE",
        "timestamp": None,
        "camera_id": "CAM_01"
    }
