import cv2
import os

# Initialize the CSRT tracker
tracker = cv2.TrackerCSRT_create()

# Path to your video file
video_path = '/Users/calebchristian/Desktop/2024-07-01 14-29-48_compressed.mov'
base_output_path = '/Users/calebchristian/Desktop/2024-07-02 10-42-43Lbl'  # Base path to save YOLO format annotations

# Read the video file
video = cv2.VideoCapture(video_path)
if not video.isOpened():
    print(f"Error: Could not open video {video_path}")
    exit()

# Get video properties
total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
display_width = 640
display_height = int(display_width * (frame_height / frame_width))

# Read the first frame of the video
ret, frame = video.read()
frame = cv2.resize(frame, (display_width, display_height))
bbox = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
tracker.init(frame, bbox)

paused = False
current_frame = 0
bbox_history = {current_frame: bbox}  # Dictionary to store bounding box history

def save_yolo_format(frame_num, bbox, img_width, img_height):
    x_center = (bbox[0] + bbox[2] / 2) / img_width
    y_center = (bbox[1] + bbox[3] / 2) / img_height
    width = bbox[2] / img_width
    height = bbox[3] / img_height
    output_path = os.path.join(base_output_path, f"{frame_num:06d}.txt")
    with open(output_path, 'w') as file:
        file.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

while True:
    if not paused:
        ret, frame = video.read()
        if not ret or frame is None:
            print("Video playback completed or error occurred")
            break

        frame = cv2.resize(frame, (display_width, display_height))
        current_frame += 1
        ret, bbox = tracker.update(frame)
        if ret:
            bbox_history[current_frame] = bbox
            save_yolo_format(current_frame, bbox, display_width, display_height)
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
        else:
            cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

        # Display the current frame number in the top left-hand corner
        cv2.putText(frame, f"Frame: {current_frame}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow('Frame', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
    elif key == ord('p'):
        paused = not paused
    elif key == ord('b') and paused:
        # Move backward one frame
        if current_frame > 0:
            current_frame -= 1
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = video.read()
            frame = cv2.resize(frame, (display_width, display_height))
            bbox = bbox_history.get(current_frame, None)  # Retrieve the bounding box from history
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)  # Draw the bounding box
            cv2.putText(frame, f"Frame: {current_frame}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)  # Display frame number
            cv2.imshow('Frame', frame)
    elif key == ord('r') and paused:
        # Allow redrawing the bounding box
        bbox = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
        tracker = cv2.TrackerCSRT_create()
        tracker.init(frame, bbox)
        bbox_history[current_frame] = bbox
        save_yolo_format(current_frame, bbox, display_width, display_height)
        paused = False  # Resume tracking
    elif key == ord('f') and paused:
        # Move forward one frame
        if current_frame < total_frames - 1:
            current_frame += 1
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = video.read()
            frame = cv2.resize(frame, (display_width, display_height))
            bbox = bbox_history.get(current_frame, None)  # Retrieve the bounding box from history, if available
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)  # Draw the bounding box
            cv2.putText(frame, f"Frame: {current_frame}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)  # Display frame number
            cv2.imshow('Frame', frame)

# Release the video capture object
video.release()
cv2.destroyAllWindows()




