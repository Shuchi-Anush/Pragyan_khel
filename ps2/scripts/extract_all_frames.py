import cv2
import os
from pathlib import Path

video_folder = "ps2/sample_videos"
output_root = "ps2/dataset/raw_frames"

os.makedirs(output_root, exist_ok=True)

video_paths = list(Path(video_folder).glob("*.mp4"))

total_saved = 0

for video_path in video_paths:
    cap = cv2.VideoCapture(str(video_path))
    video_name = video_path.stem

    frame_count = 0
    saved_count = 0

    # Create subfolder per video
    video_output_dir = os.path.join(output_root, video_name)
    os.makedirs(video_output_dir, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save every frame (we filter later)
        filename = os.path.join(
            video_output_dir,
            f"{video_name}_frame_{frame_count:05d}.jpg"
        )
        cv2.imwrite(filename, frame)

        frame_count += 1
        saved_count += 1

    cap.release()

    print(f"{video_name} → {saved_count} frames saved")
    total_saved += saved_count

print("TOTAL FRAMES SAVED:", total_saved)