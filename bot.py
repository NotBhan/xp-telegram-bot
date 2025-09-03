import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from src.handlers.start import register_start_handlers
from src.handlers.dashboard import register_dashboard_handlers
from src.handlers.quests import register_quest_handlers
from src.handlers.shop import register_shop_handlers
from src.handlers.inventory import register_inventory_handlers
from src.notion.notion_client import NotionClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get bot token from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")

async def on_startup(dispatcher: Dispatcher):
    """Initialize bot and services on startup"""
    logger.info("Starting XP Tracking Telegram Bot...")
    
    # Initialize Notion client
    dispatcher['notion_client'] = NotionClient()
    
    logger.info("Bot started successfully!")

async def on_shutdown(dispatcher: Dispatcher):
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    
    # Close Notion client if needed
    if hasattr(dispatcher, 'workflow_data') and 'notion_client' in dispatcher.workflow_data:
        await dispatcher.workflow_data['notion_client'].close()
    
    logger.info("Bot shutdown complete")

async def main():
    """Main bot entry point"""
    # Initialize bot and dispatcher
    bot = Bot(token=TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Register all handlers
    register_start_handlers(dp)
    register_dashboard_handlers(dp)
    register_quest_handlers(dp)
    register_shop_handlers(dp)
    register_inventory_handlers(dp)
    
    # Start the bot
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())