import os
import cv2
import supervision as sv
from ultralytics import YOLO

output_video_path = "bird_video.mp4"

print("--- STARTING BIRD MONITORING SYSTEM ---")

if not os.path.exists(output_video_path):
    print(f"ERROR: '{output_video_path}' not found in the folder!")
    exit()
else:
    print(f"SUCCESS: Found '{output_video_path}'")

# Load YOLO model and tracker
print("Loading YOLO model...")
model = YOLO("yolov8n.pt")
tracker = sv.ByteTrack()

box_annotator = sv.BoxAnnotator(thickness=2)
trace_annotator = sv.TraceAnnotator(thickness=2, trace_length=30)
label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)

print(f"Opening video file: {output_video_path}")
cap = cv2.VideoCapture(output_video_path)

if not cap.isOpened():
    print("ERROR: Could not open local video file.")
    exit()
else:
    print("SUCCESS: Video stream opened!")

fps = cap.get(cv2.CAP_PROP_FPS)
delay = int(1000 / fps) if fps > 0 else 30
print(f"Video FPS: {fps}, Playback Delay: {delay}ms")

print("Processing frames... Press 'q' in the video window to exit.")

unique_bird_ids = set()
frame_count = 0

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print(f"End of video file reached after processing {frame_count} frames.")
        break

    frame_count += 1

    # Run tracking
    results = model.track(frame, persist=True, conf=0.25, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Filter strictly for birds (COCO class ID 14)
    if len(detections) > 0:
        detections = detections[detections.class_id == 14]

    # Update tracker with unique IDs
    detections = tracker.update_with_detections(detections)

    if detections.tracker_id is not None:
        for tid in detections.tracker_id:
            unique_bird_ids.add(tid)

    # Create label tags with unique ID numbers for each bird
    labels = [
        f"ID: {tracker_id}" if tracker_id is not None else "Bird"
        for tracker_id in detections.tracker_id
    ]

    # Apply motion trails, boxes, and ID number labels
    annotated_frame = trace_annotator.annotate(scene=frame.copy(), detections=detections)
    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

    # --- PROFESSIONAL ANALYTICS DASHBOARD & TABLE OVERLAY ---
    overlay = annotated_frame.copy()
    cv2.rectangle(overlay, (20, 20), (420, 190), (0, 0, 0), -1)
    alpha = 0.65
    cv2.addWeighted(overlay, alpha, annotated_frame, 1 - alpha, 0, annotated_frame)
    cv2.rectangle(annotated_frame, (20, 20), (420, 190), (0, 255, 0), 2)

    cv2.putText(annotated_frame, "WILDLIFE ANALYTICS PLATFORM", (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(annotated_frame, f"Active Flock Count (Frame): {len(detections)}", (35, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(annotated_frame, f"Total Unique Birds Tracked: {len(unique_bird_ids)}", (35, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    cv2.putText(annotated_frame, "Status: Monitoring Migration Density", (35, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 200), 1)

    # Display window
    cv2.imshow("Bird Population Monitoring System", annotated_frame)

    if cv2.waitKey(delay) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Program finished cleanly.")