# tests/test_api.py
"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import io


class TestOCREndpoints:
    """Tests for OCR API endpoints."""
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    @pytest.mark.integration
    def test_ocr_image_endpoint(self, test_client, sample_image, monkeypatch):
        """Test OCR image endpoint."""
        # Mock the OCR function
        from core import ocr_engine
        
        def mock_ocr(img, **kwargs):
            return {
                "success": True,
                "message": "Text extracted",
                "lines": [{"text": "Test", "conf": 0.9, "crop": None}]
            }
        
        monkeypatch.setattr(ocr_engine, "run_paddle_ocr", mock_ocr)
        
        files = {"file": ("test.png", io.BytesIO(sample_image), "image/png")}
        response = test_client.post("/api/ocr/image", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "text" in data


class TestRAGEndpoints:
    """Tests for RAG API endpoints."""
    
    @pytest.mark.requires_redis
    def test_rag_stats(self, test_client):
        """Test RAG stats endpoint."""
        response = test_client.get("/api/rag/stats")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "stores" in data


class TestAsyncEndpoints:
    """Tests for async task endpoints."""
    
    @pytest.mark.integration
    def test_async_ocr_submission(self, test_client, sample_image, monkeypatch):
        """Test async OCR task submission."""
        # Mock Celery task
        from core import celery_tasks
        
        class MockTask:
            id = "test-task-123"
        
        def mock_delay(*args, **kwargs):
            return MockTask()
        
        monkeypatch.setattr(celery_tasks.process_image_task, "delay", mock_delay)
        
        files = {"file": ("test.png", io.BytesIO(sample_image), "image/png")}
        response = test_client.post("/api/async/ocr/image", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "task_id" in data


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_file_type(self, test_client):
        """Test with invalid file type."""
        files = {"file": ("test.txt", io.BytesIO(b"test"), "text/plain")}
        response = test_client.post("/api/ocr/pdf", files=files)
        assert response.status_code == 400
    
    def test_missing_file(self, test_client):
        """Test with missing file."""
        response = test_client.post("/api/ocr/image")
        assert response.status_code == 422  # Validation error
