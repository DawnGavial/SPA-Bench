# SPA-Bench: A Novel Video Benchmark for Proactive Physical Hazard Prediction in MLLMs

## Video Acquisition
We do not directly provide the original video files. Researchers can download the original videos using the video IDs provided in the annotation files, rename them to `yt_{Video ID}.mp4`, and then use the annotation files along with our provided script `scripts/generate_clips.py` to extract all video clips. Specific usage instructions are provided within the script code.

## Supplementary Materials
Please refer to `SupplementaryMaterial.pdf`.

## Video Annotations
The `labels` folder contains two video annotation files: `labels_main.json` includes annotations for 2,440 accident videos, and `labels_safe.json` includes annotations for 448 safe videos.

The annotation for each sample is formatted as follows:
```json
    {
        "source_video": "yt_-8DwVUirUqE",               // "yt_" + Original video ID
        "filename": "yt_-8DwVUirUqE_1.mp4",             // Clip's filename
        "sport": {
            "type1": "Standardized Sports Venues",      // Environmental Setting
            "type2": "Cycling"                          // Sports Category
        },
        "hazard": {
            "level1": [
                "Personal Factors"                      // Macro Inducing Factors
            ],
            "level2": "Bicycle losing control after hitting a bump and crashing into a guardrail" // Direct Cause Description
        },
        "is_valid": true,
        "absolute_start_frame": 0,
        "absolute_end_frame": 212, // Annotation used for video cropping
        "is_cropped": true,
        "crop_box": {
            "x": 1,
            "y": 9,
            "w": 702,
            "h": 1254
        },
        "original_resolution": {
            "w": 720,
            "h": 1280
        },                         // Annotation used for video cropping
        "fps": 30.0,
        "timestamp1_frame_relative": 149, // Earliest Cue Moment
        "timestamp2_frame_relative": 167  // Most Obvious Moment
    }
