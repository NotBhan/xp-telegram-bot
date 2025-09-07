import asyncio
import logging
import logging.config
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import config
from src.handlers.start import register_start_handlers
from src.handlers.dashboard import register_dashboard_handlers
from src.handlers.quests import register_quest_handlers
from src.handlers.inventory import register_inventory_handlers
from src.handlers.shop import register_shop_handlers
from src.notion.notion_client import NotionClient

# Configure logging using config
logging.config.dictConfig(config.logging_config)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Initialize bot and services on startup"""
    logger.info("Starting XP Tracking Telegram Bot...")
    
    try:
        # Initialize Notion client and store bot instance
        notion_client = NotionClient()
        dispatcher['notion_client'] = notion_client
        dispatcher['bot'] = bot
        
        # Test Notion connection
        await notion_client.test_connection()
        logger.info("Notion client connection verified")
        
        # Register all handlers using the function-based registration
        register_start_handlers(dispatcher)
        register_dashboard_handlers(dispatcher)
        register_quest_handlers(dispatcher, notion_client)
        register_shop_handlers(dispatcher)
        register_inventory_handlers(dispatcher)
        
        logger.info("Bot started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

async def on_shutdown(dispatcher: Dispatcher):
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    
    try:
        # Close Notion client if needed
        if 'notion_client' in dispatcher:
            await dispatcher['notion_client'].close()
            logger.info("Notion client closed")
        
        logger.info("Bot shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main() -> None:
    """Main bot entry point with proper error handling"""
    try:
        logger.info(f"Starting {config.bot_name}...")
        
        # Initialize bot and dispatcher
        bot = Bot(
            token=config.bot_token, 
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Register startup and shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Start polling (handlers are registered in on_startup)
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during bot startup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)