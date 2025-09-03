import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient

logger = logging.getLogger(__name__)

def register_start_handlers(dp: Dispatcher):
    """Register start command handlers"""
    
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        """Handle /start command - Register new user"""
        await state.clear()
        
        user_id = message.from_user.id
        username = message.from_user.username or str(user_id)
        first_name = message.from_user.first_name or username
        
        notion_client: NotionClient = dp.get('notion_client')
        
        try:
            # Check if user already exists
            existing_user = await notion_client.get_user(user_id)
            
            if existing_user:
                # Welcome back message
                xp = existing_user["properties"]["XP"]["number"] or 0
                level = existing_user["properties"]["Level"]["number"] or 1
                runes = existing_user["properties"]["Runes"]["number"] or 0
                
                welcome_text = f"""
🎮 **Welcome back to XP Tracker!** 🎮

👤 **{first_name}**
📊 **Level:** {level}
⭐ **XP:** {xp}
💎 **Runes:** {runes}

Ready to continue your adventure? Use the menu below to get started!
                """
            else:
                # Create new user profile
                await notion_client.create_user(user_id, username, first_name)
                
                welcome_text = f"""
🎉 **Welcome to XP Tracker!** 🎉

Hey {first_name}! I've created your adventurer profile in our system. 

🎯 **Your Starting Stats:**
📊 **Level:** 1
⭐ **XP:** 0
💎 **Runes:** 0
🏆 **Title:** Novice

Let's start your gamified life journey! Check your dashboard and complete quests to level up.
                """
            
            # Create keyboard with main actions
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"),
                    InlineKeyboardButton(text="🎯 Quests", callback_data="quests")
                ],
                [
                    InlineKeyboardButton(text="🛒 Shop", callback_data="shop"),
                    InlineKeyboardButton(text="🎒 Inventory", callback_data="inventory")
                ]
            ])
            
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await message.answer(
                "❌ Sorry, there was an error setting up your profile. Please try again later."
            )

    @dp.callback_query(F.data == "start")
    async def handle_start_callback(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle start button callback"""
        await state.clear()
        # Re-trigger the start command logic, but for a callback
        message = callback_query.message
        message.from_user = callback_query.from_user # Ensure user context is correct
        await cmd_start(message, state)
        await callback_query.answer()