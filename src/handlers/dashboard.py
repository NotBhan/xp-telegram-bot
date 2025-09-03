import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient

logger = logging.getLogger(__name__)

async def show_dashboard(message: types.Message, notion_client: NotionClient):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Adventurer"

    try:
        user = await notion_client.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Profile not found. Please use /start to register first."
            )
            return

        xp = user["properties"]["XP"]["number"] or 0
        level = user["properties"]["Level"]["number"] or 1
        runes = user["properties"]["Runes"]["number"] or 0

        current_xp_in_level = xp - ((level - 1) ** 2 * 100) if level > 1 else xp
        xp_needed_for_next = (level ** 2 * 100) - ((level - 1) ** 2 * 100)
        progress_percent = min(int((current_xp_in_level / xp_needed_for_next) * 100), 100)

        progress_bar = "█" * (progress_percent // 10) + "░" * (10 - (progress_percent // 10))

        titles = ["Novice", "Apprentice", "Adventurer", "Hero", "Champion", 
                    "Legend", "Master", "Grandmaster", "Elder", "Immortal"]
        title_index = min((level - 1) // 25, len(titles) - 1)
        title = titles[title_index]

        dashboard_text = f"""
🎮 **{first_name}'s Adventure Dashboard** 🎮

📊 **Level:** {level} {title}
⭐ **Total XP:** {xp:,}
📈 **Progress:** [{progress_bar}] {progress_percent}%
💎 **Runes:** {runes:,}
🔥 **Streak:** Coming soon!

🎯 **Next Level:** {current_xp_in_level}/{xp_needed_for_next} XP
🏆 **Current Title:** {title}

📋 **Quick Actions:**
        """

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 Daily Quests", callback_data="quests"),
                InlineKeyboardButton(text="🛒 Item Shop", callback_data="shop")
            ],
            [
                InlineKeyboardButton(text="🎒 My Inventory", callback_data="inventory"),
                InlineKeyboardButton(text="⚔️ Challenges", callback_data="challenges")
            ],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="dashboard")]
        ])

        # Check if we are editing a message or sending a new one
        if hasattr(message, 'message_id'):
            await message.edit_text(dashboard_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(dashboard_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in dashboard handler: {e}")
        await message.answer(
            "❌ Error loading dashboard. Please try again later."
        )

def register_dashboard_handlers(dp: Dispatcher):
    """Register dashboard command handlers"""

    @dp.message(Command("dashboard"))
    async def cmd_dashboard(message: types.Message, state: FSMContext):
        """Handle /dashboard command - Show user stats"""
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_dashboard(message, notion_client)

    @dp.callback_query(F.data == "dashboard")
    async def callback_dashboard(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle dashboard callback"""
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        # Pass the message object to be edited
        await show_dashboard(callback_query.message, notion_client)
        await callback_query.answer()