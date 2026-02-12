"""
Receipt OCR via OCR.Space API (Sole Provider)
Clean, isolated implementation. NO Google Vision/Gemini.
"""
import os
import httpx
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

OCR_SPACE_API_URL = "https://api.ocr.space/parse/image"


import io
from PIL import Image, ImageOps, ImageEnhance

def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Enhance image for OCR: Grayscale -> Contrast -> Upscale
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # 1. Convert to grayscale
        img = ImageOps.grayscale(img)
        
        # 2. Increase contrast (2.0x)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 3. Upscale if width < 1500px (OCR.Space engine 2 likes bigger images)
        w, h = img.size
        target_w = 1500
        if w < target_w:
             factor = target_w / w
             new_size = (int(w * factor), int(h * factor))
             img = img.resize(new_size, Image.Resampling.LANCZOS)
             print(f"DEBUG: Upscaled image from {w}x{h} to {new_size}")
             
        # Save to bytes
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:
        print(f"DEBUG: Preprocessing failed: {e}")
        return image_bytes # Fallback to original


async def extract_text_ocr_space(image_bytes: bytes) -> str:
    """
    Extract text using OCR.Space API with preprocessing
    """
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        return "[OCR_SPACE_API_KEY missing]"

    try:
        # Preprocess
        processed_bytes = preprocess_image(image_bytes)
        
        # Debug: Check inputs
        print(f"DEBUG: Sending {len(processed_bytes)} bytes to OCR.Space")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                OCR_SPACE_API_URL,
                files={"file": ("receipt.jpg", processed_bytes, "image/jpeg")},
                data={
                    "apikey": api_key,
                    "language": "eng",
                    "isOverlayRequired": "false",
                    "detectOrientation": "true",
                    "scale": "true",
                    "isTable": "true",
                    "OCREngine": "2"
                }
            )

            if response.status_code != 200:
                print(f"DEBUG: API Error {response.status_code} - {response.text}")
                return f"[API Error: {response.status_code}]"

            result = response.json()

            # Debug: Print Parsed Text Length
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                text = parsed_results[0].get("ParsedText", "")
                print(f"DEBUG: Extracted {len(text)} chars:\n{text[:200]}...")
            else:
                print(f"DEBUG: No ParsedResults found.\nRaw: {json.dumps(result)}")

            # Check for OCR.Space errors
            if result.get("IsErroredOnProcessing"):
                 error_msg = str(result.get("ErrorMessage"))
                 return f"[OCR Error: {error_msg}]"
            
            if not parsed_results:
                return "[OCR Error: No result returned]"

            parsed_text = parsed_results[0].get("ParsedText", "")
            return parsed_text.strip()

    except Exception as e:
        print(f"OCR.Space Exception: {e}")
        return f"[Exception: {str(e)}]"


# process_receipt_for_inventory Removed

# FIX 5: Backward compatibility alias
extract_text_from_receipt = extract_text_ocr_space
