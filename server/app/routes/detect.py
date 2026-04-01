import sys
import cv2
import base64
import numpy as np
from pathlib import Path
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

# Add server directory to path for absolute import
server_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(server_dir))

from yolo.detection import detect_image


router = APIRouter(prefix="/detect", tags=["detect"])


@router.post("")
async def detect(file: UploadFile = File(...)):
    """
    Detect objects in uploaded image using YOLO model.

    Returns:
        JSONResponse with annotated image (base64 encoded) and count dictionary
        with label numbers as keys (only includes detected labels)
    """
    try:
        # Check if file is provided
        if not file.filename:
            return JSONResponse(
                status_code=404,
                content={"message": "File not found. Please upload a file."},
            )

        # Read uploaded file content
        contents = await file.read()

        # Convert bytes to numpy array
        nparr = np.frombuffer(contents, np.uint8)

        # Decode image using OpenCV
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                status_code=400,
                content={"message": "Invalid image file. Please upload a valid image."},
            )

        # Process image through YOLO detection
        annotated_image, count_dict, confidence_dict = detect_image(image)

        # Encode annotated image to JPEG format
        _, buffer = cv2.imencode(".jpg", annotated_image)

        # Convert to base64 for JSON response
        image_base64 = base64.b64encode(buffer).decode("utf-8")

    except Exception:
        return JSONResponse(
            status_code=500, content={"message": "Error processing image"}
        )

    return JSONResponse(
        status_code=200,
        content={
            "count": count_dict,
            "confidence": confidence_dict,
            "image_format": ".jpg",
            "annotated_image_base64": image_base64,
        },
    )
