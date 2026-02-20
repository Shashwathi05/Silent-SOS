import cv2
import mediapipe as mp


def default_response():
    return {
        "distress": None,
        "risk": "NONE",
        "timestamp": None,
        "camera_id": "CAM_01",
        "confidence": 0.0
    }


def process_video(video_path):

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return default_response()

    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    frame_number = 0
    prev_center_y = None
    prev_height = None

    fall_detected = False
    recovery_detected = False
    collapse_timestamp = None

    inactivity_frames = 0
    max_inactivity_frames = 0

    max_velocity = 0
    max_height_drop = 1

    velocity_threshold = 55
    height_drop_threshold = 0.75

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

        indices = [
            mp_pose.PoseLandmark.LEFT_SHOULDER,
            mp_pose.PoseLandmark.RIGHT_SHOULDER,
            mp_pose.PoseLandmark.LEFT_HIP,
            mp_pose.PoseLandmark.RIGHT_HIP
        ]

        ys = [int(landmarks[i].y * h) for i in indices]

        center_y = sum(ys) / len(ys)
        body_height = max(ys) - min(ys)

        vertical_velocity = 0
        if prev_center_y is not None:
            vertical_velocity = (center_y - prev_center_y) * fps

        prev_center_y = center_y

        height_ratio = 1
        if prev_height and prev_height != 0:
            height_ratio = body_height / prev_height

        prev_height = body_height

        max_velocity = max(max_velocity, vertical_velocity)
        max_height_drop = min(max_height_drop, height_ratio)

        # ---------------- FALL DETECTION ---------------- #
        if not fall_detected:
            if vertical_velocity > velocity_threshold and height_ratio < height_drop_threshold:
                fall_detected = True
                collapse_timestamp = frame_number / fps
                inactivity_frames = 0

        else:
            # Recovery detection
            if height_ratio > 1.15 and vertical_velocity < -20:
                recovery_detected = True

            # Inactivity tracking
            if abs(vertical_velocity) < 4:
                inactivity_frames += 1
                max_inactivity_frames = max(max_inactivity_frames, inactivity_frames)
            else:
                inactivity_frames = 0

    cap.release()

    if not fall_detected:
        return default_response()

    inactivity_seconds = max_inactivity_frames / fps

    # ---------------- FINAL DECISION AFTER FULL VIDEO ---------------- #

    if recovery_detected:
        risk = "MEDIUM"
    else:
        if inactivity_seconds >= 15:
            risk = "CRITICAL"
        elif inactivity_seconds >= 8:
            risk = "HIGH"
        else:
            risk = "HIGH"  # If video ends with person down

    # Dynamic confidence
    velocity_score = min(max_velocity / 300, 1)
    height_score = min((1 - max_height_drop) / 0.5, 1)
    inactivity_score = min(inactivity_seconds / 15, 1)

    confidence = round(
        0.4 * velocity_score +
        0.3 * height_score +
        0.3 * inactivity_score, 2
    )

    confidence = max(confidence, 0.7)

    return {
        "distress": "collapse",
        "risk": risk,
        "timestamp": round(collapse_timestamp, 2),
        "camera_id": "CAM_01",
        "confidence": confidence
    }