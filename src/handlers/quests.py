import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient

logger = logging.getLogger(__name__)

async def show_quests(message: types.Message, user_id: int, notion_client: NotionClient, edit_message: bool = False):
    """Display available quests for the user."""
    try:
        user = await notion_client.get_user(user_id)
        if not user:
            await message.answer("❌ Profile not found. Please use /start to register first.")
            return

        quests = await notion_client.get_quests(user_id)
        first_name = message.from_user.first_name or "Adventurer"

        if not quests:
            default_quests = [
                {"name": "Morning Routine", "description": "Complete your morning routine", "xp_reward": 50, "category": "Daily"},
                {"name": "Exercise 30min", "description": "Do 30 minutes of physical exercise", "xp_reward": 100, "category": "Health"},
                {"name": "Read 20 pages", "description": "Read 20 pages of a book", "xp_reward": 75, "category": "Learning"}
            ]
            for quest_data in default_quests:
                await notion_client.create_quest(user_id, quest_data)
            quests = await notion_client.get_quests(user_id)

        if not quests:
            await message.answer("🎯 No quests available right now. Check back later!")
            return

        quest_text = f"🎯 **{first_name}'s Daily Quests** 🎯\n\n"
        buttons = []

        for i, quest in enumerate(quests[:5], 1):
            quest_name = quest["properties"]["Quest Name"]["title"][0]["text"]["content"]
            quest_desc = quest["properties"]["Description"]["rich_text"][0]["text"]["content"] if quest["properties"]["Description"]["rich_text"] else ""
            xp_reward = quest["properties"]["XP Reward"]["number"] or 0
            status = quest["properties"]["Status"]["select"]["name"] if quest["properties"]["Status"]["select"] else "Active"
            status_emoji = "⏳" if status == "Active" else "✅"

            quest_text += f'{i}. **{quest_name}** {status_emoji}\n'
            if quest_desc:
                quest_text += f'   _{quest_desc}_\n'
            quest_text += f'   💎 **+{xp_reward} XP**\n\n'

            if status == "Active":
                buttons.append([InlineKeyboardButton(f"{i}. Complete {quest_name}", callback_data=f"complete_{quest['id']}")])

        quest_text += "\n📜 Complete quests to earn XP and level up!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons + [
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
             InlineKeyboardButton("🔄 Refresh", callback_data="quests")]
        ])

        if edit_message:
            await message.edit_text(quest_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(quest_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in show_quests: {e}")
        await message.answer("❌ Error loading quests. Please try again later.")

def register_quest_handlers(dp: Dispatcher):
    """Register quest command handlers."""

    @dp.message(Command("quests"))
    async def cmd_quests_message(message: types.Message, state: FSMContext):
        """Handle /quests command."""
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_quests(message, message.from_user.id, notion_client)

    @dp.callback_query(F.data == "quests")
    async def cmd_quests_callback(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle quests callback for refresh."""
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_quests(callback_query.message, callback_query.from_user.id, notion_client, edit_message=True)
        await callback_query.answer()

    @dp.callback_query(F.data.startswith("complete_"))
    async def cmd_complete_quest(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle quest completion."""
        quest_id = callback_query.data.split("_")[-1]
        user_id = callback_query.from_user.id
        notion_client: NotionClient = dp.get('notion_client')

        try:
            result = await notion_client.complete_quest(quest_id)
            if result:
                xp_earned = result["xp_earned"]
                await callback_query.answer(f"🎉 Quest Completed! You earned {xp_earned} XP!", show_alert=True)
                await show_quests(callback_query.message, user_id, notion_client, edit_message=True)
            else:
                await callback_query.answer("❌ Could not complete quest.", show_alert=True)
        except Exception as e:
            logger.error(f"Error completing quest: {e}")
            await callback_query.answer("❌ An error occurred while completing the quest.", show_alert=True)