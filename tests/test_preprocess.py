# tests/test_preprocess.py
"""
Unit tests for image preprocessing module.
"""
import pytest
import numpy as np
import cv2
from core.preprocess import (
    safe_to_gray, deskew_image, detect_blur, conditional_deblur,
    force_white_background, preprocess_image, validate,
    is_low_contrast, is_low_resolution, ensure_bgr
)


class TestSafeToGray:
    """Tests for safe_to_gray function."""
    
    def test_already_grayscale(self):
        """Test with already grayscale image."""
        gray_img = np.ones((100, 100), dtype=np.uint8) * 128
        result = safe_to_gray(gray_img)
        assert result.shape == (100, 100)
        assert len(result.shape) == 2
    
    def test_bgr_to_gray(self):
        """Test BGR to grayscale conversion."""
        bgr_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = safe_to_gray(bgr_img)
        assert result.shape == (100, 100)
        assert len(result.shape) == 2
    
    def test_bgra_to_gray(self):
        """Test BGRA to grayscale conversion."""
        bgra_img = np.ones((100, 100, 4), dtype=np.uint8) * 128
        result = safe_to_gray(bgra_img)
        assert result.shape == (100, 100)
        assert len(result.shape) == 2


class TestBlurDetection:
    """Tests for blur detection."""
    
    def test_sharp_image(self, sample_image_np):
        """Test with sharp image."""
        is_blurry, score = detect_blur(sample_image_np, threshold=100.0)
        assert isinstance(is_blurry, bool)
        assert isinstance(score, (int, float))
    
    def test_blurry_image(self):
        """Test with blurred image."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        blurred = cv2.GaussianBlur(img, (15, 15), 10)
        is_blurry, score = detect_blur(blurred, threshold=100.0)
        assert isinstance(is_blurry, bool)


class TestValidation:
    """Tests for image validation."""
    
    def test_valid_image(self, sample_image_np):
        """Test with valid image."""
        is_valid, msg = validate(sample_image_np)
        assert isinstance(is_valid, bool)
        assert isinstance(msg, str)
    
    def test_low_resolution(self):
        """Test with low resolution image."""
        small_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
        is_valid, msg = validate(small_img)
        assert is_valid == False
        assert "resolution" in msg.lower()


class TestEnsureBGR:
    """Tests for ensure_bgr function."""
    
    def test_grayscale_to_bgr(self):
        """Test grayscale to BGR conversion."""
        gray = np.ones((100, 100), dtype=np.uint8) * 128
        result = ensure_bgr(gray)
        assert result.shape == (100, 100, 3)
    
    def test_already_bgr(self):
        """Test with already BGR image."""
        bgr = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = ensure_bgr(bgr)
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result, bgr)


class TestPreprocessImage:
    """Tests for preprocess_image function."""
    
    def test_basic_preprocessing(self, sample_image_np):
        """Test basic preprocessing pipeline."""
        result = preprocess_image(sample_image_np, debug=False)
        assert result is not None
        assert len(result.shape) == 2  # Should be grayscale
    
    def test_debug_mode(self, sample_image_np, tmp_path, monkeypatch):
        """Test preprocessing with debug mode."""
        monkeypatch.chdir(tmp_path)
        result = preprocess_image(sample_image_np, debug=True)
        assert result is not None


@pytest.mark.unit
class TestContrastAndResolution:
    """Tests for contrast and resolution checks."""
    
    def test_low_contrast_detection(self):
        """Test low contrast detection."""
        # Create low contrast image
        low_contrast = np.ones((100, 100, 3), dtype=np.uint8) * 128
        assert is_low_contrast(low_contrast, threshold=15.0) == True
    
    def test_high_contrast_detection(self):
        """Test high contrast detection."""
        # Create high contrast image
        high_contrast = np.zeros((100, 100, 3), dtype=np.uint8)
        high_contrast[50:, :] = 255
        assert is_low_contrast(high_contrast, threshold=15.0) == False
    
    def test_low_resolution_detection(self):
        """Test low resolution detection."""
        small_img = np.ones((100, 100, 3), dtype=np.uint8)
        assert is_low_resolution(small_img, min_height=500) == True
    
    def test_high_resolution_detection(self):
        """Test high resolution detection."""
        large_img = np.ones((1000, 1000, 3), dtype=np.uint8)
        assert is_low_resolution(large_img, min_height=500) == False
