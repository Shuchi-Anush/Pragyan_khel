import cv2
cap = cv2.VideoCapture("ps2/sample_videos/test-1.mp4")
print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))