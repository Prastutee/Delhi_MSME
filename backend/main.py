"""
Bharat Biz-Agent - FastAPI Backend Entry Point
Telegram-Only Version
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import os

from config import settings
from db import init_db, log_event

# Import routers
# Messaging channels
# app.include_router(telegram_router, prefix="/telegram", tags=["Telegram"])
from tools.invoice import router as invoice_router
from tools.ledger import router as ledger_router
from tools.inventory import router as inventory_router

# Dashboard API routers
from routes.customers import router as customers_router
from routes.inventory import router as inventory_api_router
from routes.transactions import router as transactions_router
from routes.reminders import router as reminders_router
from routes.chat import router as chat_router
from routes.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\n" + "="*50)
    print("🚀 BHARAT BIZ-AGENT STARTING UP (TELEGRAM MODE)")
    print("="*50)
    
    # Initialize database
    await init_db()
    
    # Log startup
    print("✅ Backend server started (Ready)")
    
    print("="*50 + "\n")
    
    yield
    
    # Shutdown
    print("\n👋 Bharat Biz-Agent shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Bharat Biz-Agent",
    description="Telegram-first business co-pilot for Indian MSMEs",
    version="0.3.0-dashboard",
    lifespan=lifespan
)

# CORS middleware for dashboard
origins = ["*"]
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = allowed_origins_env.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# INCLUDE ROUTERS
# ============================================

# --------------------------------------------
# 1. AGENT TOOLS (Telegram/Bot Utilities)
# --------------------------------------------
# These endpoints are primarily used by the AI Agent to perform actions
# or by legacy webhook handlers.
# --------------------------------------------
app.include_router(invoice_router, prefix="/api/tools/invoices", tags=["Tools: Invoices"])
app.include_router(ledger_router, prefix="/api/tools/ledger", tags=["Tools: Ledger"])
# Note: Renamed prefix to /tools/ to avoid conflict with Dashboard API
app.include_router(inventory_router, prefix="/api/tools/inventory", tags=["Tools: Inventory"])


# --------------------------------------------
# 2. DASHBOARD API (Frontend Interface)
# --------------------------------------------
# These endpoints are used by the Next.js Dashboard for CRUD operations.
# --------------------------------------------
app.include_router(dashboard_router, tags=["Dashboard: Metrics"])
app.include_router(customers_router, tags=["Dashboard: Customers"])
app.include_router(inventory_api_router, tags=["Dashboard: Inventory"]) # prefix: /api/inventory
app.include_router(transactions_router, tags=["Dashboard: Transactions"])
app.include_router(reminders_router, tags=["Dashboard: Reminders"])
app.include_router(chat_router, tags=["Dashboard: Chat"])

# --------------------------------------------
# 3. UTILITIES (OCR, Voice, etc.)
# --------------------------------------------
from routes.stt import router as stt_router
app.include_router(stt_router, tags=["Utils: Voice"])
from routes.ocr import router as ocr_router
app.include_router(ocr_router, tags=["Utils: OCR"])


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check and welcome"""
    return {
        "status": "ok",
        "message": "🙏 Bharat Biz-Agent is running!",
        "version": "0.2.0-telegram-only",
        "mode": "Telegram Bot Polling/Webhook",
        "endpoints": {
            "telegram_webhook": "/telegram/webhook",
            "api_docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "telegram": "enabled" if settings and settings.telegram_enabled else "disabled"
    }


# ============================================
# DASHBOARD API ENDPOINTS
# ============================================


@app.get("/api/logs")
async def get_recent_logs(limit: int = 50, action_type: str = None):
    """Get recent business activity logs (User Facing Only)"""
    from db import get_logs
    
    # FIX 4: Filtering happens at write time (log_business_event).
    # No double-filtering needed here — all logs in the table are already valid.
    logs = await get_logs(limit=limit, action_type=action_type)
    return {"logs": logs}


@app.get("/api/chats/{user_phone}")
async def get_user_chats(user_phone: str, limit: int = 50):
    """Get chat history for a user"""
    from db import get_chat_history
    
    chats = await get_chat_history(user_phone, limit=limit)
    return {"chats": chats}



# ============================================
# MASTER PROMPT ENDPOINTS
# ============================================

from pydantic import BaseModel

class ConfirmRequest(BaseModel):
    user_id: str
    confirmed: bool = True

@app.post("/api/confirm")
async def api_confirm(request: ConfirmRequest):
    """Confirm pending action — routed through run_workflow for unified path"""
    from graph import run_workflow
    result = await run_workflow(request.user_id, "YES", language="en")
    return result

@app.post("/api/cancel")
async def api_cancel(request: ConfirmRequest):
    """Cancel pending action — routed through run_workflow for unified path"""
    from graph import run_workflow
    result = await run_workflow(request.user_id, "NO", language="en")
    return result


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
