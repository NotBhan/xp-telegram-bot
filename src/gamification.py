"""
Gamification System for XP Telegram Bot

This module implements the core gamification mechanics including XP/Levels,
Streaks, Runes, Titles, Trophies, Buffs, and Debuffs.
"""

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

# Import pre-calculated leveling tables for efficiency
from .leveling_tables import LevelingTables, XP_THRESHOLDS, CUMULATIVE_XP, RUNE_REWARDS

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class BuffType(Enum):
    """Types of buffs available in the system"""
    XP_BOOST = "xp_boost"
    RUNE_BOOST = "rune_boost"
    DEBUFF_SHIELD = "debuff_shield"
    STREAK_PROTECTION = "streak_protection"
    QUEST_MULTIPLIER = "quest_multiplier"

class DebuffType(Enum):
    """Types of debuffs that can be applied"""
    SLUGGISH = "sluggish"
    CHAOS_PENALTY = "chaos_penalty"
    RUNE_DRAIN = "rune_drain"
    XP_REDUCTION = "xp_reduction"
    QUEST_LIMIT = "quest_limit"
    STREAK_BLOCK = "streak_block"

@dataclass
class Buff:
    """Represents an active buff"""
    buff_type: BuffType
    name: str
    description: str
    effect_value: float  # Percentage or absolute value
    duration_days: int
    applied_date: datetime
    
    def is_active(self) -> bool:
        """Check if buff is still active"""
        return (datetime.now() - self.applied_date).days < self.duration_days
    
    def days_remaining(self) -> int:
        """Get days remaining for this buff"""
        elapsed = (datetime.now() - self.applied_date).days
        return max(0, self.duration_days - elapsed)
    
    def copy(self):
        """Create a copy of this buff"""
        return Buff(
            buff_type=self.buff_type,
            name=self.name,
            description=self.description,
            effect_value=self.effect_value,
            duration_days=self.duration_days,
            applied_date=self.applied_date
        )

@dataclass
class Debuff:
    """Represents an active debuff"""
    debuff_type: DebuffType
    name: str
    description: str
    effect_value: float  # Percentage or absolute value
    duration_days: int
    applied_date: datetime
    
    def is_active(self) -> bool:
        """Check if debuff is still active"""
        return (datetime.now() - self.applied_date).days < self.duration_days
    
    def days_remaining(self) -> int:
        """Get days remaining for this debuff"""
        elapsed = (datetime.now() - self.applied_date).days
        return max(0, self.duration_days - elapsed)
    
    def copy(self):
        """Create a copy of this debuff"""
        return Debuff(
            debuff_type=self.debuff_type,
            name=self.name,
            description=self.description,
            effect_value=self.effect_value,
            duration_days=self.duration_days,
            applied_date=self.applied_date
        )

@dataclass
class Title:
    """Represents a user title"""
    level_requirement: int
    name: str
    description: str
    emoji: str
    anti_debuff_perk: Optional[str] = None

@dataclass
class NewGamePlusData:
    """Represents New Game+ cycle data"""
    cycle: int  # NG+0, NG+1, NG+2, etc.
    total_completions: int  # How many times user has completed NG+
    carried_over_titles: List[str]
    carried_over_buffs: List[str]
    carried_over_trophies: List[str]
    prestige_rewards: List[str]
    started_date: datetime
    
    def get_xp_scaling_multiplier(self) -> float:
        """Get XP scaling multiplier for current NG+ cycle"""
        return 1.0 + (0.2 * self.cycle)  # +20% per NG+ cycle
    
    def get_quest_scaling_multiplier(self) -> float:
        """Get quest reward scaling multiplier for current NG+ cycle"""
        return 1.0 + (0.15 * self.cycle)  # +15% per NG+ cycle
    
    def get_debuff_scaling_multiplier(self) -> float:
        """Get debuff severity scaling multiplier for current NG+ cycle"""
        return 1.0 + (0.1 * self.cycle)  # +10% severity per NG+ cycle
    
    def get_debuff_duration_bonus(self) -> int:
        """Get additional debuff duration days for current NG+ cycle"""
@dataclass
class Trophy:
    """Represents an achievement trophy"""
    trophy_id: str
    name: str
    description: str
    emoji: str
    requirement: str
    earned_date: Optional[datetime] = None
    ng_plus_cycle: Optional[int] = None  # Track which NG+ cycle this was earned in

