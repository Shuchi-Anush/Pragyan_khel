# file: ps2/scripts/single_frame_test.py
import os
import argparse
from ultralytics import YOLO
import cv2

def main(image_path, model_path, out_dir="ps2/results", conf=0.25, imgsz=960, target_class=None):
    os.makedirs(out_dir, exist_ok=True)
    model = YOLO(model_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError("Failed to read image: " + image_path)

    results = model(img, conf=conf, imgsz=imgsz, verbose=False)
    res = results[0]  # single image result
    annotated = img.copy()

    best_box = None
    best_conf = 0.0

    # if user gives a class name, find its index
    cls_idx = None
    if target_class is not None:
        for k, v in model.names.items():
            if v == target_class:
                cls_idx = int(k)
                break

    for box in res.boxes:
        bconf = float(box.conf[0])
        bcls = int(box.cls[0])
        if cls_idx is not None and bcls != cls_idx:
            continue
        if bconf > best_conf:
            best_conf = bconf
            best_box = box

    if best_box is not None:
        x1, y1, x2, y2 = map(int, best_box.xyxy[0])
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, f"{model.names[int(best_box.cls[0])]} {best_conf:.2f}",
                    (x1, max(10, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cx, cy = (x1+x2)//2, (y1+y2)//2
        cv2.circle(annotated, (cx, cy), 4, (0,0,255), -1)

    out_path = os.path.join(out_dir, os.path.splitext(os.path.basename(image_path))[0] + "_ann.jpg")
    cv2.imwrite(out_path, annotated)
    print("Saved annotated image to:", out_path)
    print("Detections (best):", best_conf, "class:", model.names.get(int(best_box.cls[0])) if best_box is not None else None)
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out", default="ps2/results")
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--imgsz", type=int, default=960)
    p.add_argument("--class-name", default=None, help="optional class name to restrict detections (e.g. 'cricket_ball')")
    args = p.parse_args()
    raise SystemExit(main(args.image, args.model, out_dir=args.out, conf=args.conf, imgsz=args.imgsz, target_class=args.class_name))