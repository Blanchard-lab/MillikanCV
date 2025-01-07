import cv2
import os

def extract_video_properties(video):
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    display_width = 640
    display_height = int(display_width * (frame_height / frame_width))

    return total_frames, frame_width, frame_height, display_width, display_height

def save_yolo_format(frame_num, bbox, img_width, img_height, base_output_path):
    x_center = (bbox[0] + bbox[2] / 2) / img_width
    y_center = (bbox[1] + bbox[3] / 2) / img_height
    width = bbox[2] / img_width
    height = bbox[3] / img_height
    output_path = os.path.join(base_output_path, f"{frame_num:06d}.txt")
    with open(output_path, 'w') as file:
        file.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")