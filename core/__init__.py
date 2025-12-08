# core/__init__.py
"""
Core OCR modules for ImageAI Document AI Platform.
"""
from .preprocess import (
    super_resolve, safe_to_gray, deskew_image, detect_blur, conditional_deblur,
    force_white_background, preprocess_for_ocr, preprocess_crop, ensure_bgr,
    preprocess_image, is_low_contrast, is_low_resolution, validate
)
from .ocr_engine import run_paddle_ocr, CONFIDENCE_THRESHOLD
from .tesseract_fallback import run_tesseract_on_low_conf, postprocess_text

__all__ = [
    'super_resolve', 'safe_to_gray', 'deskew_image', 'detect_blur', 'conditional_deblur',
    'force_white_background', 'preprocess_for_ocr', 'preprocess_crop', 'ensure_bgr',
    'preprocess_image', 'is_low_contrast', 'is_low_resolution', 'validate',
    'run_paddle_ocr', 'run_tesseract_on_low_conf', 'postprocess_text', 'CONFIDENCE_THRESHOLD'
]
