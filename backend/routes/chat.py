"""
Chat API Route
Direct interface to the agent workflow
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import run_workflow
from db import log_debug_event, log_business_event

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    user_id: str  # Can be phone number or session ID
    message: str

class ChatResponse(BaseModel):
    reply: str
    show_buttons: bool = False
    buttons: list = []

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the agent workflow
    Returns the agent's text response and optional buttons
    """
    try:
        # Use user_id as phone number for now (dashboard user)
        # In future, could map session ID to a specific "dashboard" user
        user_phone = request.user_id 
        
        # Log incoming
        print(f"💬 Chat from {user_phone}: {request.message}")
        
        # Run workflow
        result = await run_workflow(
            user_phone=user_phone,
            message=request.message,
            media_url=None,
            media_type=None,
            language="en"  # FORCE ENGLISH FOR WEBSITE
        )
        
        return result
        
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        log_debug_event("chat_api_error", f"Chat endpoint error: {str(e)}", str(request.dict()))
        raise HTTPException(status_code=500, detail=str(e))
