"""
STT API Route
Handles voice input from dashboard using Groq Whisper
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from tools.voice import transcribe_audio_groq

router = APIRouter(prefix="/api/stt", tags=["Voice"])

@router.post("")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio file using Groq Whisper
    Returns: {"transcript": "text"}
    """
    try:
        # Read file bytes
        content = await file.read()
        
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
            
        print(f"🎤 STT Request: Received {len(content)} bytes")
        
        # Call Groq Whisper (Force English for Website)
        transcript = await transcribe_audio_groq(content, language="en")
        
        if transcript.startswith("[") and "Error" in transcript:
             raise HTTPException(status_code=500, detail=transcript)
             
        print(f"   ✅ Transcript: {transcript}")
        return {"transcript": transcript}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
