import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Dispatcher
from src.notion.notion_client import NotionClient
from src.gamification import GamificationEngine
from src.quest_system import QuestSystem
from src.enhanced_notion_client import EnhancedNotionClient

logger = logging.getLogger(__name__)

async def show_dashboard(user_id: int, edit_message=None, message=None):
    notion = NotionClient()
    
    try:
        user_stats = await notion.get_user_stats(user_id)
        
        if not user_stats:
            text = "❌ **Error Loading Dashboard**\n\n"
            text += "Could not load your profile. Please try /start first."
        else:
            # Get comprehensive gamification data
            current_level = user_stats['level']
            current_xp = user_stats['xp']
            current_runes = user_stats['runes']
            current_streak = user_stats['streak']
            current_title = user_stats['title']
            
            # Calculate XP progress using gamification engine
            level, xp_in_level, xp_needed = GamificationEngine.calculate_level_from_xp(current_xp)
            
            # Get active buffs and debuffs
            active_buffs = await notion.get_active_buffs(user_id)
            active_debuffs = await notion.get_active_debuffs(user_id)
            
            # Build enhanced dashboard with quest integration
            text = f"🎮 **Your Adventure Dashboard** 🎮\n\n"
            
            # Basic stats section
            text += f"🏅 Level {current_level} — {xp_in_level}/{xp_in_level + xp_needed} XP\n"
            text += f"🔥 Streak: {current_streak} days\n"
            text += f"💰 Runes: {current_runes}\n\n"
            
            # Quest section - Get active quests and display them
            try:
                # This would normally query for today's active quests
                # For now, showing placeholder quest format
                text += await get_dashboard_quest_display(user_id, current_level)
                text += "\n"
            except Exception as e:
                logger.warning(f"Could not load quest display: {e}")
                text += "📜 Quests: Use /quests to view current challenges\n\n"
            
            # Status effects section
            if active_debuffs:
                debuff_text = ", ".join([f"{d.name} ({d.days_remaining()} days left)" for d in active_debuffs if d.is_active()])
                if debuff_text:
                    text += f"☠️ Debuffs: {debuff_text}\n"
            
            if active_buffs:
                buff_text = ", ".join([f"{b.name}" for b in active_buffs if b.is_active()])
                if buff_text:
                    text += f"🌟 Buffs: {buff_text}\n"
            
            text += f"🎖️ Title: {current_title}\n"
            
            # Add visual XP progress bar
            xp_progress_percent = int((xp_in_level / (xp_in_level + xp_needed)) * 100) if (xp_in_level + xp_needed) > 0 else 0
            progress_bar_length = 10
            filled_bars = int((xp_progress_percent / 100) * progress_bar_length)
            progress_bar = "🟩" * filled_bars + "⬜" * (progress_bar_length - filled_bars)
            
            text += f"\n📊 **Progress:** {progress_bar} {xp_progress_percent}%\n"
            
            # Show next title progress
            next_title_levels = [25, 50, 75, 100]
            next_title_level = None
            for title_level in next_title_levels:
                if current_level < title_level:
                    next_title_level = title_level
                    break
            
            if next_title_level:
                next_title = GamificationEngine.get_title_for_level(next_title_level)
                levels_needed = next_title_level - current_level
                text += f"🎯 **Next Title:** {next_title.emoji} {next_title.name} (in {levels_needed} levels)\n"
            
            # Show recent trophies (last 3)
            user_trophies = await notion.get_user_trophies(user_id)
            if user_trophies:
                text += f"\n🏆 **Recent Trophies** ({len(user_trophies)} total):\n"
                for trophy in user_trophies[-3:]:  # Show last 3
                    text += f"   • {trophy.name}\n"
                if len(user_trophies) > 3:
                    text += f"   • ... and {len(user_trophies) - 3} more in inventory\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 Quests", callback_data="quests"),
                InlineKeyboardButton(text="🛒 Shop", callback_data="shop")
            ],
            [
                InlineKeyboardButton(text="🎒 Inventory", callback_data="inventory"),
                InlineKeyboardButton(text="📊 Analytics", callback_data="analytics")
            ],
            [
                InlineKeyboardButton(text="🏆 Trophies", callback_data="trophies"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="dashboard")
            ]
        ])

        if edit_message:
            try:
                await edit_message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            except:
                await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error in show_dashboard: {e}")
        text = "❌ **Error Loading Dashboard**\n\n"
        text += "There was an issue loading your dashboard. Please try again."
        
        if edit_message:
            try:
                await edit_message.edit_text(text)
            except:
                await message.answer(text)
        else:
            await message.answer(text)
    finally:
        await notion.close()

