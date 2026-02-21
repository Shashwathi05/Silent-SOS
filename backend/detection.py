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

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    frame_number = 0
    prev_center_y = None
    prev_height = None

    state = "UPRIGHT"
    fall_timestamp = None

    recovery_frames = 0
    recovery_limit = int(fps * 1.5)  # ~1.5 sec upright = recovered

    velocity_threshold = 70
    height_ratio_threshold = 0.45

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

        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        points = [
            (int(left_shoulder.x * w), int(left_shoulder.y * h)),
            (int(right_shoulder.x * w), int(right_shoulder.y * h)),
            (int(left_hip.x * w), int(left_hip.y * h)),
            (int(right_hip.x * w), int(right_hip.y * h))
        ]

        ys = [p[1] for p in points]

        center_y = sum(ys) / len(ys)
        body_height = max(ys) - min(ys)

        vertical_velocity = 0
        if prev_center_y is not None:
            vertical_velocity = (center_y - prev_center_y) * fps

        height_ratio = 1
        if prev_height is not None and prev_height != 0:
            height_ratio = body_height / prev_height

        prev_center_y = center_y
        prev_height = body_height

        # ---------------- STATE MACHINE ---------------- #

        if state == "UPRIGHT":
            if vertical_velocity > velocity_threshold:
                state = "FALLING"

        elif state == "FALLING":
            if height_ratio < height_ratio_threshold:
                state = "DOWN"
                fall_timestamp = frame_number / fps

        elif state == "DOWN":

            # If body regains height → recovery
            if height_ratio > 0.8:
                recovery_frames += 1
            else:
                recovery_frames = 0

            if recovery_frames > recovery_limit:
                state = "RECOVERED"
                break

    cap.release()

    # ---------------- FINAL DECISION ---------------- #

    if state == "RECOVERED":
        return {
            "distress": "collapse",
            "risk": "LOW",
            "timestamp": round(fall_timestamp, 2),
            "camera_id": "CAM_01",
            "confidence": 0.85
        }

    # 🔥 KEY CHANGE:
    # If fall happened but never recovered before video ended → HIGH
    if state == "DOWN":
        return {
            "distress": "collapse",
            "risk": "HIGH",
            "timestamp": round(fall_timestamp, 2),
            "camera_id": "CAM_01",
            "confidence": 0.95
        }

    return {
        "distress": None,
        "risk": "NONE",
        "timestamp": None,
        "camera_id": "CAM_01",
        "confidence": 0.0
    }