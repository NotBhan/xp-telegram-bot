"""
Formatting utilities for display purposes
"""

def format_xp_bar(current_xp, level):
    """
    Create a visual progress bar for XP
    
    Args:
        current_xp (int): Current XP amount
        level (int): Current level
    
    Returns:
        str: Formatted progress bar string
    """
    # Calculate XP needed for current level and next level
    xp_for_current = (level - 1) ** 2 * 100 if level > 1 else 0
    xp_for_next = level ** 2 * 100
    
    # XP in current level
    xp_in_level = current_xp - xp_for_current
    xp_needed = xp_for_next - xp_for_current
    
    # Calculate progress percentage
    progress = min(int((xp_in_level / xp_needed) * 100), 100) if xp_needed > 0 else 100
    
    # Create progress bar
    filled = int(progress / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    return f"[{bar}] {progress}%"

def format_rarity(rarity):
    """
    Format rarity with emoji
    
    Args:
        rarity (str): Rarity level
    
    Returns:
        str: Formatted rarity string with emoji
    """
    rarity_map = {
        "common": "⚪ Common",
        "uncommon": "🟢 Uncommon", 
        "rare": "🔵 Rare",
        "epic": "🟣 Epic",
        "legendary": "🟠 Legendary"
    }
    
    return rarity_map.get(rarity.lower(), f"⚪ {rarity}")

def format_time_ago(timestamp):
    """
    Format timestamp as relative time
    
    Args:
        timestamp (datetime): Timestamp to format
    
    Returns:
        str: Human-readable relative time
    """
    from datetime import datetime
    
    if not timestamp:
        return "Never"
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def format_number(number):
    """
    Format large numbers with commas
    
    Args:
        number (int): Number to format
    
    Returns:
        str: Formatted number string
    """
    return f"{number:,}"