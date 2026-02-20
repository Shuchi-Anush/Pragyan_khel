# ps2/scripts/annotate_and_report.py
import cv2
import numpy as np
import csv
import os
from skimage.metrics import structural_similarity as ssim

# ---------- utilities ----------
def laplacian_variance(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def compute_ssim(f1, f2):
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    return ssim(g1, g2)

def sliding_stats(arr, idx, window=20):
    start = max(0, idx - window//2)
    end = min(len(arr), idx + window//2)
    w = np.array(arr[start:end]) if end>start else np.array(arr)
    if len(w)==0:
        return float(np.mean(arr)), float(np.std(arr))+1e-6
    return float(np.mean(w)), float(np.std(w))+1e-6

# ---------- core analysis ----------
def analyze_and_annotate(video_path, out_dir="..\\results", window=40):
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # read all frames first (memory OK for short clips); otherwise stream with buffers
    frames = []
    ret = True
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()
    n = len(frames)
    if n < 3:
        raise RuntimeError("Too few frames")

    # compute signals
    flows = [0.0] * n
    blurs = [0.0] * n
    ssims = [1.0] * n

    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for i in range(1, n):
        gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5,3,15,3,5,1.2,0)
        mag = float(np.mean(np.sqrt(flow[...,0]**2 + flow[...,1]**2)))
        flows[i] = mag
        blurs[i] = float(laplacian_variance(frames[i]))
        ssims[i] = float(compute_ssim(frames[i-1], frames[i]))
        prev_gray = gray

    # classification using sliding window stats + heuristics
    labels = ["NORMAL"] * n
    confidences = [0.0] * n

    for i in range(1, n-1):
        mean_flow, std_flow = sliding_stats(flows, i, window=window)
        z = (flows[i] - mean_flow) / (std_flow if std_flow>1e-6 else 1e-6)

        # scene cut detection (avoid false positives)
        if ssims[i] < 0.2 and flows[i] > mean_flow + 2*std_flow:
            labels[i] = "CUT"
            confidences[i] = min(1.0, (flows[i] - mean_flow) / (4*std_flow + 1e-6))
            continue

        # drop detection (big z-score)
        if z > max(2.5, 2 * std_flow):
            labels[i] = "DROP"
            confidences[i] = float(min(1.0, (z / 6.0)))
            continue

        # merge detection (low flow, very high similarity to both sides, and blur increase)
        s_prev = ssims[i]
        s_next = compute_ssim(frames[i], frames[i+1]) if i+1<n else s_prev
        blur_ratio = blurs[i] / max(blurs[i-1], blurs[i+1], 1e-6)
        if flows[i] < max(0.08, mean_flow*0.3) and s_prev > 0.98 and s_next > 0.98 and blur_ratio > 1.1:
            labels[i] = "MERGE"
            confidences[i] = 0.9
            continue

        # otherwise normal (score 0)
        labels[i] = "NORMAL"
        confidences[i] = 0.0

    # write CSV report
    csv_path = os.path.join(out_dir, "report.csv")
    with open(csv_path, "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["frame", "flow", "ssim_prev", "blur", "label", "confidence"])
        for i in range(n):
            s_prev = ssims[i]
            wcsv.writerow([i, flows[i], s_prev, blurs[i], labels[i], round(confidences[i], 3)])

    # make annotated video
    out_video = os.path.join(out_dir, "annotated.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (w, h))

    for i, frame in enumerate(frames):
        label = labels[i]
        conf = confidences[i]
        if label == "NORMAL":
            color = (0, 200, 0)
        elif label == "DROP":
            color = (0, 0, 255)
        elif label == "MERGE":
            color = (0, 200, 200)
        elif label == "CUT":
            color = (128, 128, 128)
        else:
            color = (255,255,255)
        text = f"{label} ({conf:.2f})"
        cv2.putText(frame, text, (30,60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3, cv2.LINE_AA)
        # optionally draw flow magnitude small plot or meter
        writer.write(frame)
    writer.release()

    print("Saved:", csv_path, out_video)
    return csv_path, out_video

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python annotate_and_report.py <input_video_path> [out_dir]")
        sys.exit(1)
    video = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results")
    analyze_and_annotate(video, out_dir=outdir)