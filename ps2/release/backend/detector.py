"""
Ball detection engine — Kalman-filtered, ROI-constrained, motion-gated.

Provides `process_video(video_path, model_path)` that returns:
    {
        "annotated_video": "<filename>.mp4",
        "report": { ... summary ... },
        "report_file": "<filename>_report.json",
    }
"""

import cv2
import math
import os
import json
import numpy as np
from ultralytics import YOLO
from skimage.metrics import structural_similarity as ssim

# ─── DEFAULT TUNING KNOBS ─────────────────────────────────────────────
DEFAULT_CFG = {
    "YOLO_CONF":            0.15,
    "BALL_AREA_MIN":        20,
    "BALL_AREA_MAX":        3000,
    "GATE_THRESHOLD_PX":    80,
    "BALL_RADIUS_EST":      15,
    "MERGE_SSIM_THRESHOLD": 0.75,
    "MERGE_BLUR_RATIO":     0.7,
    "LOW_CONF_MERGE":       0.4,
    "ROI_SEARCH_PX":        200,
    "ROI_MIN_ACCEPTED":     3,
    "DROP_GAP_MIN":         2,
}

# ─── MODEL CACHE (load once, reuse across requests) ──────────────────
_model_cache = {}

def _get_model(model_path: str) -> YOLO:
    if model_path not in _model_cache:
        _model_cache[model_path] = YOLO(model_path)
    return _model_cache[model_path]


