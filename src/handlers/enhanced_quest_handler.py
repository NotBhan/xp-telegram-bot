"""
Enhanced Quest Handler for Telegram Bot

Implements all quest-related commands with the new Quest & Side Quest system:
- /quests - Show current quests with enhanced display
- /complete <quest_id> - Complete quest with full reward processing
- /sidequest - Trigger optional side quest
- /reroll <quest_id> - Spend runes to reroll quest
"""

import logging
from datetime import datetime
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from ..enhanced_notion_client import EnhancedNotionClient
from ..quest_system import QuestSystem, QuestStatus
from ..side_quest_manager import SideQuestManager, SideQuestTrigger
from ..gamification import GamificationEngine

logger = logging.getLogger(__name__)

class EnhancedQuestHandler:
    """Enhanced quest handler with new quest system integration"""
    
    def __init__(self, notion_client: EnhancedNotionClient):
        self.notion = notion_client
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all quest-related command handlers"""
        
        @self.router.message(Command("quests"))
        async def show_quests_command(message: types.Message):
            """Show current quests with enhanced display"""
            await self.show_enhanced_quests(message)
        
        @self.router.message(Command("complete"))
        async def complete_quest_command(message: types.Message):
            """Complete a quest: /complete Q1"""
            await self.handle_quest_completion(message)
        
        @self.router.message(Command("sidequest"))
        async def trigger_side_quest_command(message: types.Message):
            """Manually trigger a side quest"""
            await self.trigger_side_quest(message)
        
        @self.router.message(Command("reroll"))
        async def reroll_quest_command(message: types.Message):
            """Reroll a quest: /reroll Q1"""
            await self.handle_quest_reroll(message)
        
        @self.router.callback_query(F.data.startswith("complete_"))
        async def complete_quest_callback(callback: CallbackQuery):
            """Handle quest completion via inline button"""
            quest_id = callback.data.split("_", 1)[1]
            await self.complete_quest_by_id(callback, quest_id)
        
        @self.router.callback_query(F.data.startswith("reroll_"))
        async def reroll_quest_callback(callback: CallbackQuery):
            """Handle quest reroll via inline button"""
            quest_id = callback.data.split("_", 1)[1]
            await self.reroll_quest_by_id(callback, quest_id)
        
        @self.router.callback_query(F.data == "trigger_sidequest")
        async def trigger_side_quest_callback(callback: CallbackQuery):
            """Handle side quest trigger via inline button"""
            await self.trigger_side_quest_callback_handler(callback)
    
    async def get_user_data(self, user_id: int) -> dict:
        """Get comprehensive user data for quest operations"""
        # This should integrate with your existing user data retrieval
        # For now, returning mock data structure
        return {
            "user_id": user_id,
            "level": 7,
            "total_xp": 850,
            "runes": 120,
            "streak": 12,
            "last_quest_date": datetime.now(),
            "active_buffs": [],
            "active_debuffs": []
        }
    
    async def show_enhanced_quests(self, message: types.Message):
        """Display quests with enhanced formatting per specification"""
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name or "Adventurer"
            
            # Get user data
            user_data = await self.get_user_data(user_id)
            
            # Check if user needs new daily quests
            today = datetime.now().date()
            last_quest_date = user_data.get("last_quest_date")
            
            if not last_quest_date or last_quest_date.date() < today:
                # Create new daily quest set
                quest_set = await self.notion.create_daily_quests(user_id, user_data)
                quests_display = self._format_quest_set_display(quest_set, first_name)
            else:
                # Get existing quests from today
                # This would query Notion for today's quests
                quest_set = {"main_quests": [], "side_quest": None}  # Placeholder
                quests_display = "🎯 **Loading your current quests...**"
            
            # Create enhanced keyboard
            keyboard = self._create_quest_keyboard(quest_set)
            
            await message.answer(
                quests_display,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing enhanced quests: {e}")
            await message.answer(
                "❌ Error loading quests. Please try again later.",
                reply_markup=self._create_fallback_keyboard()
            )
    
    def _format_quest_set_display(self, quest_set: dict, first_name: str) -> str:
        """Format quest display according to specification"""
        display = f"🎯 **{first_name}'s Daily Quests**\\n\\n"
        
        # Main quests section
        if quest_set.get("main_quests"):
            display += "📜 **Quests:**\\n"
            for i, quest_data in enumerate(quest_set["main_quests"], 1):
                quest_name = quest_data.get("name", "Unknown Quest")
                difficulty = quest_data.get("difficulty", "Easy")
                xp_reward = quest_data.get("xp_reward", 0)
                rune_reward = quest_data.get("rune_reward", 0)
                quest_id = quest_data.get("quest_id", f"Q{i}")
                
                display += f"[ ] {quest_id} — {quest_name} ({difficulty}) — {xp_reward} XP, {rune_reward} Runes\\n"
        
        # Side quest section
        if quest_set.get("side_quest"):
            side_quest = quest_set["side_quest"]
            display += "\\n✨ **Side Quest:**\\n"
            display += f"[ ] {side_quest.get('quest_id', 'SQ1')} — {side_quest.get('name', 'Mystery Quest')} "
            display += f"({side_quest.get('difficulty', 'Easy')}) — {side_quest.get('xp_reward', 0)} XP, "
            display += f"{side_quest.get('rune_reward', 0)} Runes\\n"
        
        # Add instructions
        display += "\\n💡 Complete quests to earn rewards and maintain your streak!"
        
        return display
    
    def _create_quest_keyboard(self, quest_set: dict) -> InlineKeyboardMarkup:
        """Create enhanced keyboard for quest interactions"""
        buttons = []
        
        # Complete buttons for each quest
        if quest_set.get("main_quests"):
            for quest_data in quest_set["main_quests"]:
                quest_id = quest_data.get("quest_id", "Q1")
                buttons.append([
                    InlineKeyboardButton(
                        text=f"✅ Complete {quest_id}",
                        callback_data=f"complete_{quest_data.get('notion_id', quest_id)}"
                    )
                ])
        
        if quest_set.get("side_quest"):
            side_quest = quest_set["side_quest"]
            buttons.append([
                InlineKeyboardButton(
                    text=f"✨ Complete {side_quest.get('quest_id', 'SQ1')}",
                    callback_data=f"complete_{side_quest.get('notion_id', 'SQ1')}"
                )
            ])
        
        # Action buttons
        action_row = []
        if not quest_set.get("side_quest"):
            action_row.append(
                InlineKeyboardButton(text="🌟 Get Side Quest", callback_data="trigger_sidequest")
            )
        
        action_row.append(
            InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")
        )
        
        if action_row:
            buttons.append(action_row)
        
        # Reroll options (if user has enough runes)
        reroll_row = []
        if quest_set.get("main_quests"):
            for quest_data in quest_set["main_quests"][:2]:  # Limit to first 2 for space
                quest_id = quest_data.get("quest_id", "Q1")
                reroll_row.append(
                    InlineKeyboardButton(
                        text=f"🔄 Reroll {quest_id}",
                        callback_data=f"reroll_{quest_data.get('notion_id', quest_id)}"
                    )
                )
        
        if reroll_row:
            buttons.append(reroll_row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def _create_fallback_keyboard(self) -> InlineKeyboardMarkup:
        """Create fallback keyboard when quest loading fails"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Try Again", callback_data="quests")],
            [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")]
        ])
    
    async def handle_quest_completion(self, message: types.Message):
        """Handle quest completion from command"""
        try:
            # Parse quest ID from command
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await message.answer(
                    "❌ Please specify a quest ID: `/complete Q1`",
                    parse_mode="Markdown"
                )
                return
            
            quest_id = command_parts[1]
            user_id = message.from_user.id
            
            # Get user data
            user_data = await self.get_user_data(user_id)
            
            # Find quest by ID (this would query Notion)
            # For now, using placeholder logic
            await message.answer(f"🔄 Completing quest {quest_id}...")
            
            # Process completion
            completion_result = await self.complete_quest_by_quest_id(user_id, quest_id, user_data)
            
            if completion_result.get("error"):
                await message.answer(f"❌ {completion_result['error']}")
            else:
                # Format completion response
                response = self._format_completion_response(completion_result)
                await message.answer(response, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error handling quest completion: {e}")
            await message.answer("❌ Error completing quest. Please try again.")
    
    async def complete_quest_by_id(self, callback: CallbackQuery, notion_id: str):
        """Complete quest by Notion ID"""
        try:
            user_id = callback.from_user.id
            user_data = await self.get_user_data(user_id)
            
            # Process completion through enhanced Notion client
            completion_result = await self.notion.complete_quest(notion_id, user_id, user_data)
            
            if completion_result.get("error"):
                await callback.answer(f"❌ {completion_result['error']}", show_alert=True)
            else:
                # Format success response
                response = self._format_completion_response(completion_result)
                
                await callback.message.edit_text(
                    response,
                    parse_mode="Markdown",
                    reply_markup=self._create_post_completion_keyboard()
                )
                
                await callback.answer("🎉 Quest completed!", show_alert=True)
        
        except Exception as e:
            logger.error(f"Error completing quest by ID: {e}")
            await callback.answer("❌ Error completing quest", show_alert=True)
    
    def _format_completion_response(self, completion_result: dict) -> str:
        """Format quest completion response"""
        quest_info = completion_result.get("quest_completed", {}).get("quest", {})
        rewards = completion_result.get("rewards", {})
        level_progression = completion_result.get("level_progression", {})
        streak_update = completion_result.get("streak_update", {})
        new_totals = completion_result.get("new_totals", {})
        
        response = f"🎉 **Quest Completed!**\\n\\n"
        response += f"✅ {quest_info.get('name', 'Quest')}\\n\\n"
        
        # Rewards section
        response += f"💎 **Rewards Earned:**\\n"
        response += f"• +{rewards.get('final_xp_gained', 0)} XP\\n"
        response += f"• +{rewards.get('final_runes_gained', 0)} Runes\\n"
        
        # Level up notification
        if level_progression.get("level_up_occurred", False):
            levels_gained = level_progression.get("levels_gained", 1)
            new_level = level_progression.get("new_level", 1)
            response += f"\\n🆙 **LEVEL UP!** Level {new_level}"
            if levels_gained > 1:
                response += f" (+{levels_gained} levels!)"
            response += "\\n"
        
        # Streak update
        if streak_update.get("streak_updated", False):
            new_streak = streak_update.get("new_streak", 0)
            response += f"\\n🔥 **Streak: {new_streak} days**"
            
            if streak_update.get("milestone_rewards"):
                response += " *(Milestone reward!)*"
            response += "\\n"
        
        # Current totals
        response += f"\\n📊 **Current Status:**\\n"
        response += f"• Level {new_totals.get('level', 1)}\\n"
        response += f"• {new_totals.get('total_xp', 0)} total XP\\n"
        response += f"• {new_totals.get('runes', 0)} Runes\\n"
        response += f"• {new_totals.get('streak', 0)}-day streak\\n"
        
        return response
    
    def _create_post_completion_keyboard(self) -> InlineKeyboardMarkup:
        """Create keyboard shown after quest completion"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 View Quests", callback_data="quests")],
            [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")]
        ])
    
    async def trigger_side_quest(self, message: types.Message):
        """Handle manual side quest trigger"""
        try:
            user_id = message.from_user.id
            user_data = await self.get_user_data(user_id)
            
            # Check if user already has an active side quest
            # This would check Notion for existing side quests
            has_active_side_quest = False  # Placeholder
            
            if has_active_side_quest:
                await message.answer(
                    "🌟 You already have an active side quest! Complete it first.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📜 View Quests", callback_data="quests")]
                    ])
                )
                return
            
            # Trigger side quest
            side_quest_data = await self.notion.trigger_side_quest(user_id, user_data)
            
            if side_quest_data:
                response = f"✨ **New Side Quest Available!**\\n\\n"
                response += f"🎯 **{side_quest_data.get('name', 'Mystery Quest')}**\\n"
                response += f"_{side_quest_data.get('description', 'No description')}_\\n\\n"
                response += f"💎 **Rewards:** {side_quest_data.get('xp_reward', 0)} XP, {side_quest_data.get('rune_reward', 0)} Runes\\n"
                response += f"⏱️ **Estimated Time:** {side_quest_data.get('estimated_time', 'Variable')}"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Complete Side Quest",
                        callback_data=f"complete_{side_quest_data.get('notion_id', 'SQ1')}"
                    )],
                    [InlineKeyboardButton(text="📜 View All Quests", callback_data="quests")]
                ])
                
                await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer(
                    "😔 No side quest available right now. Try again later!",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📜 View Quests", callback_data="quests")]
                    ])
                )
        
        except Exception as e:
            logger.error(f"Error triggering side quest: {e}")
            await message.answer("❌ Error creating side quest. Please try again.")
    
    async def trigger_side_quest_callback_handler(self, callback: CallbackQuery):
        """Handle side quest trigger from callback"""
        try:
            user_id = callback.from_user.id
            user_data = await self.get_user_data(user_id)
            
            side_quest_data = await self.notion.trigger_side_quest(user_id, user_data)
            
            if side_quest_data:
                response = f"✨ **New Side Quest!**\\n\\n"
                response += f"🎯 {side_quest_data.get('name', 'Mystery Quest')}\\n"
                response += f"💎 {side_quest_data.get('xp_reward', 0)} XP, {side_quest_data.get('rune_reward', 0)} Runes"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Complete",
                        callback_data=f"complete_{side_quest_data.get('notion_id', 'SQ1')}"
                    )],
                    [InlineKeyboardButton(text="📜 All Quests", callback_data="quests")]
                ])
                
                await callback.message.edit_text(
                    response,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await callback.answer("🌟 Side quest created!")
            else:
                await callback.answer("😔 No side quest available right now", show_alert=True)
        
        except Exception as e:
            logger.error(f"Error in side quest callback: {e}")
            await callback.answer("❌ Error creating side quest", show_alert=True)
    
    async def handle_quest_reroll(self, message: types.Message):
        """Handle quest reroll from command"""
        try:
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await message.answer(
                    "❌ Please specify a quest ID: `/reroll Q1`",
                    parse_mode="Markdown"
                )
                return
            
            quest_id = command_parts[1]
            user_id = message.from_user.id
            user_data = await self.get_user_data(user_id)
            
            # Find quest notion ID by quest_id (would query Notion)
            quest_notion_id = "placeholder"  # This needs actual implementation
            
            # Process reroll
            reroll_result = await self.notion.reroll_quest(quest_notion_id, user_id, user_data)
            
            if reroll_result.get("error"):
                await message.answer(f"❌ {reroll_result['error']}")
            else:
                response = self._format_reroll_response(reroll_result)
                await message.answer(response, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error handling quest reroll: {e}")
            await message.answer("❌ Error rerolling quest. Please try again.")
    
    async def reroll_quest_by_id(self, callback: CallbackQuery, notion_id: str):
        """Handle quest reroll from callback"""
        try:
            user_id = callback.from_user.id
            user_data = await self.get_user_data(user_id)
            
            reroll_result = await self.notion.reroll_quest(notion_id, user_id, user_data)
            
            if reroll_result.get("error"):
                await callback.answer(f"❌ {reroll_result['error']}", show_alert=True)
            else:
                response = self._format_reroll_response(reroll_result)
                
                await callback.message.edit_text(
                    response,
                    parse_mode="Markdown",
                    reply_markup=self._create_post_reroll_keyboard(notion_id)
                )
                await callback.answer("🔄 Quest rerolled!")
        
        except Exception as e:
            logger.error(f"Error rerolling quest by ID: {e}")
            await callback.answer("❌ Error rerolling quest", show_alert=True)
    
    def _format_reroll_response(self, reroll_result: dict) -> str:
        """Format quest reroll response"""
        new_quest = reroll_result.get("new_quest", {})
        cost = reroll_result.get("cost", 0)
        remaining_runes = reroll_result.get("remaining_runes", 0)
        
        response = f"🔄 **Quest Rerolled!**\\n\\n"
        response += f"🎯 **New Quest:** {new_quest.get('name', 'Unknown')}\\n"
        response += f"📝 _{new_quest.get('description', 'No description')}_\\n\\n"
        response += f"💎 **Rewards:** {new_quest.get('xp_reward', 0)} XP, {new_quest.get('rune_reward', 0)} Runes\\n"
        response += f"💰 **Cost:** -{cost} Runes\\n"
        response += f"💰 **Remaining:** {remaining_runes} Runes"
        
        return response
    
    def _create_post_reroll_keyboard(self, notion_id: str) -> InlineKeyboardMarkup:
        """Create keyboard after quest reroll"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Complete Quest",
                callback_data=f"complete_{notion_id}"
            )],
            [InlineKeyboardButton(text="📜 View All Quests", callback_data="quests")]
        ])
    
    async def complete_quest_by_quest_id(self, user_id: int, quest_id: str, user_data: dict) -> dict:
        """Complete quest by quest ID (helper method)"""
        # This would need to query Notion to find the quest by quest_id
        # and then complete it. For now, returning placeholder
        return {
            "error": f"Quest {quest_id} not found or already completed"
        }