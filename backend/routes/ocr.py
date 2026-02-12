"""
OCR API Route — Text Extraction Only
POST /api/ocr/extract → Extract text from image (No DB mutation)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ocr import extract_text_ocr_space

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

@router.post("/extract")
async def extract_text(file: UploadFile = File(...)):
    """
    Extract text from an uploaded image.
    Returns raw text for the chat agent to process.
    """
    try:
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        print(f"📸 OCR Extract Request: Received {len(content)} bytes ({file.filename})")

        # Call OCR.Space Trace
        text = await extract_text_ocr_space(content)

        if text.startswith("[") and "Error" in text:
             raise HTTPException(status_code=500, detail=text)

        print(f"   ✅ OCR Extracted: {len(text)} chars")

        return {
            "text": text,
            "source": "ocr_space"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

