# CHANGELOG.md
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-08

### Added
- **Complete Document AI Platform transformation**
  - Modular architecture with `core/`, `api/`, `utils/`, `frontend/` structure
  - RAG (Retrieval-Augmented Generation) with FAISS vector storage
  - Knowledge Graph generation with NetworkX
  - Interactive Streamlit UI with 5 feature tabs
  - Docker containerization with multi-service orchestration
  - Celery + Redis for async task processing
  - Flower dashboard for task monitoring

- **Testing Infrastructure**
  - Comprehensive pytest test suite
  - Unit tests for core modules
  - Integration tests for API endpoints
  - Test coverage reporting (80%+ target)
  - pytest configuration with markers

- **Security Features**
  - API key authentication
  - Rate limiting middleware
  - Security headers (HSTS, X-Frame-Options, etc.)
  - Input validation with Pydantic
  - CORS configuration

- **Development Tools**
  - CI/CD pipeline with GitHub Actions
  - Pre-commit hooks (Black, Flake8, isort, mypy)
  - Static type checking with mypy
  - Code formatting with Black
  - Linting with Flake8
  - Security scanning with Bandit

- **Documentation**
  - Professional README with architecture diagrams
  - Docker deployment guide (DOCKER.md)
  - Contributing guidelines (CONTRIBUTING.md)
  - API documentation with OpenAPI/Swagger
  - Comprehensive inline code documentation

- **API Endpoints**
  - `/api/ocr/image` - Image OCR
  - `/api/ocr/pdf` - PDF OCR
  - `/api/ocr/document` - Multi-format OCR
  - `/api/ocr/video` - Video frame OCR
  - `/api/extract/fields` - Structured field extraction
  - `/api/rag/index` - RAG indexing
  - `/api/rag/query` - Semantic search
  - `/api/rag/reset` - Vector store management
  - `/api/async/ocr/image` - Async OCR
  - `/api/async/ocr/batch` - Batch OCR
  - `/api/async/status/{task_id}` - Task status

### Changed
- Reorganized codebase into modular structure
- Updated all import paths to new module structure
- Enhanced error handling and logging
- Improved API response formats with Pydantic schemas
- Updated requirements.txt with new dependencies

### Fixed
- Import path issues after reorganization
- Environment variable handling
- CORS configuration for production
- Rate limiting edge cases

### Removed
- Old monolithic files (image.py, utils.py, upload.py)
- Debug PNG files from root directory
- Temporary test files

## [1.0.0] - 2024-01-01

### Added
- Initial release with basic OCR functionality
- PaddleOCR + Tesseract hybrid pipeline
- Advanced image preprocessing
- FastAPI server
- Multi-format support (images, PDFs, documents)
- OpenAI GPT integration for field extraction
- Basic caching mechanism

---

## Upgrade Guide

### From 1.0.0 to 2.0.0

**Breaking Changes:**
- Import paths have changed due to code reorganization
- API authentication may be required (configure API_KEYS in .env)
- Rate limiting is enabled by default

**Migration Steps:**

1. **Update imports:**
   ```python
   # Old
   from image import run_paddle_ocr
   from utils import extract_text
   
   # New
   from core.ocr_engine import run_paddle_ocr
   from utils.file_handler import extract_text
   ```

2. **Update environment variables:**
   ```bash
   # Add to .env
   API_KEYS=your-api-key-1,your-api-key-2  # Optional
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

3. **Update Docker deployment:**
   ```bash
   docker-compose down
   docker-compose pull
   docker-compose up -d
   ```

4. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

**New Features to Try:**
- Async OCR processing with Celery
- RAG semantic search over documents
- Knowledge graph generation
- Streamlit UI at http://localhost:8501
- Flower monitoring at http://localhost:5555
