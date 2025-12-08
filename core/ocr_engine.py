# core/ocr_engine.py
"""
PaddleOCR engine module for ImageAI.
Handles PaddleOCR initialization and execution.

IMPORTANT: This code is moved from image.py WITHOUT ANY CHANGES to the OCR logic.
Only imports and organization have been updated.
"""
import cv2
import os
from paddleocr import PaddleOCR
from dotenv import load_dotenv
from core.preprocess import (
    super_resolve, deskew_image, preprocess_image, 
    preprocess_crop, ensure_bgr, validate
)
from utils.logger import log

# Load environment variables
load_dotenv()

# === Initialize PaddleOCR ===
try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="en",
        det_model_dir="models/en_PP-OCRv3_det_infer",
        rec_model_dir="models/en_PP-OCRv4_rec_infer",
        cls_model_dir="models/ch_ppocr_mobile_v2.0_cls_infer"
    )
    log.info("Loaded PP-OCRv4 custom models")
except Exception as e:
    log.warning(f"Custom PP-OCR models not found, using default: {e}")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')

CONFIDENCE_THRESHOLD = 0.75


# === Run PaddleOCR ===
def run_paddle_ocr(img, use_superres=True, use_deskew=True, debug=False):
    """
    Runs PaddleOCR on the given image.
    Returns a dict: {"success": bool, "message": str, "lines": list}
    """
    try:
        # 1️⃣ Validate image
        if use_superres:
            img = super_resolve(img)
        valid, msg = validate(img)
        if not valid:
            return {"success": False, "message": msg, "lines": []}

        # 2️⃣ Preprocess
        img = preprocess_image(img, debug=debug)

        
        if use_deskew:
            img = deskew_image(img)

        img = ensure_bgr(img)

        # 3️⃣ Run OCR
        results = ocr.ocr(img, cls=True)
        if not results or not results[0]:
            log.info("PaddleOCR returned no results")
            return {"success": False, "message": "No text detected", "lines": []}

        # 4️⃣ Process OCR results
        paddle_lines = []
        for line in results[0]:
            box = line[0]
            text, conf = line[1]
            x_min = int(min(pt[0] for pt in box))
            x_max = int(max(pt[0] for pt in box))
            y_min = int(min(pt[1] for pt in box))
            y_max = int(max(pt[1] for pt in box))
            cropped = img[y_min:y_max, x_min:x_max]

            if cropped.size == 0 or cropped.shape[0] < 5 or cropped.shape[1] < 5:
                continue

            processed_crop = preprocess_crop(cropped)
            paddle_lines.append({"text": text.strip(), "conf": conf, "crop": processed_crop})
            log.info(f"PaddleOCR: '{text.strip()}' (conf={conf:.2f})")

        if not paddle_lines:
            return {"success": False, "message": "No valid text found", "lines": []}

        return {"success": True, "message": "Text extracted", "lines": paddle_lines}

    except Exception as e:
        log.warning(f"PaddleOCR failed: {e}")
        return {"success": False, "message": f"OCR failed: {e}", "lines": []}
