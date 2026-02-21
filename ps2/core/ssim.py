# ps2/core/ssim.py
import cv2
from skimage.metrics import structural_similarity as ssim

def compute_ssim(f1, f2):
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)

    h, w = g1.shape

    win = min(7, h, w)
    if win % 2 == 0:
        win -= 1
    win = max(3, win)

    return float(ssim(g1, g2, win_size=win))