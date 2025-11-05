# 📝 ImageOCR – Multi-format Intelligent OCR Pipeline

[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green)](https://fastapi.tiangolo.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.6+-orange)](https://github.com/PaddlePaddle/PaddleOCR)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**ImageOCR** is a production-ready Python OCR framework for extracting text from images, videos, PDFs, DOCX, Excel, and CSV/TXT files. It combines **FastAPI**, **PaddleOCR**, and **Tesseract** with advanced image preprocessing, intelligent caching, and GPT-powered structured text extraction.

---

## 🚀 Key Features

- 🖼 **Multi-format Support**
  Images (`png/jpg/jpeg/tiff/bmp/gif/webp`), Videos (`mp4/avi/mov/mkv`), PDFs, DOCX, Excel (`xls/xlsx`), CSV, TXT

- ✨ **Advanced Image Preprocessing**
  - Super-resolution (FSRCNN 4x upscaling)
  - Automatic deskewing and rotation correction
  - Blur detection & conditional deblurring
  - White background enforcement
  - Adaptive thresholding for mixed lighting
  - Glare and shadow removal

- 🔍 **Robust Dual-Engine OCR Pipeline**
  - **Primary**: PaddleOCR with PP-OCRv3/v4 models
  - **Refinement**: Tesseract for low-confidence text with Levenshtein similarity matching
  - Automatic fallback and confidence-based refinement

- 🤖 **AI-Powered Structured Extraction**
  - OpenAI GPT integration for intelligent question answering
  - Automatic keyword extraction (RAKE + NLTK)
  - Checkbox and form interpretation
  - Hallucination prevention with strict OCR-only extraction

- 💾 **Performance Optimizations**
  - MD5-based image caching to avoid redundant OCR
  - Batch PDF processing with configurable page sizes
  - Async/await for concurrent file processing

- 📊 **Production-Ready Features**
  - Rotating file logger with UTF-8 support
  - Image quality validation (blur, contrast, resolution checks)
  - Comprehensive error handling and logging
  - CORS configuration for web integration

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Amosprakash/ImageOCR.git
cd ImageOCR
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install system dependencies

#### **Tesseract OCR**

**Windows:**
```bash
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
# Default installation path: C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

#### **Poppler (for PDF processing)**

**Windows:**
```bash
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Extract to: C:\Program Files\poppler-xx.xx.x\Library\bin
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

### 5. Configure environment variables

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Minimal configuration
OPENAI_API_KEY=your_openai_api_key_here
TESSERACT_PATH=tesseract  # or full path on Windows
```

See [Configuration](#-configuration) section for all available options.

### 6. Download PaddleOCR models (optional)

The application will download default models automatically on first run. For custom models, place them in the `models/` directory:

```
models/
├── en_PP-OCRv3_det_infer/
├── en_PP-OCRv4_rec_infer/
└── ch_ppocr_mobile_v2.0_cls_infer/
```

---

## 🖥 Usage

### Start the FastAPI server

```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

Or simply run:

```bash
python app.py
```

The API will be available at: `http://localhost:3000`

Interactive API documentation: `http://localhost:3000/docs`

### API Endpoint

**POST** `/api/upload`

**Parameters:**
- `files`: List of files (multipart/form-data)
- `question`: String - Question to ask about the extracted text

**Supported file types:**
- Images: `png`, `jpg`, `jpeg`, `tiff`, `bmp`, `gif`, `webp`
- Videos: `mp4`, `avi`, `mov`, `mkv`
- Documents: `pdf`, `docx`, `xlsx`, `xls`, `csv`, `txt`

**Response:**
```json
{
  "answer": "Extracted and structured information based on your question"
}
```

### Python API Example

```python
from utils import extract_text_sync

# Extract text from a file
with open("Input/sample.pdf", "rb") as f:
    content = f.read()

result = extract_text_sync(content, "sample.pdf")
print(result)
```

### cURL Example

```bash
curl -X POST "http://localhost:3000/api/upload" \
  -F "files=@document.pdf" \
  -F "files=@image.jpg" \
  -F "question=Extract all names and dates from these documents"
```

### Python Requests Example

```python
import requests

files = [
    ("files", ("document.pdf", open("document.pdf", "rb"), "application/pdf")),
    ("files", ("image.jpg", open("image.jpg", "rb"), "image/jpeg"))
]

data = {
    "question": "What is the total amount in the invoice?"
}

response = requests.post("http://localhost:3000/api/upload", files=files, data=data)
print(response.json())
```

---

## 🔧 Configuration

All configuration is managed through environment variables. Create a `.env` file based on `.env.example`:

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `3000` | Server port |
| `RELOAD` | `True` | Enable auto-reload for development |

### CORS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `*` | Comma-separated list of allowed origins. Use specific domains in production |

**Example for production:**
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### OCR Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TESSERACT_PATH` | `tesseract` | Path to Tesseract executable. Use `tesseract` if in system PATH |
| `POPPLER_PATH` | - | Path to Poppler binaries (optional, for PDF processing) |

**Windows example:**
```bash
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-25.07.0\Library\bin
```

### API Keys

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT integration |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to Google Cloud credentials JSON (if using Google Vision API) |

---

## 📂 Project Structure

```
ImageOCR/
├── app.py                   # FastAPI application & middleware
├── upload.py                # Upload endpoint & OpenAI integration
├── utils.py                 # Multi-format text extraction pipeline
├── image.py                 # Image preprocessing & OCR engines
├── log.py                   # Rotating logger configuration
├── openai_client.py         # Async OpenAI API wrapper with retries
├── ocr.py                   # Standalone OCR testing script
├── sample.py                # Preprocessing demonstration script
├── models/                  # PaddleOCR model files
│   ├── en_PP-OCRv3_det_infer/
│   ├── en_PP-OCRv4_rec_infer/
│   └── ch_ppocr_mobile_v2.0_cls_infer/
├── Input/                   # Sample input files for testing
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
├── FSRCNN_x4.pb            # Super-resolution model
└── README.md               # This file
```

---

## 🔬 How It Works

### OCR Pipeline Flow

```
File Upload → Format Detection → Preprocessing → OCR Processing → Post-processing → GPT Extraction
```

#### 1. **Format Detection**
- Automatically detects file type from extension
- Routes to appropriate extraction handler

#### 2. **Image Preprocessing** (for images and scanned PDFs)
- Force white background
- Blur detection and conditional deblurring
- Automatic deskewing
- Noise reduction (fastNlMeansDenoising)
- Histogram equalization
- Sharpening
- Adaptive thresholding

#### 3. **OCR Processing**
- **Primary**: PaddleOCR with confidence threshold (0.75)
- **Refinement**: Tesseract for low-confidence regions
- **Similarity Matching**: Levenshtein distance to choose best result
- **Caching**: MD5-based image hashing to skip duplicate processing

#### 4. **Post-processing**
- Deduplication of extracted lines
- Common OCR error corrections (e.g., "I1em" → "Item")
- Text cleaning and formatting

#### 5. **AI-Powered Extraction**
- Keyword extraction using RAKE + NLTK
- OpenAI GPT structured question answering
- Checkbox interpretation (e.g., "xYes" → "You are eligible")
- Strict hallucination prevention

---

## 🎯 Advanced Features

### Image Quality Validation

Before processing, images are validated for:
- **Blur detection**: Laplacian variance method
- **Contrast check**: Min/max pixel value difference
- **Resolution check**: Minimum height requirement (500px default)

Invalid images are rejected with descriptive error messages.

### Caching System

Images are cached using MD5 hashing:
```python
image_hash = get_image_hash(image_bytes)
if image_hash in ocr_cache:
    return ocr_cache[image_hash]  # Skip OCR
```

### Video Processing

- Extracts frames at 1-second intervals (configurable)
- Applies preprocessing to each frame
- Aggregates text from all frames

### PDF Processing

- **Text-based PDFs**: Direct text extraction with PyPDF2
- **Image-based PDFs**: Batch conversion to images with pdf2image
- **Hybrid PDFs**: Combines both methods

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `Tesseract not found`
```bash
# Verify Tesseract installation
tesseract --version

# If not in PATH, set full path in .env:
TESSERACT_PATH=/usr/local/bin/tesseract  # Linux/Mac
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows
```

**Issue**: `PDF processing fails`
```bash
# Install Poppler and set path in .env:
POPPLER_PATH=/usr/bin  # Linux
POPPLER_PATH=C:\Program Files\poppler\bin  # Windows
```

**Issue**: `OpenAI API errors`
```bash
# Verify API key is set correctly in .env
OPENAI_API_KEY=sk-...

# Check API key has sufficient credits
# Check model name is correct (gpt-4o-mini, gpt-4, etc.)
```

**Issue**: `CORS errors in browser`
```bash
# Add your frontend domain to ALLOWED_ORIGINS in .env:
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Debug Mode

Enable debug mode to save intermediate preprocessing images:

```python
result = run_paddle_ocr(img, debug=True)
```

This will save:
- `1_gray.png` - Grayscale conversion
- `2_norm.png` - Lighting normalization
- `3_sharp.png` - Sharpening result
- `4_thresh.png` - Thresholding result

---

## 📊 Performance Tips

1. **Use environment variables** for configuration instead of hardcoding paths
2. **Enable caching** for repeated image processing (enabled by default)
3. **Batch PDF processing** - Adjust `BATCH_SIZE` in utils.py:170 for your system
4. **Reduce video frame sampling** - Increase `FRAME_INTERVAL_SEC` in utils.py:135
5. **Pre-resize large images** before upload to reduce processing time

---

## 🧪 Testing

### Run Manual Tests

```bash
# Test image OCR
python ocr.py

# Test preprocessing pipeline
python sample.py
```

### API Testing

```bash
# Test with sample files
curl -X POST "http://localhost:3000/api/upload" \
  -F "files=@Input/test.jpg" \
  -F "question=Extract all text from this image"
```

---

## 🔐 Security Considerations

1. **Environment Variables**: Never commit `.env` to version control
2. **CORS**: Configure `ALLOWED_ORIGINS` for production (avoid `*`)
3. **API Keys**: Rotate keys regularly and use secret management in production
4. **File Upload Limits**: Configure max file size in FastAPI settings
5. **Input Validation**: All file types are validated before processing

---

## 📖 API Documentation

Interactive API documentation is automatically generated by FastAPI:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - Multilingual OCR toolkit
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR engine
- [OpenAI](https://openai.com/) - GPT API for intelligent text extraction
- [RAKE-NLTK](https://pypi.org/project/rake-nltk/) - Keyword extraction

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

**Repository**: [https://github.com/Amosprakash/ImageOCR](https://github.com/Amosprakash/ImageOCR)
