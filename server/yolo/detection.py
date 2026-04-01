import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

from .preprocess import preprocess_image

CLASS_NAME_MAPPING = {
    "Pill_01": 1,
    "Pill_02": 2,
}

# Load YOLO model from weights directory
model_path = Path(__file__).parent / "weights" / "best.pt"
model = YOLO(str(model_path))

# Default confidence threshold (0.0 to 1.0)
DEFAULT_CONF_THRESHOLD = 0.6


def detect_image(image_input, conf_threshold=DEFAULT_CONF_THRESHOLD):
    """
    Process static image through YOLO model and annotate detected objects.

    Args:
        image_input: Input image to process
        conf_threshold: Confidence threshold (0.0 to 1.0). Detections with confidence
                       below this value will be filtered out. Default is 0.5.

    Returns:
        tuple: (annotated_image, count_dict, confidence_dict) - Annotated image with
               bounding boxes and label numbers in top-left corner, dictionary of counts
               by label number (only includes detected labels), and dictionary of average
               confidence scores by label number
    """
    # Prepare image: convert to numpy array and preprocess for model
    original_img_array = np.array(image_input)
    model_input_img, (crop_x_offset, crop_y_offset) = preprocess_image(image_input)

    # Run YOLO model inference with confidence threshold
    results = model(model_input_img, conf=conf_threshold)

    # Initialize variables for annotation
    annotated_img = original_img_array.copy()
    detected_objects = []

    # Step A: Extract all detection data
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Map coordinates from cropped image space back to original image space
            x1 += crop_x_offset
            y1 += crop_y_offset
            x2 += crop_x_offset
            y2 += crop_y_offset

            # Get class ID and class name
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            # Get confidence score (already between 0 and 1)
            confidence = float(box.conf[0])

            # Map class name to label number using CLASS_NAME_MAPPING
            label_number = CLASS_NAME_MAPPING.get(class_name, None)

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1

            detected_objects.append(
                {
                    "coords": (x1, y1, x2, y2),
                    "center": (center_x, center_y),
                    "width": width,
                    "height": height,
                    "class_name": class_name,
                    "label_number": label_number,
                    "confidence": confidence,
                }
            )

    # Step B: Sort objects (top to bottom, left to right)
    detected_objects.sort(key=lambda obj: (obj["center"][1], obj["center"][0]))

    # Step C: Calculate global font size based on smallest detected object
    if len(detected_objects) > 0:
        min_width = min(obj["width"] for obj in detected_objects)
        min_height = min(obj["height"] for obj in detected_objects)
        font_scale = max(min_width, min_height) / 80
        thickness = int(font_scale * 2)
    else:
        font_scale = 1.0
        thickness = 2

    # Step D: Draw annotations (green bounding boxes with label numbers in top-left corner)
    # Count objects and track confidence by label number
    count_dict = {}
    confidence_sum_dict = {}

    for item in detected_objects:
        x1, y1, x2, y2 = item["coords"]
        label_number = item["label_number"]
        confidence = item["confidence"]

        # Draw green bounding box around detected object
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Prepare text label (label number from CLASS_NAME_MAPPING)
        if label_number is not None:
            text = f"{label_number:02d}"

            # Count objects by label number
            count_dict[label_number] = count_dict.get(label_number, 0) + 1

            # Accumulate confidence per label number (0–1 range)
            confidence_sum_dict[label_number] = (
                confidence_sum_dict.get(label_number, 0.0) + confidence
            )

            # Calculate text size
            (text_w, text_h), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )

            # Calculate padding around text
            padding_x = int(10 * font_scale)
            padding_y = int(5 * font_scale)

            # Position label in top-left corner of bounding box
            # Background box coordinates (top-left corner)
            box_x1 = x1
            box_y1 = y1
            box_x2 = x1 + text_w + (padding_x * 2)
            box_y2 = y1 + text_h + (padding_y * 2)

            # Draw filled black background box (thickness = -1 means filled)
            cv2.rectangle(
                annotated_img, (box_x1, box_y1), (box_x2, box_y2), (0, 0, 0), -1
            )

            # Draw white text on top of black background
            # Text origin (top-left corner with padding)
            text_origin_x = x1 + padding_x
            text_origin_y = y1 + text_h + padding_y

            cv2.putText(
                annotated_img,
                text,
                (text_origin_x, text_origin_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness,
            )

    # Calculate average confidence per label_number
    confidence_dict = {
        label: (confidence_sum_dict[label] / count_dict[label])
        for label in confidence_sum_dict
        if count_dict.get(label, 0) > 0
    }

    return annotated_img, count_dict, confidence_dict
