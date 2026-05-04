# UF Marking Defect Detection System

## Description
An image-based defect detection system for uniformity marking inspection.  
The system detects marking regions from camera images, evaluates marking quality, and saves inspection results automatically.

## Core Features
- Detects marking regions using a YOLO-based object detector
- Crops and resizes detected marking areas for standardized inspection
- Classifies markings as OK / NG based on pixel-level color difference analysis
- Saves cropped images, contour visualization, bounding boxes, and result logs
- Supports real-time UI integration through PyQt signal communication

## My Contribution
- Implemented the core inspection logic in `worker.py`
- Integrated YOLO object detection with rule-based defect judgment
- Designed pixel-ratio based OK / NG classification algorithm
- Added result saving pipeline for OK, NG, contour, cropped image, and bounding box outputs
- Connected processing results to the UI using PyQt signals

## Pipeline
Camera Image  
→ YOLO Marking Detection  
→ Bounding Box Crop  
→ Resize to Fixed Size  
→ Pixel-level Marking Area Analysis  
→ OK / NG Classification  
→ Save Results & Notify UI

## Tech Stack
- Python
- PyTorch
- Ultralytics YOLO
- OpenCV
- NumPy
- PIL
- PyQt5