async def cmd_dashboard_message(message):
    await show_dashboard(message.from_user.id, message=message)

async def cmd_dashboard_callback(callback_query):
    await show_dashboard(callback_query.from_user.id, edit_message=callback_query.message, message=callback_query.message)
    await callback_query.answer()

async def show_trophies(user_id: int, edit_message=None, message=None):
    """Show user's trophy collection"""
    notion = NotionClient()
    
    try:
        user_trophies = await notion.get_user_trophies(user_id)
        
        if not user_trophies:
            text = "🏆 **Your Trophy Collection** 🏆\n\n"
            text += "📭 No trophies yet! Complete quests and reach milestones to earn trophies.\n\n"
            text += "🎯 **How to earn trophies:**\n"
            text += "• Complete your first quest\n"
            text += "• Maintain a 7-day streak\n"
            text += "• Reach level milestones\n"
            text += "• Complete 100 quests\n"
            text += "• Accumulate 1000 runes\n"
        else:
            text = f"🏆 **Your Trophy Collection** 🏆\n\n"
            text += f"🎖️ **Total Trophies:** {len(user_trophies)}\n\n"
            
            for trophy in user_trophies:
                text += f"🏅 **{trophy.name}**\n"
                text += f"   _{trophy.description}_\n"
                if trophy.earned_date:
                    earned_date = trophy.earned_date.strftime("%Y-%m-%d")
                    text += f"   📅 Earned: {earned_date}\n"
                text += "\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="dashboard")]
        ])
        
        if edit_message:
            try:
                await edit_message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            except:
                await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error showing trophies: {e}")
        await message.answer("❌ Error loading trophies. Please try again.")
    finally:
        await notion.close()

async def cmd_trophies_callback(callback_query):
    """Handle trophy viewing callback"""
    await show_trophies(callback_query.from_user.id, edit_message=callback_query.message, message=callback_query.message)
    await callback_query.answer()

def register_dashboard_handlers(dp: Dispatcher):
    dp.message.register(cmd_dashboard_message, lambda m: m.text == "/dashboard")
    dp.callback_query.register(cmd_dashboard_callback, lambda c: c.data == "dashboard")
    dp.callback_query.register(cmd_trophies_callback, lambda c: c.data == "trophies")

async def get_dashboard_quest_display(user_id: int, user_level: int) -> str:
    """
    Get quest display for dashboard according to specification:
    
    📜 Quests:
    [ ] Q1 — Make 2 loops (Easy) — 15 XP, 12 Runes
    [ ] Q2 — Post reel on IG (Medium) — 35 XP, 20 Runes
    [ ] Q3 — Finish one track section (Hard) — 75 XP, 35 Runes

    ✨ Side Quest:
    [ ] SQ1 — Take a 20 min nature walk (Rare) — 50 XP, 50 Runes
    """
    try:
        # This would normally query Notion for today's active quests
        # For now, generating sample quests based on user level
        sample_quests = QuestSystem.generate_daily_quests(user_level)
        
        # Check if side quest should be available
        from src.side_quest_manager import SideQuestManager
        should_have_side_quest = SideQuestManager.should_trigger_side_quest(
            user_level=user_level,
            current_streak=0,  # Would get from user data
            last_side_quest_date=None
        )
        
        sample_side_quest = None
        if should_have_side_quest:
            sample_side_quest = SideQuestManager.generate_side_quest(user_level)
        
        # Format according to specification
        quest_display = QuestSystem.format_quest_dashboard(sample_quests)
        
        if sample_side_quest:
            quest_display += f"\n\n✨ Side Quest:\n"
            quest_display += f"[ ] {sample_side_quest.quest_id} — {sample_side_quest.name} "
            quest_display += f"({sample_side_quest.difficulty.value}) — {sample_side_quest.xp_reward} XP, "
            quest_display += f"{sample_side_quest.rune_reward} Runes"
        
        return quest_display
        
    except Exception as e:
        logger.error(f"Error generating dashboard quest display: {e}")
        return "📜 Quests: Use /quests to view current challenges"