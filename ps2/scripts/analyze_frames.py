import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def laplacian_variance(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def compute_ssim(f1, f2):
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    return ssim(g1, g2)

def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Detected FPS: {fps}")

    frames = []
    flows = []
    blurs = []
    ssims = []

    ret, prev_frame = cap.read()
    if not ret:
        print("Error reading video")
        return

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    frames.append(prev_frame)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray,
            None, 0.5, 3, 15, 3, 5, 1.2, 0
        )

        mag = np.mean(np.sqrt(flow[..., 0]**2 + flow[..., 1]**2))
        flows.append(mag)

        blur_score = laplacian_variance(frame)
        blurs.append(blur_score)

        similarity = compute_ssim(prev_frame, frame)
        ssims.append(similarity)

        frames.append(frame)
        prev_gray = gray
        prev_frame = frame

    cap.release()

    flow_arr = np.array(flows)
    mean_flow = np.mean(flow_arr)
    std_flow = np.std(flow_arr)

    print("\n--- Classification ---")

    for i in range(len(flows)):
        z_score = (flows[i] - mean_flow) / (std_flow + 1e-6)

        label = "NORMAL"
        confidence = 0.0

        # Drop detection
        if z_score > 3:
            label = "DROP"
            confidence = min(1.0, z_score / 5)

        # Merge detection
        elif flows[i] < 0.1 and ssims[i] > 0.98:
            label = "MERGE"
            confidence = 0.9

        print(f"Frame {i}: {label} (Conf={confidence:.2f})")

if __name__ == "__main__":
    video_path = input("Enter video path: ")
    analyze_video(video_path)