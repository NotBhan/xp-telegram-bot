"""
Bot handlers package

This package contains all Telegram bot command handlers and message handlers.
"""

from .start import register_start_handlers
from .dashboard import register_dashboard_handlers
from .quests import register_quest_handlers
from .shop import register_shop_handlers
from .inventory import register_inventory_handlers

def register_all_handlers(dp):
    """Register all bot handlers"""
    register_start_handlers(dp)
    register_dashboard_handlers(dp)
    register_quest_handlers(dp)
    register_shop_handlers(dp)
    register_inventory_handlers(dp)