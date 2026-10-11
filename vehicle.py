
import os
import sys
import cv2
import numpy as np


print("VEHICLE.PY STARTED", flush=True)


def count_vehicles(video_path):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)

    print("Video opened:", cap.isOpened(), flush=True)
    print("Total frames:", cap.get(cv2.CAP_PROP_FRAME_COUNT), flush=True)
    print("FPS:", cap.get(cv2.CAP_PROP_FPS), flush=True)

    if not cap.isOpened():
        cap.release()
        raise ValueError("Could not open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        fps = 25.0

    duration = total_frames / fps if total_frames > 0 else 0

    detector = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=50,
        detectShadows=False
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (5, 5)
    )

    vehicle_count = 0
    frame_number = 0
    count_line = None
    tracks = {}
    next_track_id = 0

    min_width = 50
    min_height = 40
    match_distance = 60

    print("Video processing started...", flush=True)

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            frame_number += 1
            height, width = frame.shape[:2]

            if count_line is None:
                count_line = int(height * 0.65)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 5)

            mask = detector.apply(blur)
            mask = cv2.dilate(
                mask, np.ones((5, 5), np.uint8), iterations=1
            )
            mask = cv2.morphologyEx(
                mask, cv2.MORPH_CLOSE, kernel
            )

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            detections = []

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                if w < min_width or h < min_height:
                    continue

                cx = x + w // 2
                cy = y + h // 2
                detections.append((cx, cy))

            new_tracks = {}
            used_ids = set()

            for cx, cy in detections:
                best_id = None
                best_dist = match_distance

                for track_id, old in tracks.items():
                    if track_id in used_ids:
                        continue

                    old_x, old_y, counted = old
                    distance = np.hypot(cx - old_x, cy - old_y)

                    if distance < best_dist:
                        best_dist = distance
                        best_id = track_id

                if best_id is None:
                    best_id = next_track_id
                    next_track_id += 1
                    new_tracks[best_id] = (cx, cy, False)

                else:
                    old_x, old_y, counted = tracks[best_id]
                    used_ids.add(best_id)

                    # Count vehicles crossing the line downward.
                    if (
                        not counted
                        and old_y < count_line
                        and cy >= count_line
                    ):
                        vehicle_count += 1
                        counted = True

                    new_tracks[best_id] = (cx, cy, counted)

            tracks = new_tracks

            if frame_number % 100 == 0:
                print(
                    f"Processed {frame_number}/{int(total_frames)} frames",
                    flush=True
                )

    finally:
        cap.release()

    if duration > 0:
        rate = vehicle_count * 30 / duration
    else:
        rate = vehicle_count

    if rate <= 10:
        traffic_status = "LOW"
    elif rate <= 25:
        traffic_status = "MEDIUM"
    else:
        traffic_status = "HIGH"

    print("Vehicle Count:", vehicle_count, flush=True)
    print("Traffic Density:", traffic_status, flush=True)

    return vehicle_count, traffic_status


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python vehicle.py "path_to_video.mp4"')
        sys.exit(1)

    try:
        count_vehicles(sys.argv[1])
    except Exception as error:
        print("Error:", error, flush=True)
        sys.exit(1)