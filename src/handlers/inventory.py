import logging
from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient
from src.models.item import Item
from src.utils.formatters import format_rarity

logger = logging.getLogger(__name__)

router = Router()

def register_inventory_handlers(dp):
    """Register inventory command handlers"""
    dp.include_router(router)

@router.message(Command("inventory"))
@router.callback_query(F.data == "inventory")
async def cmd_inventory(message_or_callback, state=None):
        """Display user's inventory"""
        if isinstance(message_or_callback, types.CallbackQuery):
            message = message_or_callback.message
            await message_or_callback.answer()
        else:
            message = message_or_callback

        notion_client: NotionClient = message.bot['notion_client']
        user_id = message.from_user.id

        try:
            items_data = await notion_client.get_inventory(user_id)
            if not items_data:
                await message.answer("🎒 **Your Inventory**\n\n📭 Your inventory is empty! Visit the /shop to get items.", parse_mode="Markdown")
                return

            item_groups = {}
            for item_data in items_data:
                item = Item.from_notion(item_data)
                if item.quantity > 0:
                    if item.type not in item_groups:
                        item_groups[item.type] = []
                    item_groups[item.type].append(item)

            if not item_groups:
                await message.answer("🎒 **Your Inventory**\n\n📭 Your inventory is empty! Visit the /shop to get items.", parse_mode="Markdown")
                return

            text = "🎒 **Your Inventory**\n\n"
            for item_type, items_list in item_groups.items():
                text += f"**{item_type.value}:**\n"
                for item in items_list:
                    text += f"  • {item.get_display_name()}"
                    if item.quantity > 1:
                        text += f" (x{item.quantity})"
                    text += "\n"
                text += "\n"

            keyboard = []
            if any(item.type == 'Consumable' for group in item_groups.values() for item in group):
                keyboard.append([InlineKeyboardButton(text="🧪 Use Item", callback_data="use_item_select")])
            keyboard.append([InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="dashboard")])

            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error loading inventory: {e}")
            await message.answer("❌ Error loading inventory. Please try again.")

@router.callback_query(F.data == "use_item_select")
async def select_item_to_use(callback_query: types.CallbackQuery):
        """Show consumable items to use"""
        notion_client: NotionClient = callback_query.bot['notion_client']
        user_id = callback_query.from_user.id

        try:
            items_data = await notion_client.get_inventory(user_id)
            consumables = [Item.from_notion(item) for item in items_data if Item.from_notion(item).type == 'Consumable' and Item.from_notion(item).quantity > 0]

            if not consumables:
                await callback_query.answer("❌ No consumable items to use.", show_alert=True)
                return

            keyboard = []
            for item in consumables:
                keyboard.append([InlineKeyboardButton(text=f"{item.name} (x{item.quantity})", callback_data=f"use_item_{item.item_id}")])
            keyboard.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="inventory")])

            await callback_query.message.edit_text("🧪 **Select an item to use:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error selecting item to use: {e}")
            await callback_query.answer("❌ Error loading items.", show_alert=True)

@router.callback_query(F.data.startswith("use_item_"))
async def use_item(callback_query: types.CallbackQuery):
        """Use the selected item"""
        item_id = callback_query.data.split('_')[-1]
        notion_client: NotionClient = callback_query.bot['dp']['notion_client']
        user_id = callback_query.from_user.id

        try:
            item_data = await notion_client.get_item(item_id)
            if not item_data:
                await callback_query.answer("❌ Item not found.", show_alert=True)
                return

            item = Item.from_notion(item_data)
            if item.quantity <= 0:
                await callback_query.answer("❌ You don't have this item anymore.", show_alert=True)
                return

            # Item effects
            effect_message = f"✅ Used {item.name}!"
            if item.name == "XP Potion":
                await notion_client.update_user_xp(user_id, 50)
                effect_message = "🧪 Used XP Potion! You gained +50 XP!"
            
            # Update quantity
            await notion_client.update_item_quantity(item_id, item.quantity - 1)

            await callback_query.answer(effect_message, show_alert=True)
            await cmd_inventory(callback_query) # Refresh inventory view

        except Exception as e:
            logger.error(f"Error using item: {e}")
            await callback_query.answer("❌ Error using item.", show_alert=True)