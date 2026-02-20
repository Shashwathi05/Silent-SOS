import cv2
import mediapipe as mp
import math


def calculate_angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return abs(math.degrees(math.atan2(dx, dy)))


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

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    frame_number = 0
    prev_center_y = None
    prev_height = None

    state = "UPRIGHT"
    collapse_timestamp = None
    inactivity_frames = 0

    velocity_threshold = 80
    height_drop_threshold = 0.35
    inactivity_threshold_frames = int(fps * 4)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            continue

        landmarks = results.pose_landmarks.landmark
        h, w, _ = frame.shape

        # Get key landmarks
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        # Convert to pixel space
        points = [
            (int(left_shoulder.x * w), int(left_shoulder.y * h)),
            (int(right_shoulder.x * w), int(right_shoulder.y * h)),
            (int(left_hip.x * w), int(left_hip.y * h)),
            (int(right_hip.x * w), int(right_hip.y * h))
        ]

        ys = [p[1] for p in points]

        center_y = sum(ys) / len(ys)
        body_height = max(ys) - min(ys)

        # Velocity of center drop
        vertical_velocity = 0
        if prev_center_y is not None:
            vertical_velocity = (center_y - prev_center_y) * fps

        prev_center_y = center_y

        # Height change ratio
        height_ratio = 1
        if prev_height is not None and prev_height != 0:
            height_ratio = body_height / prev_height

        prev_height = body_height

        # ---------------- STATE MACHINE ---------------- #

        if state == "UPRIGHT":
            if vertical_velocity > velocity_threshold:
                state = "FALLING"

        elif state == "FALLING":
            # If body height collapses significantly
            if height_ratio < height_drop_threshold:
                state = "HORIZONTAL"
                collapse_timestamp = frame_number / fps
                inactivity_frames = 0

        elif state == "HORIZONTAL":

            if abs(vertical_velocity) < 10:
                inactivity_frames += 1
            else:
                inactivity_frames = 0

            if inactivity_frames > inactivity_threshold_frames:
                state = "INACTIVE"
                break

    cap.release()

    if state == "INACTIVE":

        inactivity_seconds = inactivity_frames / fps

        if inactivity_seconds > 8:
            risk = "CRITICAL"
            confidence = 0.95
        elif inactivity_seconds > 4:
            risk = "HIGH"
            confidence = 0.9
        else:
            risk = "MEDIUM"
            confidence = 0.8

        return {
            "distress": "collapse",
            "risk": risk,
            "timestamp": round(collapse_timestamp, 2),
            "camera_id": "CAM_01",
            "confidence": confidence
        }

    return {
        "distress": None,
        "risk": "NONE",
        "timestamp": None,
        "camera_id": "CAM_01",
        "confidence": 0.0
    }