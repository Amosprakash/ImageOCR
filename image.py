# image.py
"""
Image preprocessing and OCR module for ImageOCR.
Handles PaddleOCR and Tesseract integration with advanced image preprocessing.
"""
import cv2
import numpy as np
import pytesseract
from paddleocr import PaddleOCR
import log as Log
import re
from Levenshtein import ratio as lev_ratio
import os
from dotenv import load_dotenv

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
    Log.log.info("Loaded PP-OCRv4 custom models")
except Exception as e:
    Log.log.warning(f"Custom PP-OCR models not found, using default: {e}")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')

# === Configure Tesseract from environment variable ===
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
if TESSERACT_PATH != "tesseract":
    if not os.path.exists(TESSERACT_PATH):
        Log.log.warning(f"Tesseract not found at {TESSERACT_PATH}, falling back to system PATH")
        pytesseract.pytesseract.tesseract_cmd = "tesseract"
    else:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

CONFIDENCE_THRESHOLD = 0.75


# === Super-resolution helper (optional) ===
def super_resolve(img, debug=False):
    """
    Apply super-resolution to enhance image quality using FSRCNN model.

    Args:
        img: Input image
        debug: If True, save intermediate results

    Returns:
        Enhanced image
    """
    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel("FSRCNN_x4.pb")
        sr.setModel("fsrcnn", 4)
        img = sr.upsample(img)
        if debug:
            cv2.imwrite("1_superres.png", img)
    except Exception as e:
        Log.log.info(f"Super-resolution skipped: {e}")
    return img

def safe_to_gray(img):
    """
    Safely convert image to grayscale regardless of input format.

    Args:
        img: Input image (BGR, BGRA, or grayscale)

    Returns:
        Grayscale image
    """
    if len(img.shape) == 2:  # already grayscale
        return img
    elif len(img.shape) == 3 and img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    else:
        raise ValueError(f"Unsupported image shape: {img.shape}")

# === Deskew helper ===
def deskew_image(image):
    """
    Automatically deskew (straighten) a tilted image using contour detection.

    Args:
        image: Input image

    Returns:
        Deskewed image
    """
    try:
        gray = safe_to_gray(image)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        angles = []
        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            angle = rect[-1]
            if angle < -45:
                angle += 90
            if -45 < angle < 45:
                angles.append(angle)

        if angles:
            median_angle = np.median(angles)
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            return cv2.warpAffine(image, M, (w, h),
                                  flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REPLICATE)
    except Exception as e:
        Log.log.info(f"Deskew failed: {e}")
    return image


# === Blur detection + conditional deblur ===
def detect_blur(image, threshold=100.0):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold, laplacian_var


def conditional_deblur(img):
    is_blurry, score = detect_blur(img)
    if not is_blurry:
        return img
    gaussian = cv2.GaussianBlur(img, (9, 9), 10.0)
    deblurred = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)
    Log.log.info(f"Deblurred image (blur score={score:.2f})")
    return deblurred


