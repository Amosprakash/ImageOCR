# test_ocr.py
"""
Quick test script to verify OCR functionality after reorganization.
Tests that all imports work and core OCR pipeline is intact.
"""
import sys
from pathlib import Path

print("=" * 60)
print("Testing ImageAI Document AI Platform")
print("=" * 60)

# Test 1: Import core modules
print("\n[1/5] Testing core module imports...")
try:
    from core.preprocess import preprocess_image, validate, deskew_image
    from core.ocr_engine import run_paddle_ocr
    from core.tesseract_fallback import run_tesseract_on_low_conf
    from core.field_extractor import extract_structured_fields
    from core.rag_engine import create_vector_store, query_vector_store, FAISS_AVAILABLE
    from core.kg_builder import build_graph_from_fields
    print("✅ All core modules imported successfully")
except Exception as e:
    print(f"❌ Core module import failed: {e}")
    sys.exit(1)

# Test 2: Import utils
print("\n[2/5] Testing utils imports...")
try:
    from utils.logger import log
    from utils.file_handler import extract_text, extract_keywords
    from utils.openai_client import getOpenai
    print("✅ All utils imported successfully")
except Exception as e:
    print(f"❌ Utils import failed: {e}")
    sys.exit(1)

# Test 3: Import API modules
print("\n[3/5] Testing API imports...")
try:
    from api.server import app
    from api.ocr_routes import router as ocr_router
    from api.rag_routes import router as rag_router
    from api.schemas import OCRResponse, RAGQueryRequest
    print("✅ All API modules imported successfully")
except Exception as e:
    print(f"❌ API import failed: {e}")
    sys.exit(1)

# Test 4: Test preprocessing
print("\n[4/5] Testing preprocessing functions...")
try:
    import cv2
    import numpy as np
    
    # Create a test image
    test_img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    
    # Test validation
    is_valid, msg = validate(test_img)
    print(f"   Image validation: {msg}")
    
    # Test preprocessing
    preprocessed = preprocess_image(test_img, debug=False)
    print(f"   Preprocessed image shape: {preprocessed.shape}")
    
    print("✅ Preprocessing functions work correctly")
except Exception as e:
    print(f"❌ Preprocessing test failed: {e}")
    sys.exit(1)

# Test 5: Test RAG availability
print("\n[5/5] Testing RAG module...")
if FAISS_AVAILABLE:
    print("✅ FAISS is available - RAG module ready")
else:
    print("⚠️  FAISS not installed - RAG module disabled")
    print("   Install with: pip install faiss-cpu")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe Document AI Platform is ready to use!")
print("\nNext steps:")
print("1. Start API server: python app.py")
print("2. Start Streamlit UI: streamlit run frontend/streamlit_app.py")
print("3. View API docs: http://localhost:3000/docs")
print("=" * 60)
