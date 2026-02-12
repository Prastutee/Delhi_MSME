"""
Health check and root endpoints for deployment verification
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {
        "status": "healthy",
        "service": "bharat-biz-agent",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Bharat Biz-Agent API",
        "description": "WhatsApp-first AI business co-pilot for Indian MSMEs",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "whatsapp_webhook": "/whatsapp/webhook",
            "telegram_webhook": "/telegram/webhook",
            "invoices": "/api/invoices",
            "inventory": "/api/inventory",
            "ledger": "/api/ledger",
            "logs": "/api/logs"
        },
        "docs": "/docs"
    }