# === Force white background ===
def force_white_background(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    white_bg = np.ones_like(img, dtype=np.uint8) * 255
    white_bg[mask == 0] = img[mask == 0]
    return white_bg


# === Preprocess for OCR ===
def preprocess_for_ocr(img):
    img = force_white_background(img)
    img = conditional_deblur(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return gray


# === Preprocess crops for Tesseract ===
def preprocess_crop(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )


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
            Log.log.info("PaddleOCR returned no results")
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
            Log.log.info(f"PaddleOCR: '{text.strip()}' (conf={conf:.2f})")

        if not paddle_lines:
            return {"success": False, "message": "No valid text found", "lines": []}

        return {"success": True, "message": "Text extracted", "lines": paddle_lines}

    except Exception as e:
        Log.log.warning(f"PaddleOCR failed: {e}")
        return {"success": False, "message": f"OCR failed: {e}", "lines": []}


# === Run Tesseract on low confidence ===
def run_tesseract_on_low_conf(paddle_lines):
    """
    Refines low-confidence PaddleOCR lines using Tesseract.
    Always keeps original text if Tesseract result is unreliable.
    """
    merged_lines = []
    config = r"--oem 3 --psm 6"

    for line in paddle_lines:
        text, conf, crop = line["text"], line["conf"], line["crop"]

        # If confidence is high, keep as is
        if conf >= CONFIDENCE_THRESHOLD:
            merged_lines.append(text)
            continue

        # Otherwise, try Tesseract
        t_text = pytesseract.image_to_string(crop, lang="eng", config=config).strip()

        # Compare similarity
        similarity = lev_ratio(t_text, text) if t_text else 0

        # Decide which text to keep
        if t_text and (similarity >= 0.85 or len(t_text) > len(text) + 3):
            merged_lines.append(t_text)
            Log.log.info(f"Tesseract replaced/overrode: '{text}' → '{t_text}'")
        else:
            # Keep original if Tesseract result is unreliable
            merged_lines.append(text)
            Log.log.info(f"Kept original PaddleOCR text: '{text}' (conf={conf:.2f})")

    # Post-process all lines
    text = "\n".join(postprocess_text(merged_lines))
    return {"success": True, "message": "Text extracted", "lines": text}



# === Postprocessing cleanup ===
def postprocess_text(lines):
    cleaned = []
    for line in lines:
        txt = line
        # Common OCR fixes
        txt = txt.replace("I1em", "Item")
        txt = txt.replace("$ ", "$")
        txt = txt.replace(" - ", "-")
        txt = txt.strip()
        if txt:
            cleaned.append(txt)
    return cleaned

def ensure_bgr(img):
    if len(img.shape) == 2:  # grayscale → BGR
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 1:  # single channel
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 3:  # already BGR
        return img
    elif len(img.shape) == 3 and img.shape[2] == 4:  # has alpha channel
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        raise ValueError(f"Unsupported image format: {img.shape}")


def preprocess_image(img, debug=False):
    """
    Preprocess image for OCR robustness.
    Handles glare, blur, shadows, and uneven lighting.
    """
    # Read image
    img = ensure_bgr(img)
    img = force_white_background(img)
    img = conditional_deblur(img)

    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Denoise (helps with compression artifacts or mobile blur)
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # 3. Remove uneven lighting (morphological background subtraction)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    norm = cv2.divide(gray, background, scale=255)

    # 4. Sharpen (helps recover blurred edges from mobile captures)
    sharpen_kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
    sharp = cv2.filter2D(norm, -1, sharpen_kernel)

    # 5. Adaptive threshold (good for mixed lighting)
    thresh = cv2.adaptiveThreshold(
        sharp, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15
    )

    # 6. Optional – invert if white text on dark background
    white_pixels = np.sum(thresh == 255)
    black_pixels = np.sum(thresh == 0)
    if black_pixels > white_pixels:  # mostly dark
        thresh = cv2.bitwise_not(thresh)
        cv2.imwrite("1_gray.png", gray)
        cv2.imwrite("2_norm.png", norm)
        cv2.imwrite("3_sharp.png", sharp)
        cv2.imwrite("4_thresh.png", thresh)

    if debug:
        cv2.imwrite("1_gray.png", gray)
        cv2.imwrite("2_norm.png", norm)
        cv2.imwrite("3_sharp.png", sharp)
        cv2.imwrite("4_thresh.png", thresh)

    return thresh

def is_low_contrast(image, threshold=15.0):
    """
    Check if image has low contrast.

    Args:
        image: Input image
        threshold: Minimum contrast threshold

    Returns:
        bool: True if low contrast, False otherwise
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    min_value, max_value = gray.min(), gray.max()
    return (max_value - min_value) < threshold


def is_low_resolution(img, min_height=500):
    """
    Check if image resolution is too low.

    Args:
        img: Input image
        min_height: Minimum acceptable height in pixels

    Returns:
        bool: True if resolution is too low, False otherwise
    """
    Log.log.info(f"Image height: {img.shape[0]}px")
    return img.shape[0] < min_height


def validate(img):
    """
    Validate image quality for OCR processing.

    Args:
        img: Input image to validate

    Returns:
        tuple: (is_valid, message) where is_valid is bool and message is str
    """
    blur, fm = detect_blur(img)
    if blur:
        return False, f"The image is blurry (focus measure = {fm:.2f})"
    if is_low_contrast(img):
        return False, "The image has low contrast"
    if is_low_resolution(img):
        return False, "Please upload an image with higher resolution"
    return True, "Image quality is good"


