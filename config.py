import os
from dotenv import load_dotenv

load_dotenv()

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
XP_DB_ID = os.getenv("NOTION_XP_DB")
QUEST_DB_ID = os.getenv("NOTION_QUEST_DB")
INVENTORY_DB_ID = os.getenv("NOTION_INVENTORY_DB")
DEBUFF_DB_ID = os.getenv("NOTION_DEBUFF_DB")

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# XP Scaling
def xp_for_level(level):
    return int(100 + (level - 1) * 25)

# XP Rewards
def xp_reward(difficulty, level):
    match difficulty:
        case "Easy":
            return round(5 * (1 + 0.1 * level))
        case "Medium":
            return round(10 * (1 + 0.15 * level))
        case "Hard":
            return round(15 * (1 + 0.2 * level))
        case _:
            return 0

# Runes earned
def rune_reward(difficulty):
    return {
        "Easy": 10,
        "Medium": 15,
        "Hard": 20
    }.get(difficulty, 5)
