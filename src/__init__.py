"""
XP Telegram Bot - A gamified productivity bot

This package contains the core functionality for the XP Telegram Bot,
including handlers, models, utilities, and Notion integration.
"""

__version__ = "1.0.0"
__author__ = "XP Bot Development Team"
__description__ = "A gamified Telegram bot for tracking XP, quests, and productivity"

# Core imports
from .config import config
from .exceptions import (
    XPBotError,
    NotionAPIError,
    UserNotFoundError,
    QuestNotFoundError,
    InsufficientRunesError,
    ConfigurationError
)

__all__ = [
    'config',
    'XPBotError',
    'NotionAPIError', 
    'UserNotFoundError',
    'QuestNotFoundError',
    'InsufficientRunesError',
    'ConfigurationError'
]