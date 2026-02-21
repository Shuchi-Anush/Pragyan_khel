# Pragyan_khel
Ctrl+Shift | Pragyan NextGen Hackathon 2026 | PS2- Frame Drop / Merge Detection  

# Ball-Centric Frame Drop Detection System

**Ctrl+Shift** &nbsp;|&nbsp; Pragyan NextGen Hackathon 2026 &nbsp;|&nbsp; PS2 — Frame Drop / Merge Detection

---

## Problem Statement

In professional cricket broadcasts, video streams are occasionally corrupted by **frame drops** — moments where one or more frames go missing from the recorded footage. At first glance, this seems like a purely technical problem. But in sport, especially under DRS scrutiny, a dropped frame near a delivery or catch can change the entire interpretation of an event.

The naive fix — checking timestamps — doesn't actually work in practice. Timestamps in broadcast pipelines are often interpolated or re-stamped at encoding stages, meaning a missing frame can go undetected if the timestamp gap looks "close enough." You can't trust timestamps alone.

What you *can* trust is the ball.

A cricket ball in flight follows predictable physics. It moves in arcs. Its velocity changes gradually unless something happens — a pitch, an edge, a catch. If the ball's position suddenly jumps in ways that defy those physics, something was dropped. That's the insight this system is built on.

---

## Our Approach

### 1. Ball Detection with YOLOv8

We use a fine-tuned YOLOv8 model to detect the cricket ball in each frame. Raw detections alone are noisy — backgrounds in cricket broadcasts are complex, with ad boards, fielders, and spectator movement all capable of triggering false positives.

### 2. ROI-Constrained Tracking

Rather than running the detector over the entire frame on every pass, we define a **Region of Interest (ROI)** centered around the ball's last known position. Detection only considers candidates within this constrained window. This dramatically cuts false positives from background clutter and makes the pipeline faster.

### 3. Velocity-Based Motion Prediction

Between frames, we track the ball's velocity — both direction and speed. Given a valid trajectory, we can predict where the ball *should* appear in the next frame. If the detected position falls within a reasonable distance of that prediction, we accept it. If it doesn't, we flag it for investigation.

### 4. Drop Detection Logic

A frame drop manifests as a discontinuity in the ball's trajectory — a positional jump that doesn't match the predicted velocity. We compute this deviation across consecutive frames and apply an adaptive threshold. Frames where the ball's displacement exceeds what physics allows are marked as drop candidates.

This is fundamentally more reliable than fixed-threshold or timestamp-based approaches because it's grounded in the ball's actual motion, not metadata that may have been altered downstream.

---

## System Architecture

```
Cricket Match Video
        │
        ▼
  YOLOv8 Detection
  (per-frame ball localization)
        │
        ▼
  ROI-Constrained Filtering
  (discard detections outside expected region)
        │
        ▼
  Velocity Prediction
  (estimate next expected position from motion history)
        │
        ▼
  Trajectory Discontinuity Analysis
  (compare actual vs predicted position)
        │
        ▼
  Frame Drop Classification
  (flag frames where displacement exceeds adaptive threshold)
        │
        ▼
  Annotated Output Video + Report
```

---

## Key Features

- **Ball-Specific Analysis** — Detection and analysis focused exclusively on the cricket ball, not the entire scene.
- **Motion-Constrained Detection** — ROI-based windowing keeps detection anchored to physically plausible positions.
- **False Positive Reduction** — Combining spatial constraints with velocity filtering filters out background noise that would otherwise be misclassified.
- **Adaptive Thresholding** — Drop detection thresholds adjust based on observed trajectory smoothness rather than a fixed cutoff.
- **GPU Acceleration** — YOLOv8 inference runs on GPU when available, with CPU fallback for portability.

---

## Demo Output

The system produces an annotated video alongside structured JSON/CSV reports.

In the annotated video:
- A **green trajectory line** traces the ball's detected path across recent frames, giving a live view of its flight arc.
- **Red markers** highlight frames where a drop was detected — the exact frames where the trajectory breaks.
- Where drops are detected, you can visually see the ball's position "jump" in a way that wouldn't happen in clean footage.

The reports include per-frame detection confidence, positional data, velocity, and drop/merge flags — structured for downstream integration into analytics pipelines.

---

## Challenges Faced

**False positives from the background**
Cricket broadcast backgrounds are infamously cluttered. Advertising hoardings, players, and crowd movement all generate candidate detections. ROI filtering mitigated this, but tuning the initial detection window required significant iteration.

**Motion blur**
At high shutter speeds or high delivery velocities, the ball becomes an elongated blur rather than a clean sphere. YOLOv8 handles this better than classical detectors, but it still produces lower-confidence detections that need filtering.

**Occlusion**
When the ball passes behind a fielder or the umpire, detection gaps are unavoidable. The velocity predictor maintains trajectory continuity through short occlusions, but multi-frame occlusions required fallback logic.

**Detection instability near the pitch**
Ball bounce causes rapid directional change in a few frames. This is physically legitimate but looks like a discontinuity to a naive detector. Separating legitimate bounces from actual frame drops was one of the more nuanced calibration challenges.

---

## Real-World Applications

- **DRS Systems** — Validate video integrity before ball-tracking data is used in review decisions.
- **Sports Analytics Pipelines** — Ensure frame-accurate data before feeding into shot classification or wagon wheel generation.
- **Broadcast Quality Validation** — Automated pre-broadcast checks to catch encoding issues before air.
- **Automated Video Integrity Checking** — Flag corrupted segments in archived match footage for re-acquisition or annotation correction.

---

## Future Improvements

- **Kalman Filter Integration** — Replace the current velocity predictor with a Kalman filter for more robust state estimation under noisy conditions.
- **Optical Flow-Based Merge Detection** — Use dense optical flow alongside YOLO to better detect merged frames where two moments are blended into one.
- **Real-Time Deployment** — Optimize the pipeline for live broadcast monitoring with sub-frame latency targets.
- **Multi-Camera Fusion** — Correlate detections across multiple broadcast angles to resolve occlusion gaps and improve drop localization accuracy.

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

The key dependencies are:

```
ultralytics
opencv-python
numpy
```

A GPU with CUDA support is optional but recommended for real-time performance.

### Running the Detection Pipeline

```bash
python ps2/release/backend/main.py --input <path_to_video> --output <output_path>
```

Or run the testing script directly:

```bash
cd ps2/testing
python final_v1.py
```

### Output

Results are written to `ps2/release/backend/outputs/` as:
- An annotated `.mp4` video with trajectory overlay and drop markers
- A `.json` report with per-frame detection and drop metadata
- A `.csv` summary for spreadsheet analysis

---

## Team

**Ctrl+Shift** — Pragyan NextGen Hackathon 2026

---