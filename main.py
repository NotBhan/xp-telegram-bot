from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, xp_reward, rune_reward
from notion import get_user_entry, update_xp, update_level, log_quest
from utils import calculate_level, create_dashboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 Welcome to your XP Journey! Use /checkin to begin your day.")

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_entry = get_user_entry(user_id)
    
    if not user_entry:
        await update.message.reply_text("You're not registered in Notion yet.")
        return
    
    page_id = user_entry["id"]
    props = user_entry["properties"]
    level = props["Level"]["number"]
    xp = props["XP"]["number"]

    reward = xp_reward("Medium", level)
    xp += reward
    new_level, remaining = calculate_level(xp)

    update_xp(page_id, remaining)
    if new_level > level:
        update_level(page_id, new_level)

    runes = rune_reward("Medium")
    log_quest(page_id, "Daily Check-in", "Medium", reward, runes)

    dash = create_dashboard(new_level, remaining, runes, 5, [], [])
    await update.message.reply_text(dash, parse_mode="Markdown")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("checkin", checkin))

if __name__ == "__main__":
    app.run_polling()
