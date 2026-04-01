import numpy as np
import cv2


def preprocess_image(image_input):
    """
    Preprocess image to match training pipeline:
    2. Apply histogram equalization
    3. Convert back to 3-channel format for YOLO model compatibility
    Returns:
        tuple: (preprocessed_bgr_image, (crop_x_offset, crop_y_offset))
    """
    # Convert to numpy array (handles PIL Image inputs)
    img_array = np.array(image_input)

    # Crop image to region that contains the main object
    gray_for_crop = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray_for_crop, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x_min, y_min = img_array.shape[1], img_array.shape[0]
    x_max, y_max = 0, 0

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > 300:  # filter small noise blobs
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w)
            y_max = max(y_max, y + h)

    crop_x_offset = 0
    crop_y_offset = 0
    if x_max > x_min and y_max > y_min:
        crop_x_offset = x_min
        crop_y_offset = y_min
        img_array = img_array[y_min:y_max, x_min:x_max]

    # Convert to grayscale
    img_gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    # Apply histogram equalization to enhance contrast
    equ_img = cv2.equalizeHist(img_gray)
    # Convert back to 3 channels (BGR format)
    final_img = cv2.cvtColor(equ_img, cv2.COLOR_GRAY2BGR)

    return final_img, (crop_x_offset, crop_y_offset)
