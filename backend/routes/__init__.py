"""
Routes package initialization
"""
from .customers import router as customers_router
from .inventory import router as inventory_router
from .transactions import router as transactions_router
from .reminders import router as reminders_router

__all__ = [
    "customers_router",
    "inventory_router",
    "transactions_router",
    "reminders_router"
]
