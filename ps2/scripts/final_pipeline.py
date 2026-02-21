import cv2
import numpy as np
import math
from ultralytics import YOLO
from collections import deque
from skimage.metrics import structural_similarity as ssim

# -------- SETTINGS --------
MODEL_PATH = "best.pt"   # trained model
VIDEO_PATH = "input.mp4"
OUTPUT_PATH = "output_annotated.mp4"
MAX_TRAIL = 30

# -------- LOAD MODEL --------
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (w, h))

trajectory = deque(maxlen=MAX_TRAIL)
displacements = []
prev_center = None
prev_frame = None

frame_id = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    label = "NORMAL"
    confidence = 0.0

    results = model(frame, verbose=False)

    center = None

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            name = model.names[cls]

            if name == "cricket_ball":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                center = ((x1+x2)//2, (y1+y2)//2)

                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.circle(frame, center, 5, (0,0,255), -1)

    # ----- BALL DISPLACEMENT -----
    if center is not None and prev_center is not None:
        d = math.dist(center, prev_center)
        displacements.append(d)

        if len(displacements) > 10:
            avg_d = np.mean(displacements[-10:])

            if avg_d > 0:
                if d > 2.5 * avg_d:
                    label = "DROP"
                    confidence = 0.9

                elif d < 2 and prev_frame is not None:
                    gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                    gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    score = ssim(gray1, gray2)

                    if score > 0.99:
                        label = "MERGE"
                        confidence = 0.9

    # ----- DRAW TRAJECTORY -----
    trajectory.appendleft(center)

    for i in range(1, len(trajectory)):
        if trajectory[i-1] is None or trajectory[i] is None:
            continue
        thickness = int(np.sqrt(MAX_TRAIL / float(i+1)) * 2)
        cv2.line(frame, trajectory[i-1], trajectory[i], (0,0,255), thickness)

    # ----- OVERLAY LABEL -----
    color_map = {
        "NORMAL": (0,255,0),
        "DROP": (0,0,255),
        "MERGE": (0,165,255)
    }

    cv2.putText(
        frame,
        f"{label} ({confidence:.2f})",
        (30, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        color_map[label],
        3
    )

    cv2.putText(
        frame,
        f"Frame: {frame_id}",
        (30, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2
    )

    out.write(frame)

    prev_center = center
    prev_frame = frame.copy()
    frame_id += 1

cap.release()
out.release()

print("Processing complete.")