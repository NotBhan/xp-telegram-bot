"""
Configuration management for XP Telegram Bot
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration with validation"""
    
    # Required environment variables
    REQUIRED_VARS = [
        'BOT_TOKEN',
        'NOTION_TOKEN', 
        'XP_DB_ID',
        'QUEST_DB_ID',
        'CHALLENGE_DB_ID',
        'INVENTORY_DB_ID'
    ]
    
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.xp_db_id = os.getenv('XP_DB_ID')
        self.quest_db_id = os.getenv('QUEST_DB_ID')
        self.challenge_db_id = os.getenv('CHALLENGE_DB_ID')
        self.inventory_db_id = os.getenv('INVENTORY_DB_ID')
        
        # Optional settings with defaults
        self.bot_name = os.getenv('BOT_NAME', 'XP Tracker Bot')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        self.validate()
    
    def validate(self) -> None:
        """Validate that all required configuration is present"""
        missing_vars = []
        for var in self.REQUIRED_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please check your .env file and ensure all required variables are set."
            )
    
    @property
    def logging_config(self) -> dict:
        """Get logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.log_level,
                    'formatter': 'detailed' if self.debug else 'default',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': 'bot.log',
                    'mode': 'a'
                }
            },
            'loggers': {
                '': {  # root logger
                    'level': self.log_level,
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'aiogram': {
                    'level': 'WARNING',
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'notion_client': {
                    'level': 'WARNING', 
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            }
        }

# Global config instance
config = Config()