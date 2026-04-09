"""
This script reads a JSON annotation file, trims the corresponding video segments, applies spatial cropping if necessary, and adapts to any changes in frame rate or resolution between the annotation and the actual source video.
Finally, it outputs the processed clips and an updated JSON annotation file.

Requirements:
    - Python 3.x
    - OpenCV
    - FFmpeg (must be installed and added to the system's PATH)

Usage:
    python generate_clips.py --annotation <path_to_json> --source_dir <source_video_directory> --output_dir <output_directory> [--output_json <output_json_name>]

Arguments:
    --annotation  : (Required) Path to the original JSON annotation file.
    --source_dir  : (Required) Directory containing the original source videos (named '{source_video}.mp4').
    --output_dir  : (Required) Directory where the generated video clips and the new JSON will be saved.
    --output_json : (Optional) Name of the updated JSON file. Defaults to 'labels_updated.json'.

Example:
    python generate_clips.py --annotation labels_main.json --source_dir ./source_videos --output_dir ./output_clips
"""

import json
import os
import cv2
import copy
import subprocess
import argparse

def process_videos_with_audio(annotation_file, source_dir, output_dir, output_json_name):
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
        cap.release()

        if actual_fps <= 0:
            print(f"  [Error] Invalid FPS read: {actual_fps}. Skipping this file.")
            continue


        orig_fps = item['fps']
        orig_w = item['original_resolution']['w']
        orig_h = item['original_resolution']['h']

        fps_ratio = actual_fps / orig_fps if orig_fps > 0 else 1.0

        start_frame = int(item['absolute_start_frame'] * fps_ratio)
        end_frame = int(item['absolute_end_frame'] * fps_ratio)

        start_sec = start_frame / actual_fps
        duration_sec = (end_frame - start_frame + 1) / actual_fps

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
        crop_filter = ""
        if is_cropped:
            crop_box = item['crop_box']
            x = max(0, int(crop_box['x'] * w_ratio))
            y = max(0, int(crop_box['y'] * h_ratio))
            w = min(actual_w - x, int(crop_box['w'] * w_ratio))
            h = min(actual_h - y, int(crop_box['h'] * h_ratio))
            crop_filter = f"crop={w}:{h}:{x}:{y}"

        target_folder = os.path.join(output_dir, item['source_video'])
        os.makedirs(target_folder, exist_ok=True)
        out_path = os.path.join(target_folder, filename)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start_sec:.4f}",
            "-i", source_path,
            "-t", f"{duration_sec:.4f}"
        ]

        if is_cropped:
            cmd.extend(["-vf", crop_filter])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            out_path
        ])

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"  [FFmpeg Error] {result.stderr}")
            else:
                new_annotations.append(new_item)
        except FileNotFoundError:
            print("  [Fatal Error] 'ffmpeg' command not found. Please ensure FFmpeg is installed and added to your system PATH.")
            return

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

    process_videos_with_audio(
        annotation_file=args.annotation, 
        source_dir=args.source_dir, 
        output_dir=args.output_dir, 
        output_json_name=args.output_json
    )
    