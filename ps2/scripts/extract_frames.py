import cv2
import os

video_path = "ps2/sample_videos/test-18.mp4"
output_dir = "ps2/dataset/raw_frames"

os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)

frame_count = 0
saved_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Save every 3rd frame to avoid duplicates
    if frame_count % 1 == 0:
        filename = os.path.join(output_dir, f"frame_{saved_count:05d}.jpg")
        cv2.imwrite(filename, frame)
        saved_count += 1

    frame_count += 1

cap.release()

print("Total frames saved:", saved_count)