# core/preprocess.py
"""
Image preprocessing module for ImageAI.
Contains all preprocessing functions for OCR robustness.
Handles super-resolution, deskewing, blur detection, contrast enhancement, etc.

IMPORTANT: This code is moved from image.py WITHOUT ANY CHANGES to the algorithms.
Only imports and organization have been updated.
"""
import cv2
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        # Import logger here to avoid circular dependency
        from utils.logger import log
        log.info(f"Super-resolution skipped: {e}")
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
        from utils.logger import log
        log.info(f"Deskew failed: {e}")
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
    from utils.logger import log
    log.info(f"Deblurred image (blur score={score:.2f})")
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
    from utils.logger import log
    log.info(f"Image height: {img.shape[0]}px")
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
