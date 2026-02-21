# ps2/core/flow.py
import cv2
import numpy as np

def optical_flow_magnitude(prev_gray, gray):
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray,
        gray,
        None,
        0.5,
        3,
        15,
        3,
        5,
        1.2,
        0
    )

    mag = np.mean(np.sqrt(flow[..., 0]**2 + flow[..., 1]**2))
    return float(mag)