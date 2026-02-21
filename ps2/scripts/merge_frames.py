import os
import shutil

source_root = "ps2/dataset/raw_frames"
target_dir = "ps2/dataset/final_frames"

os.makedirs(target_dir, exist_ok=True)

counter = 0

for root, dirs, files in os.walk(source_root):
    for file in files:
        if file.endswith(".jpg"):
            src = os.path.join(root, file)
            dst = os.path.join(target_dir, f"img_{counter:05d}.jpg")
            shutil.copy(src, dst)
            counter += 1

print("Total merged:", counter)