def _scan_boxes(results, off_x, off_y, pred_x, pred_y, has_prediction, cfg):
    """Return (best_candidate, min_error) — candidate closest to predicted pos."""
    best_candidate = None
    min_error = float("inf")
    for result in results:
        for box in result.boxes:
            lx1, ly1, lx2, ly2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            x1 = lx1 + off_x;  x2 = lx2 + off_x
            y1 = ly1 + off_y;  y2 = ly2 + off_y
            area = (x2 - x1) * (y2 - y1)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            if area < cfg["BALL_AREA_MIN"] or area > cfg["BALL_AREA_MAX"]:
                continue
            error = (math.sqrt((cx - pred_x)**2 + (cy - pred_y)**2)
                     if has_prediction else 0.0)
            if error < min_error:
                min_error = error
                best_candidate = (x1, y1, x2, y2, cx, cy, area, conf)
    return best_candidate, min_error


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def process_video(video_path: str, model_path: str = "best.pt", cfg: dict = None, output_dir: str = None):
    """
    Full ball tracking pipeline.

    Parameters
    ----------
    video_path : str   – path to input video
    model_path : str   – path to YOLO .pt weights
    cfg        : dict  – override any key from DEFAULT_CFG

    Returns
    -------
    dict with keys  annotated_video, report, report_file
    """
    c = {**DEFAULT_CFG, **(cfg or {})}

    # resolve model path relative to this file
    if not os.path.isabs(model_path):
        here = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(here, model_path)
        if os.path.exists(candidate):
            model_path = candidate

    model = _get_model(model_path)

    # ── open video ────────────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS)
    frame_w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if output_dir is None:
        output_dir = os.path.dirname(video_path)
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    basename   = os.path.splitext(os.path.basename(video_path))[0]
    annotated_path = os.path.join(output_dir, f"{basename}_annotated.mp4")
    report_path    = os.path.join(output_dir, f"{basename}_report.json")

    print(f"[detector] {video_path}  |  {total_frames} frames @ {fps:.1f} FPS  |  {frame_w}x{frame_h}")

    # ══════════════════════════════════════════════════════════════════
    # PASS 1 — Kalman + ROI-constrained detection
    # ══════════════════════════════════════════════════════════════════
    ball_history  = []
    drop_frames   = set()
    drop_evidence = {}
    frame_id      = 0

    def _mark_drop(frames_iter, label):
        for f in frames_iter:
            drop_frames.add(f)
            drop_evidence.setdefault(f, []).append(label)

    kf = cv2.KalmanFilter(4, 2)
    kf.measurementMatrix   = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
    kf.transitionMatrix    = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
    kf.processNoiseCov     = np.eye(4, dtype=np.float32) * 1e-2
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 5e-1
    kf.errorCovPost        = np.eye(4, dtype=np.float32)
    kf_initialized  = False
    kf_accepted_cnt = 0

    r = c["BALL_RADIUS_EST"]

    print("[detector] Pass 1 — Kalman + ROI-constrained detection ...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        use_roi = kf_initialized and kf_accepted_cnt >= c["ROI_MIN_ACCEPTED"]

        if use_roi:
            kf_pred    = kf.predict()
            pred_x     = int(kf_pred[0, 0])
            pred_y     = int(kf_pred[1, 0])
            has_prediction = True
            rx1 = max(0, pred_x - c["ROI_SEARCH_PX"])
            ry1 = max(0, pred_y - c["ROI_SEARCH_PX"])
            rx2 = min(frame_w, pred_x + c["ROI_SEARCH_PX"])
            ry2 = min(frame_h, pred_y + c["ROI_SEARCH_PX"])
            search_frame = frame[ry1:ry2, rx1:rx2]
            offset_x, offset_y = rx1, ry1
        elif kf_initialized:
            kf_pred    = kf.predict()
            pred_x     = int(kf_pred[0, 0])
            pred_y     = int(kf_pred[1, 0])
            has_prediction = True
            search_frame = frame
            offset_x, offset_y = 0, 0
        else:
            if len(ball_history) >= 2:
                p1 = ball_history[-2]["center"]
                p2 = ball_history[-1]["center"]
                pred_x = p2[0] + (p2[0] - p1[0])
                pred_y = p2[1] + (p2[1] - p1[1])
                has_prediction = True
            elif len(ball_history) == 1:
                pred_x, pred_y = ball_history[-1]["center"]
                has_prediction = False
            else:
                pred_x, pred_y = frame_w // 2, frame_h // 2
                has_prediction = False
            search_frame = frame
            offset_x, offset_y = 0, 0

        results = model.predict(search_frame, conf=c["YOLO_CONF"], verbose=False)

        best_candidate, min_error = _scan_boxes(
            results, offset_x, offset_y, pred_x, pred_y, has_prediction, c)

        if best_candidate is None and use_roi:
            fallback_results = model.predict(frame, conf=c["YOLO_CONF"], verbose=False)
            best_candidate, min_error = _scan_boxes(
                fallback_results, 0, 0, pred_x, pred_y, has_prediction, c)

        if best_candidate is not None:
            x1, y1, x2, y2, cx, cy, area, conf = best_candidate

            if has_prediction and min_error > c["GATE_THRESHOLD_PX"]:
                cx, cy = int(pred_x), int(pred_y)
                x1, y1, x2, y2 = cx - r, cy - r, cx + r, cy + r
                area = (2 * r) ** 2
                conf = 0.0
                _mark_drop([frame_id], f"GATE({min_error:.0f}px)")
                ball_history.append({
                    "frame": frame_id, "center": (cx, cy),
                    "bbox": (x1, y1, x2, y2), "area": area, "conf": conf,
                    "predicted": True, "roi_gray": None, "blur": 0.0,
                })
            else:
                meas = np.array([[np.float32(cx)], [np.float32(cy)]])
                if not kf_initialized:
                    kf.statePre  = np.array([[cx],[cy],[0],[0]], np.float32)
                    kf.statePost = np.array([[cx],[cy],[0],[0]], np.float32)
                    kf_initialized = True
                else:
                    kf.correct(meas)
                kf_accepted_cnt += 1

                ball_roi = frame[y1:y2, x1:x2]
                if ball_roi.size > 0:
                    gray_ball = cv2.cvtColor(ball_roi, cv2.COLOR_BGR2GRAY)
                    blur_val  = cv2.Laplacian(gray_ball, cv2.CV_64F).var()
                else:
                    gray_ball = None
                    blur_val  = 0.0
                ball_history.append({
                    "frame": frame_id, "center": (cx, cy),
                    "bbox": (x1, y1, x2, y2), "area": area, "conf": conf,
                    "predicted": False, "roi_gray": gray_ball, "blur": blur_val,
                })

        elif has_prediction:
            cx, cy = int(pred_x), int(pred_y)
            x1, y1, x2, y2 = cx - r, cy - r, cx + r, cy + r
            _mark_drop([frame_id], "NO_DET")
            ball_history.append({
                "frame": frame_id, "center": (cx, cy),
                "bbox": (x1, y1, x2, y2), "area": (2*r)**2, "conf": 0.0,
                "predicted": True, "roi_gray": None, "blur": 0.0,
            })

        frame_id += 1
        if frame_id % 200 == 0:
            print(f"[detector] Pass 1: {frame_id}/{total_frames} frames")

    print(f"[detector] Pass 1 done — {len(ball_history)} tracked in {frame_id} frames")

    # ══════════════════════════════════════════════════════════════════
    # POST-PASS — gap + merge detection
    # ══════════════════════════════════════════════════════════════════
    for i in range(1, len(ball_history)):
        gap = ball_history[i]["frame"] - ball_history[i - 1]["frame"]
        if gap >= c["DROP_GAP_MIN"]:
            missing = range(ball_history[i - 1]["frame"] + 1,
                            ball_history[i]["frame"])
            _mark_drop(missing, f"GAP({gap}f)")

    merge_frames = set()
    for i in range(1, len(ball_history) - 1):
        curr = ball_history[i]
        prev_b = ball_history[i - 1]
        nxt  = ball_history[i + 1]
        if curr["predicted"]:
            continue
        roi_curr = curr["roi_gray"]
        roi_prev = prev_b["roi_gray"]
        roi_next = nxt["roi_gray"]
        if roi_curr is not None and roi_prev is not None and roi_next is not None:
            h, w = roi_curr.shape[:2]
            if h >= 7 and w >= 7:
                roi_prev_r = cv2.resize(roi_prev, (w, h))
                roi_next_r = cv2.resize(roi_next, (w, h))
                ssim_prev  = ssim(roi_prev_r, roi_curr)
                ssim_next  = ssim(roi_curr, roi_next_r)
                if (ssim_prev > c["MERGE_SSIM_THRESHOLD"]
                        and ssim_next > c["MERGE_SSIM_THRESHOLD"]
                        and curr["blur"] < min(prev_b["blur"], nxt["blur"]) * c["MERGE_BLUR_RATIO"]):
                    merge_frames.add(curr["frame"])
        if curr["conf"] < c["LOW_CONF_MERGE"]:
            merge_frames.add(curr["frame"])

    print(f"[detector] Drops: {len(drop_frames)}  Merges: {len(merge_frames)}")

    # ══════════════════════════════════════════════════════════════════
    # PASS 2 — Render annotated video
    # ══════════════════════════════════════════════════════════════════
    frame_to_ball = {b["frame"]: b for b in ball_history}

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    # Prefer H.264 (avc1) for browser-compatible playback; fall back to mp4v
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out   = cv2.VideoWriter(annotated_path, fourcc, fps, (frame_w, frame_h))
    if not out.isOpened():
        print("[detector] avc1 encoder unavailable, falling back to mp4v")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out    = cv2.VideoWriter(annotated_path, fourcc, fps, (frame_w, frame_h))

    fid = 0
    print("[detector] Pass 2 — Rendering annotated video ...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        pts = [b["center"] for b in ball_history if b["frame"] <= fid]
        for j in range(1, len(pts)):
            cv2.line(frame, pts[j - 1], pts[j], (0, 255, 0), 2)

        for df in drop_frames:
            if df <= fid and df in frame_to_ball:
                dcx, dcy = frame_to_ball[df]["center"]
                cv2.circle(frame, (dcx, dcy), 7, (0, 0, 255), -1)
                cv2.putText(frame, "DROP", (dcx - 22, dcy - 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        for mf in merge_frames:
            if mf <= fid and mf in frame_to_ball:
                mcx, mcy = frame_to_ball[mf]["center"]
                cv2.circle(frame, (mcx, mcy), 7, (255, 191, 0), -1)
                cv2.putText(frame, "MERGE", (mcx - 28, mcy - 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 191, 0), 2)

        if fid in frame_to_ball:
            b = frame_to_ball[fid]
            bx1, by1, bx2, by2 = b["bbox"]
            is_drop     = fid in drop_frames
            is_predicted = b.get("predicted", False)
            if is_drop:
                bbox_color = (0, 0, 255)
            elif is_predicted:
                bbox_color = (0, 165, 255)
            else:
                bbox_color = (0, 255, 0)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), bbox_color, 2)
            lbl = "PRED" if is_predicted else f"{b['conf']:.2f}"
            cv2.putText(frame, lbl, (bx1, by1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, bbox_color, 1)

        cv2.putText(frame, f"Frame {fid}/{total_frames}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Drops: {len(drop_frames)}  Merges: {len(merge_frames)}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 80, 255), 2)

        out.write(frame)
        fid += 1

    cap.release()
    out.release()

    # ══════════════════════════════════════════════════════════════════
    # Build JSON report
    # ══════════════════════════════════════════════════════════════════
    frame_reports = []
    for b in ball_history:
        fid = b["frame"]
        if fid in drop_frames:
            label = "DROP"
        elif fid in merge_frames:
            label = "MERGE"
        else:
            label = "NORMAL"
        frame_reports.append({
            "frame":     fid,
            "label":     label,
            "center":    list(b["center"]),
            "conf":      round(b["conf"], 4),
            "predicted": b["predicted"],
            "reasons":   drop_evidence.get(fid, []),
        })

    # Build a compact drop-evidence map (frame -> unique reasons)
    drop_reasons_map = {str(f): list(set(vs)) for f, vs in drop_evidence.items()}

    summary = {
        "total_frames":      frame_id,
        "tracked_positions": len(ball_history),
        "drop_frames":       len(drop_frames),
        "merge_frames":      len(merge_frames),
        "drop_frame_list":   sorted(drop_frames),
        "merge_frame_list":  sorted(merge_frames),
        "drop_reasons":      drop_reasons_map,
    }

    full_report = {
        "source":     os.path.basename(video_path),
        "fps":        fps,
        "resolution": f"{frame_w}x{frame_h}",
        "summary":    summary,
        "frames":     frame_reports,
    }

    with open(report_path, "w") as f:
        json.dump(full_report, f, indent=2)

    csv_path = os.path.join(output_dir, f"{basename}_report.csv")
    with open(csv_path, "w") as f:
        f.write("Frame,Label,Center_X,Center_Y,Confidence,Predicted\n")
        for fr in frame_reports:
            f.write(f"{fr['frame']},{fr['label']},{fr['center'][0]},{fr['center'][1]},{fr['conf']},{fr['predicted']}\n")

    print(f"[detector] Output:  {annotated_path}")
    print(f"[detector] Report:  {report_path}")
    print(f"[detector] CSV:     {csv_path}")

    return {
        "annotated_video": os.path.basename(annotated_path),
        "report":          summary,
        "report_file":     os.path.basename(report_path),
        "csv_file":        os.path.basename(csv_path),
    }

