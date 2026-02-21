from ultralytics import YOLO
import cv2

# -----------------------------
# Load pretrained YOLOv8 model
# -----------------------------
model = YOLO("ps2/models/yolov8m.pt")

video_path = "ps2/sample_videos/test-1.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Create resizable window once
cv2.namedWindow("YOLO Test", cv2.WINDOW_NORMAL)
cv2.resizeWindow("YOLO Test", 1280, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference
    results = model(frame, verbose=False)

    # Process detections
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            # COCO class name for ball
            if label == "sports ball":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Draw label
                cv2.putText(
                    frame,
                    f"{label} {conf:.2f}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    # Resize for safe display
    display_frame = cv2.resize(frame, (1280, 720))

    cv2.imshow("YOLO Test", display_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()