from config import xp_for_level

def calculate_level(xp):
    level = 1
    total_xp = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
    return level, xp

def create_dashboard(level, xp, runes, streak, buffs, debuffs):
    bar_length = 20
    filled = int((xp / xp_for_level(level)) * bar_length)
    bar = "🟩" * filled + "⬜️" * (bar_length - filled)

    return (
        f"🎮 **Dashboard**\n\n"
        f"🏅 Level: {level}\n"
        f"📊 XP: {xp}/{xp_for_level(level)}\n"
        f"{bar}\n"
        f"🔥 Streak: {streak} days\n"
        f"💎 Runes: {runes}\n"
        f"💫 Buffs: {', '.join(buffs) or 'None'}\n"
        f"☠️ Debuffs: {', '.join(debuffs) or 'None'}"
    )
