"""
Video Processing Script based on Annotations

This script reads a JSON annotation file, trims the corresponding video segments, applies spatial cropping if necessary, and adapts to any changes in frame rate or resolution between the annotation and the source video.
Finally, it outputs the processed clips and an updated JSON annotation file.

Requirements:
    - Python 3.x
    - OpenCV (pip install opencv-python)

Usage:
    python process_dataset_opencv.py --annotation <path_to_json> --source_dir <source_video_directory> --output_dir <output_directory> [--output_json <output_json_name>]

Arguments:
    --annotation  : (Required) Path to the original JSON annotation file.
    --source_dir  : (Required) Directory containing the original source videos (named '{source_video}.mp4').
    --output_dir  : (Required) Directory where the generated video clips and the new JSON will be saved.
    --output_json : (Optional) Name of the updated JSON file. Defaults to 'labels_updated.json'.

Example:
    python process_dataset_opencv.py --annotation data.json --source_dir ./source_videos --output_dir ./output_clips
"""

import json
import os
import cv2
import copy
import argparse

def process_videos_opencv(annotation_file, source_dir, output_dir, output_json_name):
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)

    new_annotations = []

    os.makedirs(output_dir, exist_ok=True)

    for idx, item in enumerate(annotations):
        filename = item['filename']
        source_video_name = item['source_video'] + ".mp4"
        source_path = os.path.join(source_dir, source_video_name)

        print(f"[{idx+1}/{len(annotations)}] Processing: {filename} ...")

        if not os.path.exists(source_path):
            print(f"  [Warning] Source video not found: {source_path}. Skipping.")
            continue

        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            print(f"  [Error] Cannot open video: {source_path}")
            continue

        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if actual_fps <= 0:
            print(f"  [Error] Invalid FPS read: {actual_fps}. Skipping this file.")
            cap.release()
            continue

        orig_fps = item['fps']
        orig_w = item['original_resolution']['w']
        orig_h = item['original_resolution']['h']

        fps_ratio = actual_fps / orig_fps if orig_fps > 0 else 1.0

        start_frame = int(item['absolute_start_frame'] * fps_ratio)
        end_frame = int(item['absolute_end_frame'] * fps_ratio)

        new_item = copy.deepcopy(item)

        if abs(fps_ratio - 1.0) > 1e-3:
            new_item['absolute_start_frame'] = start_frame
            new_item['absolute_end_frame'] = end_frame
            new_item['timestamp1_frame_relative'] = int(item['timestamp1_frame_relative'] * fps_ratio)
            new_item['timestamp2_frame_relative'] = int(item['timestamp2_frame_relative'] * fps_ratio)
            new_item['fps'] = actual_fps

        w_ratio = actual_w / orig_w if orig_w > 0 else 1.0
        h_ratio = actual_h / orig_h if orig_h > 0 else 1.0

        is_cropped = item.get('is_cropped', False)
        if is_cropped:
            crop_box = item['crop_box']
            x1 = max(0, int(crop_box['x'] * w_ratio))
            y1 = max(0, int(crop_box['y'] * h_ratio))
            x2 = min(actual_w, x1 + int(crop_box['w'] * w_ratio))
            y2 = min(actual_h, y1 + int(crop_box['h'] * h_ratio))
            
            out_w = x2 - x1
            out_h = y2 - y1
        else:
            x1, y1, x2, y2 = 0, 0, actual_w, actual_h
            out_w, out_h = actual_w, actual_h

        target_folder = os.path.join(output_dir, item['source_video'])
        os.makedirs(target_folder, exist_ok=True)
        out_path = os.path.join(target_folder, filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(out_path, fourcc, actual_fps, (out_w, out_h))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current_frame = start_frame

        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            if is_cropped:
                frame = frame[y1:y2, x1:x2]

            writer.write(frame)
            current_frame += 1

        cap.release()
        writer.release()
        
        new_annotations.append(new_item)

    output_json_path = os.path.join(output_dir, output_json_name)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(new_annotations, f, indent=4, ensure_ascii=False)
    
    print(f"\nProcessing complete.")
    print(f"The updated annotation file is saved at: {output_json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process videos based on annotations.")

    parser.add_argument("--annotation", required=True, help="Path to the input JSON annotation file.")
    parser.add_argument("--source_dir", required=True, help="Directory containing the source videos.")
    parser.add_argument("--output_dir", required=True, help="Directory to save the processed video clips.")
    parser.add_argument("--output_json", default="labels_updated.json", help="Name of the output JSON file. Defaults to 'labels_updated.json'.")

    args = parser.parse_args()

    process_videos_opencv(
        annotation_file=args.annotation, 
        source_dir=args.source_dir, 
        output_dir=args.output_dir, 
        output_json_name=args.output_json
    )
