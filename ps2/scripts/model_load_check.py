# file: ps2/scripts/model_load_check.py
from ultralytics import YOLO
import argparse
import torch
import os
import sys

def main(model_path: str):
    if not os.path.exists(model_path):
        print(f"ERROR: model not found: {model_path}", file=sys.stderr)
        return 2
    model = YOLO(model_path)
    print("Model loaded:", model_path)
    print("Device:", "cuda" if torch.cuda.is_available() else "cpu")
    # model.names is a dict mapping id->name
    print("Class names:", model.names)
    try:
        imgsz = model.model.yaml.get("imgsz") if hasattr(model, "model") else None
        print("Model cfg imgsz (if available):", imgsz)
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="path to model (e.g. ps2/models/best.pt)")
    args = p.parse_args()
    raise SystemExit(main(args.model))