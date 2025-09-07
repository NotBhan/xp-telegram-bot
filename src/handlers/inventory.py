import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient
from src.models.item import Item
from src.utils.formatters import format_rarity

logger = logging.getLogger(__name__)

async def show_inventory(message: types.Message, user_id: int, notion_client: NotionClient, edit_message: bool = False):
    """Display user's inventory with improved error handling"""
    
    try:
        items_data = await notion_client.get_inventory(user_id)
        if not items_data:
            inventory_text = "🎒 **Your Inventory**\n\n📭 Your inventory is empty! Visit the /shop to get items."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Shop", callback_data="shop")],
                [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")]
            ])
            
            if edit_message:
                await message.edit_text(inventory_text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.answer(inventory_text, reply_markup=keyboard, parse_mode="Markdown")
            return

        item_groups = {}
        for item_data in items_data:
            item = Item.from_notion(item_data)
            if item.quantity > 0:
                if item.type not in item_groups:
                    item_groups[item.type] = []
                item_groups[item.type].append(item)

        if not item_groups:
            inventory_text = "🎒 **Your Inventory**\n\n📭 Your inventory is empty! Visit the /shop to get items."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Shop", callback_data="shop")],
                [InlineKeyboardButton(text="📊 Dashboard", callback_data="dashboard")]
            ])
            
            if edit_message:
                await message.edit_text(inventory_text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.answer(inventory_text, reply_markup=keyboard, parse_mode="Markdown")
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

        if edit_message:
            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error loading inventory: {e}")
        await message.answer("❌ Error loading inventory. Please try again.")

async def select_item_to_use(message: types.Message, user_id: int, notion_client: NotionClient):
    """Show consumable items to use"""
    try:
        items_data = await notion_client.get_inventory(user_id)
        consumables = [Item.from_notion(item) for item in items_data if Item.from_notion(item).type == 'Consumable' and Item.from_notion(item).quantity > 0]

        if not consumables:
            await message.answer("❌ No consumable items to use.")
            return

        keyboard = []
        for item in consumables:
            keyboard.append([InlineKeyboardButton(text=f"{item.name} (x{item.quantity})", callback_data=f"use_item_{item.item_id}")])
        keyboard.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="inventory")])

        await message.edit_text("🧪 **Select an item to use:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error selecting item to use: {e}")
        await message.answer("❌ Error loading items.")

async def use_selected_item(message: types.Message, user_id: int, item_id: str, notion_client: NotionClient):
    """Use the selected item"""
    try:
        item_data = await notion_client.get_item(item_id)
        if not item_data:
            await message.answer("❌ Item not found.")
            return

        item = Item.from_notion(item_data)
        if item.quantity <= 0:
            await message.answer("❌ You don't have this item anymore.")
            return

        # Item effects
        effect_message = f"✅ Used {item.name}!"
        if item.name == "XP Potion":
            await notion_client.update_user_xp(user_id, 50)
            effect_message = "🧪 Used XP Potion! You gained +50 XP!"
        
        # Update quantity
        await notion_client.update_item_quantity(item_id, item.quantity - 1)

        await message.answer(effect_message)
        await show_inventory(message, notion_client)

    except Exception as e:
        logger.error(f"Error using item: {e}")
        await message.answer("❌ Error using item.")

def register_inventory_handlers(dp: Dispatcher):
    """Register inventory command handlers"""

    @dp.message(Command("inventory"))
    async def cmd_inventory_message(message: types.Message, state: FSMContext):
        """Handle /inventory command"""
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_inventory(message, message.from_user.id, notion_client)

    @dp.callback_query(F.data == "inventory")
    async def cmd_inventory_callback(callback_query: types.CallbackQuery, state: FSMContext):
        """Display user's inventory via callback"""
        await state.clear()
        await callback_query.answer()
        notion_client: NotionClient = dp.get('notion_client')
        await show_inventory(callback_query.message, callback_query.from_user.id, notion_client, edit_message=True)

    @dp.callback_query(F.data == "use_item_select")
    async def cmd_use_item_select(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle use item selection"""
        await state.clear()
        await callback_query.answer()
        notion_client: NotionClient = dp.get('notion_client')
        user_id = callback_query.from_user.id
        await select_item_to_use(callback_query.message, user_id, notion_client)

    @dp.callback_query(F.data.startswith("use_item_"))
    async def cmd_use_item(callback_query: types.CallbackQuery, state: FSMContext):
        """Handle item usage"""
        await state.clear()
        item_id = callback_query.data.split('_')[-1]
        user_id = callback_query.from_user.id
        notion_client: NotionClient = dp.get('notion_client')
        await use_selected_item(callback_query.message, user_id, item_id, notion_client)
        await callback_query.answer()