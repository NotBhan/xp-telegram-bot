"""
Custom exceptions for XP Telegram Bot
"""

class XPBotError(Exception):
    """Base exception for XP Bot"""
    pass

class NotionAPIError(XPBotError):
    """Raised when Notion API operations fail"""
    pass

class UserNotFoundError(XPBotError):
    """Raised when a user is not found in the database"""
    pass

class QuestNotFoundError(XPBotError):
    """Raised when a quest is not found"""
    pass

class InsufficientRunesError(XPBotError):
    """Raised when user doesn't have enough runes for an operation"""
    pass

class ConfigurationError(XPBotError):
    """Raised when there's a configuration issue"""
    pass