"""
Pre-calculated XP and Leveling Tables for XP Telegram Bot

This module contains pre-calculated tables for efficient lookups of:
- XP thresholds for each level
- Cumulative XP requirements
- Rune rewards for level-ups
- Milestone unlocks (titles, buffs, trophies)

Formula: XP_required(level) = 50 + (level - 1) * 25
"""

from typing import Dict, List, Any

class LevelingTables:
    """Pre-calculated leveling data for efficient lookups"""
    
    # XP thresholds for levels 1-100
    XP_THRESHOLDS = {}
    
    # Cumulative XP needed to reach each level
    CUMULATIVE_XP = {}
    
    # Rune rewards for each level (Base: 10 + 2 * level)
    LEVEL_RUNE_REWARDS = {}
    
    # Milestone unlocks
    MILESTONE_UNLOCKS = {}
    
    @classmethod
    def initialize_tables(cls):
        """Initialize all pre-calculated tables"""
        cls._calculate_xp_thresholds()
        cls._calculate_cumulative_xp()
        cls._calculate_rune_rewards()
        cls._define_milestone_unlocks()
    
    @classmethod
    def _calculate_xp_thresholds(cls):
        """Calculate XP thresholds for each level"""
        for level in range(1, 101):  # Levels 1-100
            if level == 1:
                cls.XP_THRESHOLDS[level] = 50
            else:
                # XP_required(level) = 50 + (level - 1) * 25
                cls.XP_THRESHOLDS[level] = 50 + (level - 1) * 25
    
    @classmethod
    def _calculate_cumulative_xp(cls):
        """Calculate cumulative XP needed to reach each level"""
        cls.CUMULATIVE_XP[1] = 0  # Level 1 starts at 0 XP
        
        for level in range(2, 101):
            cls.CUMULATIVE_XP[level] = cls.CUMULATIVE_XP[level - 1] + cls.XP_THRESHOLDS[level - 1]
    
    @classmethod
    def _calculate_rune_rewards(cls):
        """Calculate rune rewards for each level"""
        for level in range(1, 101):
            # Base reward: +10 Runes, Bonus scaling: +2 * level Runes
            cls.LEVEL_RUNE_REWARDS[level] = 10 + (2 * level)
    
    @classmethod
    def _define_milestone_unlocks(cls):
        """Define milestone unlocks for special levels"""
        cls.MILESTONE_UNLOCKS = {
            25: {
                "title": {"name": "Apprentice of Shadows", "emoji": "🎭", "perk": "Immune to Sluggish debuff"},
                "buff": {"name": "Focused Mind", "effect": "+10% XP gain", "duration": 7},
                "trophy": {"name": "Quarter Century", "description": "Reached level 25"}
            },
            50: {
                "title": {"name": "Expert Craftsman", "emoji": "🔨", "perk": "Reduces debuff duration by 1 day"},
                "buff": {"name": "Rune Magnet", "effect": "+10 Runes per quest", "duration": 10},
                "trophy": {"name": "Halfway Hero", "description": "Reached level 50"}
            },
            75: {
                "title": {"name": "Master of Elements", "emoji": "🔥", "perk": "Immune to Chaos Penalty"},
                "buff": {"name": "Quest Master", "effect": "Double quest rewards", "duration": 5},
                "trophy": {"name": "Master's Ascension", "description": "Reached level 75"}
            },
            100: {
                "title": {"name": "Legendary Champion", "emoji": "👑", "perk": "Immune to all debuffs for 1 day after earning"},
                "buff": {"name": "Legendary Aura", "effect": "All bonuses doubled", "duration": 14},
                "trophy": {"name": "Century Legend", "description": "Reached the legendary level 100"}
            }
        }
    
    @classmethod
    def get_level_from_xp(cls, total_xp: int) -> Dict[str, Any]:
        """Get level information from total XP using pre-calculated tables"""
        if not cls.XP_THRESHOLDS:
            cls.initialize_tables()
        
        # Find current level
        current_level = 1
        for level in range(1, 101):
            if total_xp < cls.CUMULATIVE_XP.get(level + 1, float('inf')):
                current_level = level
                break
        
        # Calculate XP in current level
        xp_for_current_level = cls.CUMULATIVE_XP[current_level]
        xp_in_current_level = total_xp - xp_for_current_level
        
        # Calculate XP needed for next level
        next_level_threshold = cls.XP_THRESHOLDS.get(current_level + 1, 0)
        xp_needed_for_next = next_level_threshold - xp_in_current_level
        
        return {
            "level": current_level,
            "xp_in_current_level": xp_in_current_level,
            "xp_needed_for_next": max(0, xp_needed_for_next),
            "next_level_threshold": next_level_threshold,
            "total_xp": total_xp
        }
    
    @classmethod
    def get_levelup_rewards(cls, new_level: int) -> Dict[str, Any]:
        """Get rewards for reaching a specific level"""
        if not cls.LEVEL_RUNE_REWARDS:
            cls.initialize_tables()
        
        rewards = {
            "runes": cls.LEVEL_RUNE_REWARDS.get(new_level, 10),
            "is_milestone": new_level in cls.MILESTONE_UNLOCKS,
            "milestone_rewards": None
        }
        
        if rewards["is_milestone"]:
            rewards["milestone_rewards"] = cls.MILESTONE_UNLOCKS[new_level]
        
        return rewards
    
    @classmethod
    def get_xp_table_summary(cls, max_level: int = 50) -> List[Dict[str, Any]]:
        """Get a summary table of XP requirements and rewards"""
        if not cls.XP_THRESHOLDS:
            cls.initialize_tables()
        
        table = []
        for level in range(1, min(max_level + 1, 101)):
            entry = {
                "level": level,
                "xp_threshold": cls.XP_THRESHOLDS[level],
                "cumulative_xp": cls.CUMULATIVE_XP[level],
                "rune_reward": cls.LEVEL_RUNE_REWARDS[level],
                "is_milestone": level in cls.MILESTONE_UNLOCKS
            }
            
            if entry["is_milestone"]:
                milestone = cls.MILESTONE_UNLOCKS[level]
                entry["title"] = milestone["title"]["name"]
                entry["title_emoji"] = milestone["title"]["emoji"]
                entry["special_reward"] = milestone["buff"]["name"]
            
            table.append(entry)
        
        return table
    
    @classmethod
    def validate_xp_formula(cls, test_cases: List[Dict[str, Any]]) -> bool:
        """Validate the XP formula against test cases"""
        if not cls.XP_THRESHOLDS:
            cls.initialize_tables()
        
        for case in test_cases:
            level = case["level"]
            expected_threshold = case["expected_threshold"]
            actual_threshold = cls.XP_THRESHOLDS.get(level)
            
            if actual_threshold != expected_threshold:
                print(f"❌ Level {level}: Expected {expected_threshold}, Got {actual_threshold}")
                return False
            else:
                print(f"✅ Level {level}: {actual_threshold} XP (Correct)")
        
        return True

