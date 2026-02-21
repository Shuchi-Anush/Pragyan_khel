# file: ps2/scripts/autocurate_from_dets.py
import os
import csv
import shutil
from pathlib import Path
import argparse

def find_frame_file(frames_root: Path, video_base: str, frame_idx: int):
    # common patterns: frame_00001.jpg, frame-00001.jpg, img_00001.jpg, or contain 00001
    candidates = []
    fmt = f"{frame_idx:05d}"
    patterns = [
        f"**/frame_{fmt}.*",
        f"**/frame-{fmt}.*",
        f"**/img_{fmt}.*",
        f"**/*{fmt}.*",
        f"**/{video_base}_frame_{fmt}.*",
        f"**/{video_base}*{fmt}.*",
    ]
    for p in patterns:
        candidates.extend(list(frames_root.glob(p)))
    # prefer jpg/png
    for c in candidates:
        if c.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            return c
    return candidates[0] if candidates else None

def curate(dets_csv, frames_root, out_dir="ps2/dataset/curated", conf_thr=0.2):
    frames_root = Path(frames_root)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    with open(dets_csv, "r") as f:
        r = csv.DictReader(f)
        video_base = Path(dets_csv).stem.replace("_detections", "")
        for row in r:
            try:
                conf = float(row.get("conf") or 0.0)
            except:
                conf = 0.0
            if conf < conf_thr:
                continue
            frame_idx = int(row["frame"])
            src = find_frame_file(frames_root, video_base, frame_idx)
            if src and src.exists():
                dst = out_dir / f"{video_base}_f{frame_idx:05d}{src.suffix}"
                # avoid overwriting same file
                if not dst.exists():
                    shutil.copy(src, dst)
                    copied += 1
    print(f"Copied {copied} images to {out_dir}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dets", required=True, help="detections csv")
    p.add_argument("--frames", required=True, help="root folder where extracted frames are (searches recursively)")
    p.add_argument("--out", default="ps2/dataset/curated", help="destination for curated images")
    p.add_argument("--conf", type=float, default=0.2, help="min confidence to copy frame")
    args = p.parse_args()
    curate(args.dets, args.frames, out_dir=args.out, conf_thr=args.conf)