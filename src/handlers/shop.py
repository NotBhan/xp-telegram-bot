import logging
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.notion.notion_client import NotionClient
from src.models.item import ItemRarity
from src.utils.calculators import get_item_price

logger = logging.getLogger(__name__)

# In-memory shop items (for now)
SHOP_ITEMS = [
    {"name": "XP Potion", "rarity": ItemRarity.COMMON, "description": "Grants 50 XP.", "type": "Consumable", "effect": "+50 XP"},
    {"name": "Streak Shield", "rarity": ItemRarity.UNCOMMON, "description": "Protects your streak for 24h.", "type": "Consumable", "effect": "Streak protection"},
    {"name": "Rune Doubler", "rarity": ItemRarity.RARE, "description": "Doubles rune rewards for 24h.", "type": "Boost", "effect": "2x Runes"},
    {"name": "Energy Drink", "rarity": ItemRarity.RARE, "description": "Resets daily quest limit.", "type": "Consumable", "effect": "+1 Daily Quest"},
]

async def show_shop(message: types.Message, notion_client: NotionClient, edit_message: bool = False):
    shop_text = "🛒 **Welcome to the Item Shop!** 🛒\n\n"
    shop_text += "Here are the items available for purchase:\n\n"

    keyboard = []
    for item_data in SHOP_ITEMS:
        price = get_item_price(item_data["rarity"])
        shop_text += f"🔹 **{item_data['name']}** - {price} 💎\n"
        shop_text += f"   _{item_data['description']}_\n"
        keyboard.append([
            InlineKeyboardButton(
                text=f"Buy {item_data['name']} ({price} 💎)",
                callback_data=f"buy_{item_data['name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="dashboard")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    if edit_message:
        await message.edit_text(shop_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.answer(shop_text, reply_markup=reply_markup, parse_mode="Markdown")

def register_shop_handlers(dp: Dispatcher):
    """Register shop command handlers"""

    @dp.message(Command("shop"))
    async def cmd_shop_message(message: types.Message, state: FSMContext):
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_shop(message, notion_client)

    @dp.callback_query(F.data == "shop")
    async def cmd_shop_callback(callback_query: types.CallbackQuery, state: FSMContext):
        await state.clear()
        notion_client: NotionClient = dp.get('notion_client')
        await show_shop(callback_query.message, notion_client, edit_message=True)
        await callback_query.answer()

    @dp.callback_query(F.data.startswith('buy_'))
    async def cmd_buy_item(callback_query: types.CallbackQuery):
        """Handle item purchase"""
        item_name = callback_query.data.replace('buy_', '')
        user_id = callback_query.from_user.id
        
        notion_client: NotionClient = dp.get('notion_client')
        
        try:
            item_data = next((item for item in SHOP_ITEMS if item["name"] == item_name), None)
            if not item_data:
                await callback_query.answer("❌ Item not found in shop.", show_alert=True)
                return

            price = get_item_price(item_data["rarity"])

            user = await notion_client.get_user(user_id)
            if not user:
                await callback_query.answer("❌ Profile not found. Use /start.", show_alert=True)
                return
            
            runes = user["properties"]["Runes"]["number"] or 0

            if runes < price:
                await callback_query.answer(f"❌ Not enough runes! You need {price} 💎.", show_alert=True)
                return

            await notion_client.update_user_runes(user_id, runes - price)
            await notion_client.add_item_to_inventory(user_id, {**item_data, "price": price})

            await callback_query.answer(f"✅ Purchased {item_name} for {price} 💎!", show_alert=True)
            
            await show_shop(callback_query.message, notion_client, edit_message=True)

        except Exception as e:
            logger.error(f"Error buying item: {e}")
            await callback_query.answer("❌ Error processing purchase.", show_alert=True)