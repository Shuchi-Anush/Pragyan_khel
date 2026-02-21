# ps2/scripts/run_pipeline.py
import os
import csv
import cv2
import numpy as np

from ps2.core.blur import laplacian_variance
from ps2.core.flow import optical_flow_magnitude
from ps2.core.ssim import compute_ssim
from ps2.core.fusion import classify_frame


def run_pipeline(video_path, out_dir="../results"):

    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    n = len(frames)
    if n < 3:
        raise RuntimeError("Video too short")

    flows = [0.0] * n
    ssims = [1.0] * n
    blurs = [0.0] * n

    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)

    for i in range(1, n):
        gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

        flows[i] = optical_flow_magnitude(prev_gray, gray)
        blurs[i] = laplacian_variance(frames[i])
        ssims[i] = compute_ssim(frames[i - 1], frames[i])

        prev_gray = gray

    labels = []
    confidences = []

    for i in range(n):
        label, conf = classify_frame(i, flows, ssims, blurs)
        labels.append(label)
        confidences.append(conf)

    # -------- SAVE CSV REPORT --------

    csv_path = os.path.join(out_dir, "report.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "flow", "ssim_prev", "blur", "label", "confidence"])

        for i in range(n):
            writer.writerow([
                i,
                flows[i],
                ssims[i],
                blurs[i],
                labels[i],
                round(confidences[i], 3)
            ])

    # -------- CREATE ANNOTATED VIDEO --------

    out_video = os.path.join(out_dir, "annotated.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (width, height))

    color_map = {
        "NORMAL": (0, 255, 0),
        "DROP": (0, 0, 255),
        "MERGE": (0, 165, 255)
    }

    for i, frame in enumerate(frames):
        label = labels[i]
        conf = confidences[i]

        color = color_map.get(label, (255, 255, 255))
        text = f"{label} ({conf:.2f})"

        cv2.putText(
            frame,
            text,
            (40, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            color,
            3,
            cv2.LINE_AA
        )

        writer.write(frame)

    writer.release()

    print("Processing complete.")
    print("Saved:", csv_path)
    print("Saved:", out_video)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <video_path>")
        sys.exit(1)

    video = sys.argv[1]
    run_pipeline(video)