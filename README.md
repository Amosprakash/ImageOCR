# 📝 ImageOCR – Multi-format Intelligent OCR Pipeline

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green)](https://fastapi.tiangolo.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.6-orange)](https://github.com/PaddlePaddle/PaddleOCR)

**ImageOCR** is a production-ready Python OCR framework for extracting text from images, videos, PDFs, DOCX, Excel, and CSV/TXT files.  
It combines **FastAPI**, **PaddleOCR**, and **Tesseract** with advanced image preprocessing and caching for high accuracy.

---

## 🚀 Key Features

- 🖼 **Multi-format Support:**  
  Images (`png/jpg/jpeg/tiff/bmp/gif/webp`), Videos (`mp4/avi/mov/mkv`), PDFs, DOCX, Excel (`xls/xlsx`), CSV, TXT

- ✨ **Advanced Image Preprocessing:**  
  Super-resolution, deskewing, blur detection & correction, white background enforcement, adaptive thresholding

- 🔍 **Robust OCR Pipeline:**  
  PaddleOCR → Tesseract for low-confidence refinement

- 🗝 **Keyword Extraction:**  
  RAKE + NLTK integration for automatic keyword generation

- 💾 **Caching System:**  
  Avoid redundant OCR for repeated images

---

## ⚙️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YourUsername/ImageOCR.git
cd ImageOCR
2.Create virtual environment and install dependencies:
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

4.Install Tesseract OCR & Poppler for PDF processing.

5.Download PaddleOCR models (if not included in models/).

🖥 Usage

Start the FastAPI server:

uvicorn app:app --host 0.0.0.0 --port 3000 --reload

API Endpoint
POST /api/upload


Accepts multi-format files: image, pdf, docx, xlsx, csv, txt, video

Returns extracted text with success status and message


Python Example
from utils import extract_text_sync

with open("Input/sample.pdf", "rb") as f:
    content = f.read()

text = extract_text_sync(content, "sample.pdf")
print(text)


📂 Project Structure
ImageOCR/
├─ app.py                # FastAPI application & routes
├─ log.py                # Rotating logger
├─ openai_client.py      # Async OpenAI API wrapper with retries
├─ utils.py              # OCR pipeline & multi-format extraction
├─ image.py              # Image preprocessing & PaddleOCR/Tesseract
├─ models/               # PaddleOCR models
├─ Input/                # Example input files
├─ Output/               # Extracted results
├─ requirements.txt      # Python dependencies
├─ .gitignore
└─ log.txt               # Rotating logs


⚠️ Notes & Recommendations

Use Git LFS for files >100MB

Confirm Tesseract and Poppler paths are correct

Production-ready OCR workflows with advanced preprocessing and ca


📖 References

FastAPI Documentation

PaddleOCR GitHub

Tesseract OCR

RAKE + NLTK



---

✅ **Instructions for you:**

1. Copy the above Markdown into a new file in your project folder:  
```text
README.md


Commit and push it to GitHub:

git add README.md
git commit -m "Add polished README"
git push
