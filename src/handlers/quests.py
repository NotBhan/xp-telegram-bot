import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient

logger = logging.getLogger(__name__)

async def show_quests(message: types.Message, user_id: int, notion_client: NotionClient, edit_message: bool = False):
    """Display available quests for the user with improved error handling."""
    try:
        user = await notion_client.get_user(user_id)
        if not user:
            await message.answer("❌ Profile not found. Please use /start to register first.")
            return

        first_name = message.from_user.first_name or "Adventurer"

        # Try to get quests, with fallback to creation
        quests = []
        try:
            quests = await notion_client.get_quests(user_id)
            logger.info(f"Found {len(quests)} quests for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not fetch quests: {e}")
            # Quests will be created below

        # If no quests exist, create default ones
        if not quests:
            logger.info(f"Creating default quests for user {user_id}")
            created_quests = await notion_client.create_default_quests(user_id)
            if created_quests:
                quests = await notion_client.get_quests(user_id)
                logger.info(f"Successfully created {len(created_quests)} default quests")
            else:
                logger.error("Failed to create default quests")

        if not quests:
            # Fallback message with manual quest suggestions
            quest_text = f"🎯 **{first_name}'s Daily Quests** 🎯\n\n"
            quest_text += "📭 No quests available yet. Here are some suggestions:\n\n"
            quest_text += "1. 🌅 **Morning Routine** - Complete your morning routine\n"
            quest_text += "2. 💪 **Exercise 30min** - Do 30 minutes of exercise\n"
            quest_text += "3. 📖 **Read 20 pages** - Read 20 pages of a book\n"
            quest_text += "4. 💧 **Stay Hydrated** - Drink 8 glasses of water\n\n"
            quest_text += "💡 Complete these activities and check back later!"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")],
                [InlineKeyboardButton(text="🔄 Try Again", callback_data="quests")]
            ])
            
            if edit_message:
                try:
                    await message.edit_text(quest_text, parse_mode="Markdown", reply_markup=keyboard)
                except Exception:
                    await message.answer(quest_text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer(quest_text, parse_mode="Markdown", reply_markup=keyboard)
            return

        # Display available quests
        quest_text = f"🎯 **{first_name}'s Daily Quests** 🎯\n\n"
        buttons = []
        active_quests = []

        for quest in quests:
            try:
                # Safely extract quest properties
                quest_name = "Unknown Quest"
                if quest["properties"].get("Quest Name") and quest["properties"]["Quest Name"]["title"]:
                    quest_name = quest["properties"]["Quest Name"]["title"][0]["text"]["content"]
                
                quest_desc = ""
                if quest["properties"].get("Description") and quest["properties"]["Description"]["rich_text"]:
                    quest_desc = quest["properties"]["Description"]["rich_text"][0]["text"]["content"]
                
                xp_reward = 0
                if quest["properties"].get("XP Reward"):
                    xp_reward = quest["properties"]["XP Reward"].get("number", 0)
                
                rune_reward = 0
                if quest["properties"].get("Rune Reward"):
                    rune_reward = quest["properties"]["Rune Reward"].get("number", 0)
                
                status = "Active"
                if quest["properties"].get("Status") and quest["properties"]["Status"]["select"]:
                    status = quest["properties"]["Status"]["select"]["name"]
                
                if status == "Active":
                    active_quests.append(quest)
                    quest_text += f'**{len(active_quests)}. {quest_name}**\n'
                    if quest_desc:
                        quest_text += f'_{quest_desc}_\n'
                    quest_text += f'💎 **+{xp_reward} XP** | 💰 **+{rune_reward} Runes**\n\n'
                    
                    buttons.append([InlineKeyboardButton(
                        f"✅ Complete {len(active_quests)}", 
                        callback_data=f"complete_{quest['id']}"
                    )])
                    
            except Exception as e:
                logger.error(f"Error processing quest: {e}")
                continue

        if not active_quests:
            quest_text += "🎉 All quests completed! New quests will appear tomorrow.\n\n"
            quest_text += "💡 Check your dashboard to see your progress!"
        else:
            quest_text += f"📜 Complete {len(active_quests)} quest(s) to earn rewards!"
        
        keyboard_buttons = buttons + [
            [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="quests")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        if edit_message:
            try:
                await message.edit_text(quest_text, parse_mode="Markdown", reply_markup=keyboard)
            except Exception:
                await message.answer(quest_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(quest_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in show_quests: {e}")
        error_text = "❌ Error loading quests. Please try again later.\n\n"
        error_text += "💡 If this persists, try /start to refresh your profile."
        await message.answer(error_text)

def register_quest_handlers(dp: Dispatcher, notion: NotionClient):
    """Register quest-related handlers"""
    
    @dp.message(Command("quests"))
    async def show_quests_command(message: types.Message):
        """Show all active quests for the user"""
        user_id = message.from_user.id
        
        try:
            # Try to get existing quests
            quests = await notion.get_quests(user_id)
            
            if not quests:
                # Create comprehensive quests if none exist
                await message.answer("🎯 Creating your personalized quest list...")
                quests = await notion.create_comprehensive_quests(user_id)
                
                if not quests:
                    await message.answer(
                        "❌ Could not create quests. Please try again later or contact support.",
                        reply_markup=get_main_keyboard()
                    )
                    return
            
            # Filter active quests
            active_quests = []
            for quest in quests:
                props = quest.get("properties", {})
                status = props.get("Status", props.get("status", {})).get("select", {})
                if status and status.get("name", "").lower() in ["active", "not started", "in progress"]:
                    active_quests.append(quest)
            
            if not active_quests:
                # Create new daily quests
                active_quests = await notion.create_comprehensive_quests(user_id)
                if not active_quests:
                    await message.answer(
                        "🎮 No active quests found. I've created some fresh ones for you!",
                        reply_markup=get_main_keyboard()
                    )
                    return
            
            # Build comprehensive quest display
            response = "🎯 **Your Daily Quests**\n\n"
            
            # Group quests by category
            categories = {}
            for quest in active_quests:
                props = quest.get("properties", {})
                
                # Extract quest details with robust handling
                name = props.get("Name", props.get("name", {})).get("title", [{}])[0].get("plain_text", "Unknown Quest")
                desc = props.get("Description", props.get("description", {})).get("rich_text", [{}])[0].get("plain_text", "No description")
                category = props.get("Category", props.get("category", {})).get("select", {}).get("name", "General")
                xp = props.get("XP Reward", props.get("xp_reward", {})).get("number", 0)
                runes = props.get("Rune Reward", props.get("rune_reward", {})).get("number", 0)
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append({
                    "id": quest.get("id", ""),
                    "name": name,
                    "description": desc,
                    "xp": xp,
                    "runes": runes
                })
            
            # Display quests by category
            for category, quest_list in categories.items():
                response += f"**{category}**\n"
                for quest in quest_list:
                    response += f"• **{quest['name']}** - {quest['description']}\n"
                    response += f"  💎 {quest['runes']} runes | ⚡ {quest['xp']} XP\n\n"
            
            response += "\n✅ Use /complete <quest_id> to complete a quest!"
            
            await message.answer(response, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error showing quests: {e}")
            await message.answer(
                "❌ Error loading quests. Please try again in a moment.",
                reply_markup=get_main_keyboard()
            )

    @dp.message(Command("refresh"))
    async def refresh_quests(message: types.Message):
        """Refresh daily quests with new ones"""
        user_id = message.from_user.id
        
        try:
            # Get user level for scaling
            user_stats = await notion.get_user_stats(user_id)
            level = user_stats.get("level", 1)
            
            # Archive existing active quests
            quests = await notion.get_quests(user_id)
            for quest in quests:
                props = quest.get("properties", {})
                status = props.get("Status", props.get("status", {})).get("select", {})
                if status and status.get("name", "").lower() in ["active", "not started", "in progress"]:
                    await notion.update_quest_status(quest.get("id"), "archived")
            
            # Create fresh daily quests
            new_quests = await notion.create_comprehensive_quests(user_id, level)
            
            if new_quests:
                await message.answer(
                    f"🔄 **Daily quests refreshed!**\n\n"
                    f"✨ {len(new_quests)} new quests created for your level {level} journey!\n"
                    f"🎯 Check them out with /quests",
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    "❌ Could not refresh quests. Please try again later.",
                    reply_markup=get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error refreshing quests: {e}")
            await message.answer(
                "❌ Error refreshing quests. Please try again.",
                reply_markup=get_main_keyboard()
            )

    @dp.message(Command("complete"))
    async def complete_quest_command(message: types.Message):
        """Complete a quest by ID with enhanced feedback"""
        user_id = message.from_user.id
        
        try:
            # Parse quest ID from message
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.answer(
                    "❌ Please provide a quest ID.\n\n"
                    "Usage: /complete <quest_id>\n"
                    "Example: /complete abc123def456",
                    reply_markup=get_main_keyboard()
                )
                return
            
            quest_id = parts[1].strip()
            
            # Verify quest belongs to user
            quests = await notion.get_quests(user_id)
            user_quest = None
            
            for quest in quests:
                if quest.get("id") == quest_id:
                    user_quest = quest
                    break
            
            if not user_quest:
                await message.answer(
                    "❌ Quest not found or doesn't belong to you.\n\n"
                    "Use /quests to see your available quests.",
                    reply_markup=get_main_keyboard()
                )
                return
            
            # Complete the quest
            result = await notion.complete_quest(quest_id)
            
            if result:
                # Get updated user stats
                user_stats = await notion.get_user_stats(user_id)
                
                response = (
                    f"🎉 **Quest Completed!**\n\n"
                    f"✅ **{result['name']}** completed successfully!\n\n"
                    f"🏆 **Rewards Earned:**\n"
                    f"   💎 {result['runes']} runes\n"
                    f"   ⚡ {result['xp']} XP\n\n"
                    f"📊 **Your Stats:**\n"
                    f"   Level: {user_stats['level']}\n"
                    f"   XP: {user_stats['xp']}/{user_stats['next_level_xp']}\n"
                    f"   Runes: {user_stats['runes']}\n"
                    f"   Streak: {user_stats['streak']} days\n"
                    f"   Title: {user_stats['title']}\n"
                )
                
                # Check for level up
                if user_stats.get('level_up', False):
                    response += f"\n🎊 **LEVEL UP!** You are now level {user_stats['level']}!"
                    if user_stats.get('new_title'):
                        response += f"\n🏅 New title unlocked: {user_stats['new_title']}"
                
                # Check for streak milestone
                if user_stats['streak'] > 0 and user_stats['streak'] % 7 == 0:
                    response += f"\n🔥 **STREAK MILESTONE!** {user_stats['streak']} days!"
                
                await message.answer(response, reply_markup=get_main_keyboard(), parse_mode="Markdown")
                
            else:
                await message.answer(
                    "❌ Could not complete quest. Please try again.",
                    reply_markup=get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error completing quest: {e}")
            await message.answer(
                "❌ Error completing quest. Please try again.",
                reply_markup=get_main_keyboard()
            )

    @dp.callback_query(F.data == "quests")
    async def show_quests_callback(callback_query: types.CallbackQuery):
        """Show quests when button is clicked"""
        await callback_query.answer()
        await show_quests_command(callback_query.message)

    @dp.callback_query(F.data.startswith("complete_"))
    async def complete_quest_callback(callback_query: types.CallbackQuery):
        """Complete a quest when button is clicked"""
        await callback_query.answer()
        
        quest_id = callback_query.data.replace("complete_", "")
        user_id = callback_query.from_user.id
        
        try:
            # Complete the quest
            result = await notion.complete_quest(quest_id)
            
            if result:
                # Get updated user stats
                user_stats = await notion.get_user_stats(user_id)
                
                # Check for level up and other bonuses
                level_up_info = ""
                if result.get("level_up_occurred"):
                    level_up_info = f"\n\n🎆 **LEVEL UP!** You are now level {user_stats['level']}!"
                    if result.get("new_title"):
                        level_up_info += f"\n🏅 New title unlocked: {result['new_title']}"
                
                # Check for streak bonuses
                streak_info = ""
                if user_stats['streak'] > 0 and user_stats['streak'] % 7 == 0:
                    streak_info = f"\n🔥 **STREAK MILESTONE!** {user_stats['streak']} days!"
                
                response = (
                    f"🎉 Quest Completed!\n\n"
                    f"✅ **{result['name']}** completed!\n"
                    f"🏆 +{result['runes']} runes | +{result['xp']} XP\n\n"
                    f"📊 Level: {user_stats['level']} | Streak: {user_stats['streak']} days"
                    f"{level_up_info}{streak_info}"
                )
                
                await callback_query.message.answer(response, reply_markup=get_main_keyboard())
                
                # Check if side quest should be triggered
                side_quest = await notion.create_side_quest_if_needed(user_id)
                if side_quest:
                    side_quest_text = (
                        f"🌟 **Bonus Side Quest Unlocked!**\n\n"
                        f"🎯 **{side_quest['name']}**\n"
                        f"_{side_quest['description']}_\n\n"
                        f"💪 Reward: +{side_quest['xp_reward']} XP | +{side_quest['rune_reward']} runes\n"
                        f"⏱️ Estimated time: {side_quest.get('estimated_time', 'Unknown')}"
                    )
                    await callback_query.message.answer(side_quest_text, reply_markup=get_main_keyboard())
                    
            else:
                await callback_query.answer("❌ Could not complete quest", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error completing quest: {e}")
            await callback_query.answer("❌ An error occurred while completing the quest.", show_alert=True)
    
    @dp.message(Command("analytics"))
    async def quest_analytics_command(message: types.Message):
        """Show quest completion analytics"""
        user_id = message.from_user.id
        
        try:
            analytics = await notion.get_quest_analytics(user_id)
            
            if "error" in analytics:
                await message.answer(f"❌ {analytics['error']}", reply_markup=get_main_keyboard())
                return
            
            response = "📊 **Your Quest Analytics** (Last 30 days)\n\n"
            response += f"🎯 **Overall Performance:**\n"
            response += f"   • Total Quests: {analytics['total_quests']}\n"
            response += f"   • Completed: {analytics['completed_quests']}\n"
            response += f"   • Success Rate: {analytics['completion_rate']:.1%}\n\n"
            
            # Category breakdown
            if analytics.get('category_breakdown'):
                response += "📊 **Category Performance:**\n"
                for category, stats in analytics['category_breakdown'].items():
                    if stats['total'] > 0:
                        rate = stats['completed'] / stats['total']
                        response += f"   • {category}: {rate:.1%} ({stats['completed']}/{stats['total']})\n"
                response += "\n"
            
            # Difficulty breakdown
            if analytics.get('difficulty_breakdown'):
                response += "⚔️ **Difficulty Performance:**\n"
                for difficulty, stats in analytics['difficulty_breakdown'].items():
                    if stats['total'] > 0:
                        rate = stats['completed'] / stats['total']
                        response += f"   • {difficulty}: {rate:.1%} ({stats['completed']}/{stats['total']})\n"
                response += "\n"
            
            # Recommendations
            if analytics.get('recommendations'):
                response += "💡 **Recommendations:**\n"
                for rec in analytics['recommendations'][:3]:  # Limit to 3 recommendations
                    response += f"   • {rec}\n"
            
            await message.answer(response, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error getting quest analytics: {e}")
            await message.answer(
                "❌ Error loading analytics. Please try again.",
                reply_markup=get_main_keyboard()
            )
    
    @dp.message(Command("adaptive"))
    async def create_adaptive_quests_command(message: types.Message):
        """Create adaptive quests based on user history"""
        user_id = message.from_user.id
        
        try:
            # Get user level
            user_stats = await notion.get_user_stats(user_id)
            level = user_stats.get("level", 1)
            
            # Archive existing active quests
            active_quests = await notion.get_quests(user_id)
            for quest in active_quests:
                props = quest.get("properties", {})
                status = props.get("Status", props.get("status", {})).get("select", {})
                if status and status.get("name", "").lower() in ["active", "not started", "in progress"]:
                    await notion.update_quest_status(quest.get("id"), "archived")
            
            # Create adaptive quests
            new_quests = await notion.create_adaptive_quests(user_id, level)
            
            if new_quests:
                response = (
                    f"🤖 **Adaptive Quests Created!**\n\n"
                    f"🎓 Based on your completion history, I've created {len(new_quests)} "
                    f"personalized quests for your level {level} journey!\n\n"
                    f"🎯 These quests are tailored to your strengths and areas for improvement.\n"
                    f"🔄 Check them out with /quests"
                )
            else:
                response = "❌ Could not create adaptive quests. Please try again later."
            
            await message.answer(response, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error creating adaptive quests: {e}")
            await message.answer(
                "❌ Error creating adaptive quests. Please try again.",
                reply_markup=get_main_keyboard()
            )

def get_main_keyboard():
    """Get the main navigation keyboard"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton(text="🎯 Quests", callback_data="quests")
        ],
        [
            InlineKeyboardButton(text="🛒 Shop", callback_data="shop"),
            InlineKeyboardButton(text="🎒 Inventory", callback_data="inventory")
        ]
    ])