# core/tesseract_fallback.py
"""
Tesseract fallback module for ImageAI.
Handles Tesseract OCR for low-confidence PaddleOCR results.

IMPORTANT: This code is moved from image.py WITHOUT ANY CHANGES to the logic.
Only imports and organization have been updated.
"""
import os
import pytesseract
from Levenshtein import ratio as lev_ratio
from dotenv import load_dotenv
from utils.logger import log

# Load environment variables
load_dotenv()

# === Configure Tesseract from environment variable ===
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
if TESSERACT_PATH != "tesseract":
    if not os.path.exists(TESSERACT_PATH):
        log.warning(f"Tesseract not found at {TESSERACT_PATH}, falling back to system PATH")
        pytesseract.pytesseract.tesseract_cmd = "tesseract"
    else:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

CONFIDENCE_THRESHOLD = 0.75


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
            log.info(f"Tesseract replaced/overrode: '{text}' → '{t_text}'")
        else:
            # Keep original if Tesseract result is unreliable
            merged_lines.append(text)
            log.info(f"Kept original PaddleOCR text: '{text}' (conf={conf:.2f})")

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
