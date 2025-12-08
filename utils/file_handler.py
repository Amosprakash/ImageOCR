# utils/file_handler.py
"""
Multi-format file handling and text extraction for ImageAI.
Supports images, videos, PDFs, DOCX, Excel, CSV, and TXT files.

IMPORTANT: This code is moved from utils.py WITHOUT ANY CHANGES to the extraction logic.
Only imports have been updated to use new module paths.
"""
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from docx import Document
from google.cloud import vision
import pandas as pd
import io
from rake_nltk import Rake
import nltk
import os
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
import cv2
import numpy as np
import asyncio
import hashlib
from core.ocr_engine import run_paddle_ocr
from core.tesseract_fallback import run_tesseract_on_low_conf
from utils.logger import log
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configure Tesseract and Poppler from environment variables ---
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")  # Default to system PATH
POPPLER_PATH = os.getenv("POPPLER_PATH", None)  # Optional for PDF processing
ocr_cache = {}

# Only set tesseract_cmd if a specific path is provided
if TESSERACT_PATH != "tesseract":
    if not os.path.exists(TESSERACT_PATH):
        log.warning(f"Tesseract not found at {TESSERACT_PATH}, falling back to system PATH")
        pytesseract.pytesseract.tesseract_cmd = "tesseract"
    else:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# --- Download NLTK resources ---
nltk.download('stopwords', quiet=True)
nltk.download("punkt", quiet=True)

# --- Keyword Extraction ---
def extract_keywords(text: str, top_n: int = 100) -> str:
    """
    Extract top keywords from text using RAKE algorithm.

    Args:
        text: Input text to extract keywords from
        top_n: Number of top keywords to return

    Returns:
        Space-separated string of keywords
    """
    stop_words = stopwords.words("english")
    rake = Rake(stopwords=stop_words)
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()[:top_n]
    return " ".join(keywords)

# --- Image Enhancement and Correction ---
def enhance_and_correct_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if w > h:
        gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)

    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoising(resized, h=30)

    # Sharpening
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    # Histogram equalization
    equalized = cv2.equalizeHist(sharpened)

    # Adaptive thresholding
    binarized = cv2.adaptiveThreshold(equalized, 255,
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY,
                                      blockSize=11, C=2)
    return binarized

def get_image_hash(content: bytes) -> str:
    """
    Generate a unique hash for the image content.

    Args:
        content: Raw image bytes

    Returns:
        MD5 hash string
    """
    return hashlib.md5(content).hexdigest()


# --- Async OCR Pipeline ---
async def extract_text(file):
    """
    Extract text from various file formats (images, videos, PDFs, DOCX, Excel, CSV, TXT).

    Args:
        file: UploadFile object with filename and content

    Returns:
        dict: {"success": bool, "message": str, "text": str} for images
        str: Extracted text for other file types
    """
    ext = file.filename.split(".")[-1].lower()
    content = await file.read()
    text = ""

    image_exts = ["png", "jpg", "jpeg", "tiff", "bmp", "gif", "webp"]
    video_exts = ["mp4", "avi", "mov", "mkv"]

    try:
        # ----- IMAGE OCR -----
        if ext in image_exts:
    # Use raw bytes directly (no open)
            img_bytes = content  

            # Compute hash on bytes
            image_hash = get_image_hash(img_bytes)

            # If cached, return directly
            if image_hash in ocr_cache:
                log.info(f"OCR cache hit for image hash {image_hash}")
                return  {"success": True, "message": "Text extracted successfully", "text": ocr_cache[image_hash]}
           

            # 2️⃣ Paddle OCR
            
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(image)
            result = run_paddle_ocr(img_np,debug=True)
            if not result["success"]:
                return {"success": False, "message": result["message"], "text": ""}

            paddle_lines = result["lines"]

            # 3️⃣ Tesseract (low-confidence refinement)
            result1 = run_tesseract_on_low_conf(paddle_lines)
            if not result1["success"]:
                return {"success": False, "message": result1["message"], "text": ""}
            tesseract_text = result1["lines"]

            # 4️⃣ Combine + deduplicate
            parts = [tesseract_text]
            seen = set()
            final_lines = []
            for part in parts:
                for line in part.splitlines():
                    clean_line = line.strip()
                    if clean_line and clean_line not in seen:
                        final_lines.append(clean_line)
                        seen.add(clean_line)

            final_text = "\n".join(final_lines)

            # 5️⃣ Cache result
            ocr_cache[image_hash] = final_text

            return {"success": True, "message": "Text extracted successfully", "text": final_text}


        # ----- VIDEO OCR -----
        elif ext in video_exts:
            temp_video_path = f"temp_video.{ext}"
            with open(temp_video_path, "wb") as f:
                f.write(content)

            cap = cv2.VideoCapture(temp_video_path)
            frame_texts = []
            FRAME_INTERVAL_SEC = 1
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            current_time = 0

            while cap.isOpened() and current_time < duration:
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                if not ret:
                    break

                enhanced_frame = enhance_and_correct_image(frame)
                frame_text = pytesseract.image_to_string(enhanced_frame, lang="eng")
                if frame_text.strip():
                    frame_texts.append(frame_text)
                current_time += FRAME_INTERVAL_SEC

            cap.release()
            os.remove(temp_video_path)
            text = "\n\n".join(frame_texts)

        # ----- PDF -----
        elif ext == "pdf":
            pdf_reader = PdfReader(io.BytesIO(content))
            text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages]).strip()

            if not text:
                BATCH_SIZE = 5
                total_pages = len(pdf_reader.pages)
                ocr_texts = []
                for i in range(0, total_pages, BATCH_SIZE):
                    images = convert_from_bytes(content, poppler_path=POPPLER_PATH,
                                                first_page=i+1,
                                                last_page=min(i + BATCH_SIZE, total_pages))
                    for img in images:
                        img_np = np.array(img.convert("RGB"))
                        processed = enhance_and_correct_image(img_np)
                        page_text = pytesseract.image_to_string(processed, lang='eng')
                        if page_text.strip():
                            ocr_texts.append(page_text)

                text = "\n".join(ocr_texts)

        # ----- DOCX -----
        elif ext == "docx":
            doc = Document(io.BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs])

        # ----- EXCEL -----
        elif ext in ["xlsx", "xls"]:
            text = excel_to_text_in_chunks(content, chunk_size=1000)

        # ----- TXT / CSV -----
        elif ext in ["txt", "csv"]:
            text = content.decode("utf-8")

        else:
            log.warning(f"Unsupported file type: {ext} for {file.filename}")

    except Exception as e:
        log.error(f"Extraction error for {file.filename}: {str(e)}")
        text = ""

    if not text.strip():
        log.warning(f"Warning: No text extracted from {file.filename}")
    return text

# --- Sync wrapper ---
def extract_text_sync(content: bytes, filename: str) -> str:
    class DummyFile:
        def __init__(self, content, filename):
            self._content = content
            self.filename = filename
        async def read(self):
            return self._content

    dummy_file = DummyFile(content, filename)
    return asyncio.run(extract_text(dummy_file))

# --- Excel reader ---
def excel_to_text_in_chunks(content: bytes, chunk_size: int = 1000) -> str:
    df = pd.read_excel(io.BytesIO(content))
    all_chunks_text = []
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start+chunk_size]
        chunk_text = chunk.to_csv(index=False)
        all_chunks_text.append(chunk_text)
    return "\n\n".join(all_chunks_text)
