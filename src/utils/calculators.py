"""
Calculation utilities for game mechanics
"""

def calculate_level_from_xp(xp):
    """
    Calculate level based on XP using quadratic progression
    
    Args:
        xp (int): Current XP amount
    
    Returns:
        int: Calculated level
    """
    if xp < 0:
        return 1
    
    level = 1
    while xp >= level ** 2 * 100:
        xp -= level ** 2 * 100
        level += 1
    
    return level

def calculate_xp_for_level(level):
    """
    Calculate total XP needed for a given level
    
    Args:
        level (int): Target level
    
    Returns:
        int: Total XP needed
    """
    if level <= 1:
        return 0
    
    total_xp = 0
    for l in range(1, level):
        total_xp += l ** 2 * 100
    
    return total_xp

def calculate_streak_bonus(streak_days):
    """
    Calculate bonus XP multiplier based on streak
    
    Args:
        streak_days (int): Current streak in days
    
    Returns:
        float: XP multiplier
    """
    if streak_days < 3:
        return 1.0
    elif streak_days < 7:
        return 1.1
    elif streak_days < 14:
        return 1.2
    elif streak_days < 30:
        return 1.5
    else:
        return 2.0

def calculate_title_from_level(level):
    """
    Calculate user title based on level
    
    Args:
        level (int): Current level
    
    Returns:
        str: User title
    """
    titles = [
        "Novice",           # 1-5
        "Apprentice",       # 6-10
        "Adventurer",       # 11-15
        "Explorer",         # 16-20
        "Hero",             # 21-25
        "Champion",         # 26-30
        "Legend",           # 31-35
        "Master",           # 36-40
        "Grandmaster",      # 41-45
        "Elder",            # 46-50
        "Immortal"          # 51+
    ]
    
    title_index = min((level - 1) // 5, len(titles) - 1)
    return titles[title_index]

def calculate_quest_difficulty(quest_type):
    """
    Calculate base XP reward based on quest type
    
    Args:
        quest_type (str): Type of quest
    
    Returns:
        int: Base XP reward
    """
    difficulty_map = {
        "daily": 50,
        "easy": 25,
        "medium": 75,
        "hard": 150,
        "epic": 300,
        "legendary": 500
    }
    
    return difficulty_map.get(quest_type.lower(), 50)


def get_item_price(rarity):
    """
    Calculate item price based on rarity
    
    Args:
        rarity (ItemRarity): The rarity of the item
    
    Returns:
        int: Price in runes
    """
    price_map = {
        "common": 50,
        "uncommon": 100,
        "rare": 250,
        "epic": 500,
        "legendary": 1000
    }
    
    # Convert enum to string if needed
    if hasattr(rarity, 'value'):
        rarity_str = rarity.value.lower()
    else:
        rarity_str = str(rarity).lower()
    
    return price_map.get(rarity_str, 50)