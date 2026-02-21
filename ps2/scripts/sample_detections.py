# ps2/scripts/sample_detections.py (very small)
import csv, random, shutil, os
def sample(dets, frames_root, out="ps2/samples", k=20):
    os.makedirs(out, exist_ok=True)
    rows = [r for r in csv.DictReader(open(dets))]
    pos = [r for r in rows if float(r.get("conf",0))>0.2]
    sel = random.sample(pos, min(k, len(pos)))
    for r in sel:
        frame_idx = int(r["frame"])
        # copy logic same as autocurate
        # ...