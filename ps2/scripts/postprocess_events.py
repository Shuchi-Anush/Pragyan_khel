# file: ps2/scripts/postprocess_events.py
import os
import argparse
import csv
import math
from collections import deque
import cv2

def load_dets(csv_path):
    rows = []
    with open(csv_path, "r") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def postprocess(video_path, det_csv, out_dir="ps2/results", drop_frames_threshold=6, merge_motion_thresh=2.5):
    os.makedirs(out_dir, exist_ok=True)
    dets = load_dets(det_csv)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    base = os.path.splitext(os.path.basename(video_path))[0]
    out_video = os.path.join(out_dir, f"{base}_events.mp4")
    out_csv = os.path.join(out_dir, f"{base}_events.csv")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (w, h))

    # parse detections into list structures
    detected = []
    centers = []
    confs = []
    for row in dets:
        d = int(row.get("detected", "0"))
        detected.append(bool(d))
        try:
            cx = int(float(row.get("cx", -1)))
            cy = int(float(row.get("cy", -1)))
            if cx < 0 or cy < 0:
                cx, cy = None, None
        except:
            cx, cy = None, None
        centers.append((cx, cy))
        try:
            confs.append(float(row.get("conf", 0.0)))
        except:
            confs.append(0.0)

    n = max(len(detected), 0)
    labels = ["NORMAL"] * n

    # DROP detection using sliding window of misses
    window = drop_frames_threshold
    dq = deque(maxlen=window)
    for i in range(n):
        dq.append(detected[i])
        if len(dq) == window and sum(dq) == 0:
            # mark current frame as DROP
            labels[i] = "DROP"

    # MERGE detection: very small center displacement while detected
    for i in range(1, n):
        c0 = centers[i - 1]
        c1 = centers[i]
        if c0 is not None and c1 is not None and detected[i]:
            dist = math.hypot(c1[0] - c0[0], c1[1] - c0[1])
            if dist < merge_motion_thresh:
                labels[i] = "MERGE"

    # write annotated video + events csv
    with open(out_csv, "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["frame", "detected", "cx", "cy", "conf", "label"])
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        i = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            det = detected[i] if i < len(detected) else False
            cx, cy = centers[i] if i < len(centers) else (None, None)
            conf = confs[i] if i < len(confs) else 0.0
            label = labels[i] if i < len(labels) else "NORMAL"

            # draw center and label
            if cx is not None and cy is not None:
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            color = (0, 200, 0) if label == "NORMAL" else ((0, 0, 255) if label == "DROP" else (0, 200, 200))
            cv2.putText(frame, f"{label} ({conf:.2f})", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)

            writer.write(frame)
            wcsv.writerow([i, int(det), cx or -1, cy or -1, round(conf, 3), label])
            i += 1

    cap.release()
    writer.release()
    print("Saved:", out_csv, out_video)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--detections", required=True, help="detections csv produced by run_inference")
    p.add_argument("--video", required=True, help="raw video to annotate")
    p.add_argument("--out", default="ps2/results", help="output directory")
    p.add_argument("--drop_window", type=int, default=6, help="consecutive miss window -> DROP")
    p.add_argument("--merge_thresh", type=float, default=2.5, help="px threshold for MERGE (small motion)")
    args = p.parse_args()
    postprocess(args.video, args.detections, out_dir=args.out,
                drop_frames_threshold=args.drop_window, merge_motion_thresh=args.merge_thresh)