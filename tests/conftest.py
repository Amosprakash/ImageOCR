# tests/conftest.py
"""
Pytest configuration and fixtures for ImageAI tests.
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
import numpy as np
from PIL import Image
import io

# Set test environment
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"


@pytest.fixture
def test_client():
    """FastAPI test client."""
    from api.server import app
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


@pytest.fixture
def sample_image_np():
    """Create a sample numpy image."""
    return np.ones((100, 100, 3), dtype=np.uint8) * 255


@pytest.fixture
def mock_ocr_result():
    """Mock OCR result."""
    return {
        "success": True,
        "message": "Text extracted",
        "lines": [
            {"text": "Test Line 1", "conf": 0.95, "crop": np.ones((10, 50), dtype=np.uint8)},
            {"text": "Test Line 2", "conf": 0.85, "crop": np.ones((10, 50), dtype=np.uint8)}
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Extracted information"
    return mock_response


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "This is a test document with some sample text for testing purposes."


@pytest.fixture
def sample_fields():
    """Sample structured fields for testing."""
    return {
        "invoice_number": "INV-12345",
        "date": "2024-01-15",
        "total": "$1,234.56",
        "items": [
            {"name": "Item 1", "quantity": 2, "price": "$500"},
            {"name": "Item 2", "quantity": 1, "price": "$734.56"}
        ]
    }


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset all caches before each test."""
    from utils.file_handler import ocr_cache
    ocr_cache.clear()
    yield
    ocr_cache.clear()


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis connection."""
    mock_redis_client = MagicMock()
    mock_redis_client.ping.return_value = True
    return mock_redis_client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task."""
    mock_task = Mock()
    mock_task.id = "test-task-id-123"
    mock_task.state = "SUCCESS"
    mock_task.result = {"success": True, "text": "Test result"}
    return mock_task
