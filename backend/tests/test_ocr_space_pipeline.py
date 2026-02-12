"""
OCR Regression Tests (OCR.Space Provider)
Verifies:
1. Extract endpoint calls OCR.Space (mocked) and returns text.
2. Error handling for empty/failed OCR.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_ocr_extract_success():
    """
    Test extraction flow:
    - Mock extraction tool to return text
    - Verify response structure
    """
    print("\n🧪 TEST: OCR Extraction (Success)")
    
    # Patch the tool imported in routes.ocr
    with patch("routes.ocr.extract_text_ocr_space", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = "Expected Extracted Text"
        
        # Call API
        files = {"file": ("receipt.jpg", b"fake_bytes", "image/jpeg")}
        response = client.post("/api/ocr/extract", files=files)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Expected Extracted Text"
        assert data["source"] == "ocr_space"
        
        print("   ✅ Text extracted successfully")


@pytest.mark.asyncio
async def test_ocr_extract_failure():
    """
    Test extraction flow when OCR fails (returns error string)
    """
    print("\n🧪 TEST: OCR Extraction (Failure)")
    
    with patch("routes.ocr.extract_text_ocr_space", new_callable=AsyncMock) as mock_extract:
        # Simulate Error return from tool
        mock_extract.return_value = "[OCR Error: No text found]"
        
        files = {"file": ("bad.jpg", b"bad_bytes", "image/jpeg")}
        response = client.post("/api/ocr/extract", files=files)
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "OCR Error" in data["detail"]
        
        print("   ✅ Handled OCR failure gracefully")