class GamificationEngine:
    """Core engine for gamification mechanics"""
    
    # Enhanced Title progression system with NG+ titles
    TITLES = {
        1: Title(1, "Novice", "Beginning your journey", "🌱"),
        25: Title(25, "Apprentice of Shadows", "Mastering the basics", "🎭", "Immune to Sluggish debuff"),
        50: Title(50, "Expert Craftsman", "Skilled in your domain", "🔨", "Reduces debuff duration by 1 day"),
        75: Title(75, "Master of Elements", "Command over the fundamentals", "🔥", "Immune to Chaos Penalty"),
        100: Title(100, "Legendary Champion", "Reached the pinnacle", "👑", "Immune to all debuffs for 1 day after earning")
    }
    
    # NG+ Prestige Titles
    NG_PLUS_TITLES = {
        "ng_plus_1": Title(0, "The Reborn", "Embraced the cycle of renewal (NG+1)", "🌀", "Additional buff slot unlocked"),
        "ng_plus_2": Title(0, "Endless Challenger", "Mastered the art of perseverance (NG+2)", "♾️", "Rune Shop discounts (-10%)"),
        "ng_plus_3": Title(0, "Eternal Flame", "Transcended mortal limitations (NG+3)", "🔥", "Immune to first debuff each month"),
        "ng_plus_4": Title(0, "Legend of the Cycle", "Become myth itself (NG+4)", "🌟", "Legendary status achieved"),
        "ng_plus_5": Title(0, "Ascended", "Beyond the realm of mortals (NG+5)", "✨", "Permanent rune bonus activated")
    }
    
    # Enhanced Buff definitions with NG+ rewards
    BUFF_CATALOG = {
        "focused_mind": Buff(
            BuffType.XP_BOOST, "Focused Mind", "+10% XP gain", 0.10, float('inf'), datetime.now()
        ),
        "rune_magnet": Buff(
            BuffType.RUNE_BOOST, "Rune Magnet", "+5 Runes per quest", 5.0, float('inf'), datetime.now()
        ),
        "phoenix_spirit": Buff(
            BuffType.STREAK_PROTECTION, "Phoenix Spirit", "First streak break per month ignored", 1.0, 30, datetime.now()
        ),
        "iron_will": Buff(
            BuffType.DEBUFF_SHIELD, "Iron Will", "Debuff durations reduced by 1 day", 1.0, float('inf'), datetime.now()
        ),
        "unyielding_will": Buff(
            BuffType.XP_BOOST, "Unyielding Will", "+15% XP gain (90-day streak reward)", 0.15, float('inf'), datetime.now()
        ),
        # NG+ Prestige Buffs
        "eternal_flame": Buff(
            BuffType.DEBUFF_SHIELD, "Eternal Flame", "Immune to first debuff each month (NG+3)", 1.0, float('inf'), datetime.now()
        ),
        "ascended_runes": Buff(
            BuffType.RUNE_BOOST, "Ascended", "+5 Runes per quest forever (NG+5)", 5.0, float('inf'), datetime.now()
        ),
        "ng_plus_mastery": Buff(
            BuffType.XP_BOOST, "NG+ Mastery", "+25% XP gain (NG+ completion bonus)", 0.25, float('inf'), datetime.now()
        )
    }
    
    # Enhanced Debuff definitions according to specification
    DEBUFF_CATALOG = {
        "sluggish": Debuff(
            DebuffType.SLUGGISH, "Sluggish", "No streak progress for 2 days", 1.0, 2, datetime.now()
        ),
        "shadow_state": Debuff(
            DebuffType.XP_REDUCTION, "Shadow State", "-20% XP from all quests", 0.20, 3, datetime.now()
        ),
        "chaos_penalty": Debuff(
            DebuffType.RUNE_DRAIN, "Chaos Penalty", "-5 Runes per quest", 5.0, 5, datetime.now()
        ),
        "broken_oath": Debuff(
            DebuffType.QUEST_LIMIT, "Broken Oath", "Cannot accept new challenges for 3 days", 1.0, 3, datetime.now()
        )
    }
    
    @staticmethod
    def calculate_level_requirement(level: int, ng_plus_data: Optional[NewGamePlusData] = None) -> int:
        """Calculate XP requirement for a specific level with NG+ scaling"""
        base_requirement = XP_THRESHOLDS.get(level, 50 + (level - 1) * 25)
        
        if ng_plus_data and ng_plus_data.cycle > 0:
            scaling_multiplier = ng_plus_data.get_xp_scaling_multiplier()
            return int(base_requirement * scaling_multiplier)
        
        return base_requirement
    
    @staticmethod
    def calculate_total_xp_for_level(level: int) -> int:
        """Calculate total XP needed to reach a specific level using pre-calculated table"""
        return CUMULATIVE_XP.get(level, 0)
    
    @staticmethod
    def calculate_level_from_xp(total_xp: int) -> Tuple[int, int, int]:
        """
        Calculate level, current level XP, and XP needed for next level
        Uses pre-calculated tables for efficiency
        
        Returns:
            (current_level, xp_in_current_level, xp_needed_for_next)
        """
        level_info = LevelingTables.get_level_from_xp(total_xp)
        return (
            level_info["level"],
            level_info["xp_in_current_level"],
            level_info["xp_needed_for_next"]
        )
    
    @staticmethod
    def process_xp_gain(
        current_xp: int, 
        xp_gain: int, 
        active_buffs: List[Buff], 
        active_debuffs: List[Debuff],
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> Dict[str, Any]:
        """
        Process XP gain with overflow handling according to specification:
        
        When XP >= XP_required(level):
        1. Increment level += 1
        2. Subtract required XP: XP = XP - XP_required(previous_level)
        3. Carry over overflow XP into the new level
        4. Trigger Level-Up Rewards
        
        This repeats in a loop until XP < next threshold.
        """
        # Apply buff/debuff modifiers to XP gain
        xp_multiplier = 1.0
        
        # Apply buff effects
        for buff in active_buffs:
            if buff.is_active() and buff.buff_type == BuffType.XP_BOOST:
                xp_multiplier += buff.effect_value
        
        # Apply debuff effects
        for debuff in active_debuffs:
            if debuff.is_active() and debuff.debuff_type in [DebuffType.SLUGGISH, DebuffType.XP_REDUCTION]:
                xp_multiplier -= debuff.effect_value
        
        # Ensure minimum 10% XP gain even with debuffs
        xp_multiplier = max(0.1, xp_multiplier)
        
        # Calculate modified XP gain
        modified_xp_gain = int(xp_gain * xp_multiplier)
        
        # Get current level and XP in that level
        current_level_info = GamificationEngine.calculate_level_from_xp(current_xp)
        old_level = current_level_info[0]
        current_xp_in_level = current_level_info[1]
        
        # Start with the XP in current level plus the gain
        working_xp_in_level = current_xp_in_level + modified_xp_gain
        current_level = old_level
        levels_gained = 0
        level_up_rune_bonus = 0
        level_up_details = []
        
        # Level-up processing loop according to specification
        while True:
            # Get XP requirement for CURRENT level (to advance FROM current level) with NG+ scaling
            current_level_requirement = GamificationEngine.calculate_level_requirement(current_level, ng_plus_data)
            
            # Check if we have enough XP in current level to level up
            if working_xp_in_level >= current_level_requirement:
                # Level up!
                levels_gained += 1
                
                # Subtract required XP (overflow handling)
                working_xp_in_level = working_xp_in_level - current_level_requirement
                
                # Advance to next level
                current_level += 1
                
                # Calculate level-up rewards: Base 10 + 2 * level (with NG+ scaling)
                level_runes = 10 + (2 * current_level)
                if ng_plus_data and ng_plus_data.cycle > 0:
                    level_runes = int(level_runes * ng_plus_data.get_quest_scaling_multiplier())
                
                level_up_rune_bonus += level_runes
                
                level_up_details.append({
                    "level": current_level,
                    "runes_earned": level_runes,
                    "is_milestone": current_level % 25 == 0,
                    "ng_plus_enhanced": ng_plus_data is not None and ng_plus_data.cycle > 0
                })
                
                # Continue the loop to check for more level-ups
                continue
            else:
                # No more level-ups possible
                break
        
        # Calculate final total XP
        final_total_xp = GamificationEngine.calculate_total_xp_for_level(current_level) + working_xp_in_level
        
        # Get final level info for response
        final_level_info = GamificationEngine.calculate_level_from_xp(final_total_xp)
        level_up_occurred = levels_gained > 0
        
        # Check for milestone rewards
        milestone_levels = [level for level in range(old_level + 1, current_level + 1) if level % 25 == 0]
        title_unlocked = len(milestone_levels) > 0
        new_title = None
        if title_unlocked:
            new_title = GamificationEngine.get_title_for_level(current_level).name
        
        return {
            "old_level": old_level,
            "new_level": current_level,
            "levels_gained": levels_gained,
            "level_up_occurred": level_up_occurred,
            "original_xp_gain": xp_gain,
            "modified_xp_gain": modified_xp_gain,
            "xp_multiplier": xp_multiplier,
            "new_total_xp": final_total_xp,
            "xp_in_current_level": working_xp_in_level,
            "xp_needed_for_next": max(0, GamificationEngine.calculate_level_requirement(current_level + 1, ng_plus_data) - working_xp_in_level),
            "level_up_rune_bonus": level_up_rune_bonus,
            "level_up_details": level_up_details,
            "milestone_levels": milestone_levels,
            "title_unlocked": title_unlocked,
            "new_title": new_title,
            "buffs_applied": [buff.name for buff in active_buffs if buff.is_active() and buff.buff_type == BuffType.XP_BOOST],
            "debuffs_applied": [debuff.name for debuff in active_debuffs if debuff.is_active() and debuff.debuff_type in [DebuffType.SLUGGISH, DebuffType.XP_REDUCTION]]
        }
    
    @staticmethod
    def calculate_streak_bonus(streak_days: int) -> Dict[str, int]:
        """Calculate bonus rewards for streak milestones according to specification"""
        bonuses = {"runes": 0, "xp": 0, "buffs_unlocked": [], "titles_unlocked": []}
        
        # Daily completion bonus
        if streak_days > 0:
            bonuses["runes"] += 5  # +5 Runes for each day completed
        
        # Milestone bonuses according to specification
        milestone_rewards = {
            7: {"runes": 25, "description": "7-day milestone"},
            14: {"runes": 50, "description": "14-day milestone"},
            30: {"runes": 100, "title": "The Consistent", "description": "30-day milestone"},
            90: {"runes": 200, "buff": "unyielding_will", "description": "90-day milestone"},
            180: {"runes": 500, "description": "180-day milestone"},
        }
        
        if streak_days in milestone_rewards:
            reward = milestone_rewards[streak_days]
            bonuses["runes"] += reward["runes"]
            
            if "title" in reward:
                bonuses["titles_unlocked"].append(reward["title"])
            
            if "buff" in reward:
                bonuses["buffs_unlocked"].append(reward["buff"])
        
        return bonuses
    
    @staticmethod
    def apply_streak_loss_debuff(days_missed: int, streak_length: int = 0) -> Debuff:
        """Apply appropriate debuff based on streak loss according to specification"""
        # Scale debuff severity with streak length for longer streaks
        severity_multiplier = 1.0
        if streak_length >= 30:
            severity_multiplier = 2.0  # Harsher penalty for breaking long streaks
        elif streak_length >= 10:
            severity_multiplier = 1.5
        
        if days_missed == 1:
            # Light penalty: Sluggish - No streak progress for 2 days
            debuff = GamificationEngine.DEBUFF_CATALOG["sluggish"].copy()
            debuff.applied_date = datetime.now()
            debuff.duration_days = max(2, int(2 * severity_multiplier))
            return debuff
        elif days_missed <= 3:
            # Medium penalty: Shadow State - 20% XP reduction
            debuff = GamificationEngine.DEBUFF_CATALOG["shadow_state"].copy()
            debuff.applied_date = datetime.now()
            debuff.duration_days = max(3, int(3 * severity_multiplier))
            return debuff
        else:
            # Heavy penalty: Chaos Penalty - Rune loss
            debuff = GamificationEngine.DEBUFF_CATALOG["chaos_penalty"].copy()
            debuff.applied_date = datetime.now()
            debuff.duration_days = max(5, min(7, int(5 * severity_multiplier)))
            return debuff
    
    @staticmethod
    def process_daily_quest_completion(
        user_id: int, 
        current_streak: int, 
        last_quest_date: Optional[datetime], 
        active_buffs: List[Buff]
    ) -> Dict[str, Any]:
        """Process daily quest completion and streak logic according to specification"""
        today = datetime.now().date()
        result = {
            "streak_updated": False,
            "streak_broken": False,
            "new_streak": current_streak,
            "daily_bonus": 0,
            "milestone_rewards": {},
            "debuff_applied": None,
            "buffs_unlocked": [],
            "titles_unlocked": []
        }
        
        if last_quest_date:
            last_date = last_quest_date.date() if isinstance(last_quest_date, datetime) else last_quest_date
            days_diff = (today - last_date).days
            
            if days_diff == 0:
                # Already completed quest today
                result["streak_updated"] = False
                return result
            elif days_diff == 1:
                # Continuing streak
                result["new_streak"] = current_streak + 1
                result["streak_updated"] = True
            else:
                # Streak broken
                result["streak_broken"] = True
                
                # Check for Phoenix Spirit buff (first break per month ignored)
                phoenix_protected = any(
                    buff.buff_type == BuffType.STREAK_PROTECTION and 
                    buff.name == "Phoenix Spirit" and 
                    buff.is_active() 
                    for buff in active_buffs
                )
                
                if phoenix_protected:
                    # Protected by Phoenix Spirit, continue streak
                    result["new_streak"] = current_streak + 1
                    result["streak_updated"] = True
                    result["streak_broken"] = False
                    result["phoenix_protection_used"] = True
                else:
                    # Apply debuff and reset streak
                    result["debuff_applied"] = GamificationEngine.apply_streak_loss_debuff(days_diff, current_streak)
                    result["new_streak"] = 1  # Reset to 1 (completing today's quest)
        else:
            # First quest ever
            result["new_streak"] = 1
            result["streak_updated"] = True
        
        # Calculate bonuses for the new streak
        if result["streak_updated"]:
            streak_bonuses = GamificationEngine.calculate_streak_bonus(result["new_streak"])
            result["daily_bonus"] = streak_bonuses["runes"]
            result["buffs_unlocked"] = streak_bonuses["buffs_unlocked"]
            result["titles_unlocked"] = streak_bonuses["titles_unlocked"]
            
            # Check for milestone rewards
            if result["new_streak"] in [7, 14, 30, 90, 180]:
                result["milestone_rewards"] = {
                    "streak_length": result["new_streak"],
                    "runes": streak_bonuses["runes"] - 5,  # Subtract daily bonus
                    "buffs": streak_bonuses["buffs_unlocked"],
                    "titles": streak_bonuses["titles_unlocked"]
                }
        
        return result
    
    @staticmethod
    def get_title_for_level(level: int) -> Title:
        """Get the appropriate title for a given level"""
        applicable_title = GamificationEngine.TITLES[1]  # Default novice
        
        for level_req, title in sorted(GamificationEngine.TITLES.items(), reverse=True):
            if level >= level_req:
                applicable_title = title
                break
        
        return applicable_title
    
    @staticmethod
    def apply_debuff_with_resistance(debuff: Debuff, active_buffs: List[Buff]) -> Debuff:
        """Apply debuff while checking for resistance buffs like Iron Will"""
        modified_debuff = debuff.copy() if hasattr(debuff, 'copy') else debuff
        
        # Check for Iron Will buff (reduces debuff duration by 1 day)
        for buff in active_buffs:
            if buff.is_active() and buff.name == "Iron Will":
                modified_debuff.duration_days = max(1, modified_debuff.duration_days - 1)
                break
        
        return modified_debuff
    
    @staticmethod
    def process_rune_transaction(
        current_runes: int, 
        rune_change: int, 
        active_buffs: List[Buff], 
        active_debuffs: List[Debuff]
    ) -> Dict[str, Any]:
        """Process rune gain/loss with buff/debuff effects according to specification"""
        if rune_change > 0:  # Rune gain
            rune_multiplier = 1.0
            flat_bonus = 0
            flat_penalty = 0
            
            # Apply buff effects
            for buff in active_buffs:
                if buff.is_active():
                    if buff.buff_type == BuffType.RUNE_BOOST:
                        flat_bonus += buff.effect_value
            
            # Apply debuff effects according to specification
            for debuff in active_debuffs:
                if debuff.is_active():
                    if debuff.debuff_type == DebuffType.RUNE_DRAIN:
                        flat_penalty += debuff.effect_value
            
            # Calculate final rune gain
            modified_rune_gain = int(rune_change * rune_multiplier) + int(flat_bonus) - int(flat_penalty)
            modified_rune_gain = max(1, modified_rune_gain)  # Minimum 1 rune gain
            
        else:  # Rune spending
            modified_rune_gain = rune_change  # No modifiers for spending
            rune_multiplier = 1.0
            flat_bonus = 0
            flat_penalty = 0
        
        new_rune_total = max(0, current_runes + modified_rune_gain)
        
        return {
            "original_rune_change": rune_change,
            "modified_rune_change": modified_rune_gain,
            "new_rune_total": new_rune_total,
            "rune_multiplier": rune_multiplier,
            "flat_bonus": flat_bonus,
            "flat_penalty": flat_penalty,
            "buffs_applied": [buff.name for buff in active_buffs if buff.is_active() and buff.buff_type == BuffType.RUNE_BOOST],
            "debuffs_applied": [debuff.name for debuff in active_debuffs if debuff.is_active() and debuff.debuff_type == DebuffType.RUNE_DRAIN]
        }
    
    @staticmethod
    def check_trophy_eligibility(user_stats: Dict[str, Any]) -> List[Trophy]:
        """Check which trophies the user is eligible for"""
        eligible_trophies = []
        
        # Define trophy requirements
        trophy_requirements = [
            {
                "id": "first_quest",
                "name": "First Steps",
                "description": "Complete your first quest",
                "emoji": "🏃",
                "requirement": "Complete 1 quest",
                "check": lambda stats: stats.get("total_quests_completed", 0) >= 1
            },
            {
                "id": "week_warrior",
                "name": "Week Warrior",
                "description": "Maintain a 7-day streak",
                "emoji": "⚡",
                "requirement": "7-day streak",
                "check": lambda stats: stats.get("max_streak", 0) >= 7
            },
            {
                "id": "unyielding_flame",
                "name": "Unyielding Flame",
                "description": "Complete a 30-day challenge",
                "emoji": "🔥",
                "requirement": "30-day streak",
                "check": lambda stats: stats.get("max_streak", 0) >= 30
            },
            {
                "id": "quest_master",
                "name": "Quest Master",
                "description": "Complete 100 total quests",
                "emoji": "🏆",
                "requirement": "Complete 100 quests",
                "check": lambda stats: stats.get("total_quests_completed", 0) >= 100
            },
            {
                "id": "side_quest_explorer",
                "name": "Side Quest Explorer",
                "description": "Complete 25 side quests",
                "emoji": "🌟",
                "requirement": "Complete 25 side quests",
                "check": lambda stats: stats.get("side_quests_completed", 0) >= 25
            },
            {
                "id": "quest_master",
                "name": "Quest Master",
                "description": "Complete 100 quests",
                "emoji": "🏆",
                "requirement": "Complete 100 quests",
                "check": lambda stats: stats.get("total_quests_completed", 0) >= 100
            },
            {
                "id": "rune_collector",
                "name": "Rune Collector",
                "description": "Accumulate 1000 runes",
                "emoji": "💎",
                "requirement": "Earn 1000 total runes",
                "check": lambda stats: stats.get("total_runes_earned", 0) >= 1000
            },
            {
                "id": "level_champion",
                "name": "Level Champion",
                "description": "Reach level 50",
                "emoji": "👑",
                "requirement": "Reach level 50",
                "check": lambda stats: stats.get("level", 0) >= 50
            }
        ]
        
        for trophy_data in trophy_requirements:
            if trophy_data["check"](user_stats):
                trophy = Trophy(
                    trophy_id=trophy_data["id"],
                    name=trophy_data["name"],
                    description=trophy_data["description"],
                    emoji=trophy_data["emoji"],
                    requirement=trophy_data["requirement"],
                    earned_date=datetime.now()
                )
                eligible_trophies.append(trophy)
        
    @staticmethod
    def format_dashboard_status(
        level: int,
        xp: int,
        xp_needed: int,
        streak: int,
        runes: int,
        title: str,
        active_buffs: List[Buff],
        active_debuffs: List[Debuff]
    ) -> str:
        """Format comprehensive dashboard display according to specification"""
        
        # Level and XP progress
        dashboard = f"🏅 Level {level} — {xp}/{xp + xp_needed} XP\n"
        
        # Streak status with next milestone
        next_milestone = None
        for milestone in [7, 14, 30, 90, 180]:
            if streak < milestone:
                next_milestone = milestone
                break
        
        if next_milestone:
            days_to_milestone = next_milestone - streak
            if next_milestone == 7:
                reward = "+25 Runes"
            elif next_milestone == 14:
                reward = "+50 Runes"
            elif next_milestone == 30:
                reward = "Title: The Consistent"
            elif next_milestone == 90:
                reward = "Buff: Unyielding Will"
            else:
                reward = "+500 Runes"
            
            dashboard += f"🔥 Streak: {streak} days (Next: {reward} at {next_milestone} days)\n"
        else:
            dashboard += f"🔥 Streak: {streak} days (Master level!)\n"
        
        # Active debuffs with countdown
        active_debuff_list = [d for d in active_debuffs if d.is_active()]
        if active_debuff_list:
            debuff_text = ", ".join([f"{d.name} ({d.days_remaining()} days left)" for d in active_debuff_list])
            dashboard += f"💀 Debuffs: {debuff_text}\n"
        
        # Active buffs
        active_buff_list = [b for b in active_buffs if b.is_active()]
        if active_buff_list:
            buff_text = ", ".join([f"{b.name} ({b.description})" for b in active_buff_list])
            dashboard += f"🌟 Buffs: {buff_text}\n"
        
        # Title and runes
        dashboard += f"🎖️ Title: {title}\n"
        dashboard += f"💰 Runes: {runes}"
        
        return dashboard
    
    @staticmethod
    def can_start_new_game_plus(level: int, total_xp: int) -> bool:
        """Check if user is eligible to start New Game+"""
        return level >= 100
    
    @staticmethod
    def create_new_game_plus_data(
        current_ng_cycle: int,
        carried_titles: List[str],
        carried_buffs: List[str], 
        carried_trophies: List[str]
    ) -> NewGamePlusData:
        """Create new NG+ data for a fresh cycle"""
        new_cycle = current_ng_cycle + 1
        
        # Add prestige rewards based on NG+ cycle
        prestige_rewards = []
        if new_cycle == 1:
            prestige_rewards.extend(["ng_plus_1", "additional_buff_slot"])
        elif new_cycle == 2:
            prestige_rewards.extend(["ng_plus_2", "rune_shop_discount"])
        elif new_cycle == 3:
            prestige_rewards.extend(["ng_plus_3", "eternal_flame"])
        elif new_cycle == 4:
            prestige_rewards.extend(["ng_plus_4", "legend_trophy"])
        elif new_cycle == 5:
            prestige_rewards.extend(["ng_plus_5", "ascended_runes"])
        
        return NewGamePlusData(
            cycle=new_cycle,
            total_completions=new_cycle,
            carried_over_titles=carried_titles,
            carried_over_buffs=carried_buffs,
            carried_over_trophies=carried_trophies,
            prestige_rewards=prestige_rewards,
            started_date=datetime.now()
        )
    
    @staticmethod
    def calculate_ng_plus_quest_rewards(
        base_xp: int,
        base_runes: int,
        level: int,
        difficulty: str,
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> Dict[str, int]:
        """Calculate quest rewards with NG+ scaling"""
        
        # Base calculations
        if difficulty == "Easy":
            xp_gain = base_xp * (1 + 0.1 * level)
        elif difficulty == "Medium":
            xp_gain = base_xp * (1 + 0.15 * level)
        elif difficulty == "Hard":
            xp_gain = base_xp * (1 + 0.2 * level)
        else:
            xp_gain = base_xp
        
        rune_gain = base_runes
        
        # Apply NG+ scaling
        if ng_plus_data and ng_plus_data.cycle > 0:
            quest_scaling = ng_plus_data.get_quest_scaling_multiplier()
            xp_gain = int(xp_gain * quest_scaling)
            rune_gain = int(rune_gain * quest_scaling)
        
        return {
            "xp": int(xp_gain),
            "runes": int(rune_gain)
        }
    
    @staticmethod
    def apply_ng_plus_debuff_scaling(
        debuff: Debuff,
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> Debuff:
        """Apply NG+ scaling to debuff severity and duration"""
        if not ng_plus_data or ng_plus_data.cycle == 0:
            return debuff
        
        scaled_debuff = debuff.copy()
        
        # Increase duration
        scaled_debuff.duration_days += ng_plus_data.get_debuff_duration_bonus()
        
        # Increase severity
        severity_multiplier = ng_plus_data.get_debuff_scaling_multiplier()
        scaled_debuff.effect_value *= severity_multiplier
        
        # Update description to reflect scaling
        if ng_plus_data.cycle > 0:
            scaled_debuff.description += f" (NG+{ng_plus_data.cycle} Enhanced)"
        
        return scaled_debuff
    
    @staticmethod
    def get_ng_plus_prestige_rewards(ng_cycle: int) -> Dict[str, Any]:
        """Get prestige rewards for completing a specific NG+ cycle"""
        rewards = {
            "titles": [],
            "buffs": [],
            "trophies": [],
            "special_effects": []
        }
        
        if ng_cycle == 1:
            rewards["titles"].append("The Reborn")
            rewards["special_effects"].append("Additional buff slot")
        elif ng_cycle == 2:
            rewards["titles"].append("Endless Challenger")
            rewards["special_effects"].append("Rune Shop discounts (-10%)")
        elif ng_cycle == 3:
            rewards["titles"].append("Eternal Flame")
            rewards["buffs"].append("eternal_flame")
        elif ng_cycle == 4:
            rewards["titles"].append("Legend of the Cycle")
            rewards["trophies"].append("Legend of the Cycle Trophy")
        elif ng_cycle >= 5:
            rewards["titles"].append("Ascended")
            rewards["buffs"].append("ascended_runes")
        
        return rewards
    
    @staticmethod
    def format_ng_plus_dashboard_status(
        level: int,
        xp: int,
        xp_needed: int,
        streak: int,
        runes: int,
        title: str,
        active_buffs: List[Buff],
        active_debuffs: List[Debuff],
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> str:
        """Format dashboard with NG+ information"""
        
        # Start with NG+ indicator if active
        dashboard = ""
        if ng_plus_data and ng_plus_data.cycle > 0:
            dashboard += f"🌀 NG+{ng_plus_data.cycle} Active\n"
        
        # Use base dashboard formatting
        base_dashboard = GamificationEngine.format_dashboard_status(
            level, xp, xp_needed, streak, runes, title, active_buffs, active_debuffs
        )
        
        dashboard += base_dashboard
        
        # Add NG+ specific information
        if ng_plus_data and ng_plus_data.cycle > 0:
            dashboard += f"\n🎆 **NG+ Benefits:**\n"
            dashboard += f"   • Completed cycles: {ng_plus_data.total_completions}\n"
            dashboard += f"   • XP scaling: +{int((ng_plus_data.get_xp_scaling_multiplier() - 1) * 100)}%\n"
            dashboard += f"   • Quest rewards: +{int((ng_plus_data.get_quest_scaling_multiplier() - 1) * 100)}%\n"
            
            if ng_plus_data.prestige_rewards:
                dashboard += f"   • Prestige unlocks: {len(ng_plus_data.prestige_rewards)}\n"
        
        return dashboard
    
    @staticmethod
    def should_apply_debuff_shield(active_buffs: List[Buff], incoming_debuff: Debuff) -> bool:
        """Check if a debuff shield should protect against an incoming debuff"""
        for buff in active_buffs:
            if buff.is_active() and buff.buff_type == BuffType.DEBUFF_SHIELD:
                return True
        return False
    
    @staticmethod
    def clean_expired_effects(buffs: List[Buff], debuffs: List[Debuff]) -> Tuple[List[Buff], List[Debuff]]:
        """Remove expired buffs and debuffs"""
        active_buffs = [buff for buff in buffs if buff.is_active()]
        active_debuffs = [debuff for debuff in debuffs if debuff.is_active()]
        return active_buffs, active_debuffs
    
    @staticmethod
    def process_quest_completion_with_streaks(
        quest_type: str,  # "main" or "side"
        quest_difficulty: str,
        base_xp: int,
        base_runes: int,
        user_level: int,
        current_streak: int,
        last_quest_date: Optional[datetime],
        active_buffs: List[Buff],
        active_debuffs: List[Debuff],
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> Dict[str, Any]:
        """
        Process quest completion with full integration:
        - Calculate quest rewards with modifiers
        - Update streaks (main quests only)
        - Apply streak bonuses
        - Handle NG+ scaling
        """
        result = {
            "quest_rewards": {},
            "streak_update": {},
            "total_bonuses": {},
            "effects_applied": []
        }
        
        # Calculate base quest rewards with NG+ scaling
        quest_rewards = GamificationEngine.calculate_ng_plus_quest_rewards(
            base_xp=base_xp,
            base_runes=base_runes,
            level=user_level,
            difficulty=quest_difficulty,
            ng_plus_data=ng_plus_data
        )
        
        # Apply buff/debuff modifiers to XP
        xp_multiplier = 1.0
        rune_flat_bonus = 0
        rune_flat_penalty = 0
        
        for buff in active_buffs:
            if buff.is_active():
                if buff.buff_type == BuffType.XP_BOOST:
                    xp_multiplier += buff.effect_value
                    result["effects_applied"].append(f"Buff: {buff.name}")
                elif buff.buff_type == BuffType.RUNE_BOOST:
                    rune_flat_bonus += buff.effect_value
                    result["effects_applied"].append(f"Buff: {buff.name}")
        
        for debuff in active_debuffs:
            if debuff.is_active():
                if debuff.debuff_type == DebuffType.XP_REDUCTION:
                    xp_multiplier -= debuff.effect_value
                    result["effects_applied"].append(f"Debuff: {debuff.name}")
                elif debuff.debuff_type == DebuffType.RUNE_DRAIN:
                    rune_flat_penalty += debuff.effect_value
                    result["effects_applied"].append(f"Debuff: {debuff.name}")
        
        # Ensure minimum XP gain
        xp_multiplier = max(0.1, xp_multiplier)
        
        # Calculate final quest rewards
        final_xp = int(quest_rewards["xp"] * xp_multiplier)
        final_runes = max(1, quest_rewards["runes"] + int(rune_flat_bonus) - int(rune_flat_penalty))
        
        result["quest_rewards"] = {
            "base_xp": quest_rewards["xp"],
            "final_xp": final_xp,
            "xp_multiplier": xp_multiplier,
            "base_runes": quest_rewards["runes"],
            "final_runes": final_runes,
            "rune_bonus": rune_flat_bonus,
            "rune_penalty": rune_flat_penalty
        }
        
        # Process streak updates (only for main quests)
        if quest_type == "main":
            streak_result = GamificationEngine.process_daily_quest_completion(
                user_id=0,  # Not needed for calculation
                current_streak=current_streak,
                last_quest_date=last_quest_date,
                active_buffs=active_buffs
            )
            
            result["streak_update"] = streak_result
            
            # Add streak bonuses to rune total
            if streak_result.get("daily_bonus", 0) > 0:
                final_runes += streak_result["daily_bonus"]
                result["quest_rewards"]["streak_bonus_runes"] = streak_result["daily_bonus"]
        else:
            result["streak_update"] = {
                "streak_updated": False,
                "new_streak": current_streak,
                "note": "Side quests do not affect streaks"
            }
        
        # Calculate totals
        result["total_bonuses"] = {
            "total_xp_gained": final_xp,
            "total_runes_gained": final_runes,
            "streak_bonus_included": quest_type == "main"
        }
        
        return result
    
    @staticmethod
    def generate_quest_recommendations(
        user_level: int,
        completion_history: List[Dict[str, Any]],
        current_streak: int,
        active_buffs: List[Buff],
        ng_plus_data: Optional[NewGamePlusData] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized quest recommendations based on:
        - User level and progress
        - Completion history patterns
        - Current buffs and streak status
        - NG+ scaling considerations
        """
        recommendations = {
            "suggested_difficulties": [],
            "recommended_categories": [],
            "side_quest_recommendation": False,
            "special_notes": []
        }
        
        # Analyze completion patterns
        if completion_history:
            recent_completions = completion_history[-10:]  # Last 10 quests
            completion_rate = len([q for q in recent_completions if q.get("status") == "Completed"]) / len(recent_completions)
            
            # Difficulty recommendations based on success rate
            if completion_rate > 0.8:
                recommendations["suggested_difficulties"] = ["Medium", "Hard", "Hard"]
                recommendations["special_notes"].append("High completion rate - try harder challenges!")
            elif completion_rate < 0.4:
                recommendations["suggested_difficulties"] = ["Easy", "Easy", "Medium"]
                recommendations["special_notes"].append("Focus on easier quests to build momentum")
            else:
                recommendations["suggested_difficulties"] = ["Easy", "Medium", "Hard"]
        else:
            # Default for new users
            if user_level <= 5:
                recommendations["suggested_difficulties"] = ["Easy", "Easy", "Medium"]
            elif user_level <= 15:
                recommendations["suggested_difficulties"] = ["Easy", "Medium", "Medium"]
            else:
                recommendations["suggested_difficulties"] = ["Medium", "Medium", "Hard"]
        
        # Category analysis
        if completion_history:
            category_performance = {}
            for quest in completion_history[-20:]:
                category = quest.get("category", "").split(" - ")[0]
                if category not in category_performance:
                    category_performance[category] = {"total": 0, "completed": 0}
                
                category_performance[category]["total"] += 1
                if quest.get("status") == "Completed":
                    category_performance[category]["completed"] += 1
            
            # Recommend categories with moderate success (not too easy, not too hard)
            for category, stats in category_performance.items():
                if stats["total"] > 3:
                    success_rate = stats["completed"] / stats["total"]
                    if 0.4 <= success_rate <= 0.8:
                        recommendations["recommended_categories"].append(category)
        
        # Default categories if none recommended
        if not recommendations["recommended_categories"]:
            recommendations["recommended_categories"] = ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"]
        
        # Side quest recommendations
        if current_streak >= 7:  # Reward streak maintainers
            recommendations["side_quest_recommendation"] = True
            recommendations["special_notes"].append("Great streak! Side quest available for bonus rewards")
        elif random.random() < 0.3:  # 30% chance for variety
            recommendations["side_quest_recommendation"] = True
        
        # NG+ considerations
        if ng_plus_data and ng_plus_data.cycle > 0:
            recommendations["special_notes"].append(f"NG+{ng_plus_data.cycle}: +{int((ng_plus_data.get_quest_scaling_multiplier() - 1) * 100)}% rewards!")
            # NG+ users get more challenging recommendations
            recommendations["suggested_difficulties"] = ["Medium", "Hard", "Hard"]
        
        # Buff-based recommendations
        for buff in active_buffs:
            if buff.is_active():
                if buff.buff_type == BuffType.XP_BOOST:
                    recommendations["special_notes"].append(f"XP Boost active: Perfect time for high-XP quests!")
                elif buff.buff_type == BuffType.RUNE_BOOST:
                    recommendations["special_notes"].append(f"Rune Boost active: All quests give bonus runes!")
        
        return recommendations