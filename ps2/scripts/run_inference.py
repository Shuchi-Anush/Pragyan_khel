# file: ps2/scripts/run_inference.py
import os
import argparse
import csv
import cv2
from ultralytics import YOLO

def run(video_path, model_path, out_dir="ps2/results", conf_thresh=0.25, imgsz=960, target_class=None):
    os.makedirs(out_dir, exist_ok=True)
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video: " + video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    base = os.path.splitext(os.path.basename(video_path))[0]
    csv_path = os.path.join(out_dir, f"{base}_detections.csv")
    out_video = os.path.join(out_dir, f"{base}_inference.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (w, h))

    # map class name -> index if requested
    cls_idx = None
    if target_class is not None:
        for k, v in model.names.items():
            if v == target_class:
                cls_idx = int(k)
                break
        print("Filtering for class:", target_class, "->", cls_idx)

    with open(csv_path, "w", newline="") as cf:
        wcsv = csv.writer(cf)
        wcsv.writerow(["frame", "detected", "x1", "y1", "x2", "y2", "conf", "cx", "cy"])

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=conf_thresh, imgsz=imgsz, verbose=False)
            res = results[0]
            best_box = None
            best_conf = 0.0

            for box in res.boxes:
                bconf = float(box.conf[0])
                bcls = int(box.cls[0])
                if cls_idx is not None and bcls != cls_idx:
                    continue
                if bconf > best_conf:
                    best_conf = bconf
                    best_box = box

            if best_box is None:
                wcsv.writerow([frame_idx, 0, -1, -1, -1, -1, 0.0, -1, -1])
            else:
                x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                cx, cy = ((x1 + x2)//2, (y1 + y2)//2)
                wcsv.writerow([frame_idx, 1, x1, y1, x2, y2, round(best_conf, 4), cx, cy])
                # draw on frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.circle(frame, (cx, cy), 4, (0,0,255), -1)
                lab = model.names.get(int(best_box.cls[0]), "obj")
                cv2.putText(frame, f"{lab} {best_conf:.2f}", (x1, max(10, y1-6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            cv2.putText(frame, f"Frame: {frame_idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            writer.write(frame)
            frame_idx += 1

    cap.release()
    writer.release()
    print("Saved:", csv_path, out_video)
    return csv_path, out_video

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="input video path")
    p.add_argument("--model", required=True, help="path to model (best.pt)")
    p.add_argument("--out", default="ps2/results", help="output directory")
    p.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    p.add_argument("--imgsz", type=int, default=960, help="inference image size")
    p.add_argument("--class-name", default=None, help="optional class name to restrict detections (e.g. cricket_ball)")
    args = p.parse_args()
    run(args.video, args.model, out_dir=args.out, conf_thresh=args.conf, imgsz=args.imgsz, target_class=args.class_name)