# Initialize tables on import
LevelingTables.initialize_tables()

# Example usage and validation
if __name__ == "__main__":
    # Test cases based on the specification
    test_cases = [
        {"level": 1, "expected_threshold": 50},
        {"level": 2, "expected_threshold": 75},
        {"level": 3, "expected_threshold": 100},
        {"level": 4, "expected_threshold": 125},
        {"level": 5, "expected_threshold": 150},
        {"level": 10, "expected_threshold": 275},
        {"level": 25, "expected_threshold": 650},
        {"level": 50, "expected_threshold": 1275},
    ]
    
    print("🧮 XP Formula Validation:")
    is_valid = LevelingTables.validate_xp_formula(test_cases)
    
    if is_valid:
        print("\n✅ All test cases passed! XP formula is correctly implemented.")
        
        # Show sample table
        print("\n📊 Sample XP Table (Levels 1-10):")
        table = LevelingTables.get_xp_table_summary(10)
        print("Level | XP Req | Cumulative | Runes | Special")
        print("-" * 50)
        for entry in table:
            special = entry.get("title", "").split()[0] if entry["is_milestone"] else ""
            print(f"{entry['level']:5} | {entry['xp_threshold']:6} | {entry['cumulative_xp']:10} | {entry['rune_reward']:5} | {special}")
    else:
        print("\n❌ Test cases failed. Please check the XP formula implementation.")

# Export key data for easy access
LEVEL_XP_TABLE = LevelingTables.get_xp_table_summary(100)
XP_THRESHOLDS = LevelingTables.XP_THRESHOLDS
CUMULATIVE_XP = LevelingTables.CUMULATIVE_XP
RUNE_REWARDS = LevelingTables.LEVEL_RUNE_REWARDS
MILESTONE_UNLOCKS = LevelingTables.MILESTONE_UNLOCKS