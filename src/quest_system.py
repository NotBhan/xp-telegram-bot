"""
Enhanced Quest & Side Quest System for XP Telegram Bot

This module implements the complete Quest System specification including:
- Main Quests: Daily structured challenges with exact XP formulas
- Side Quests: Optional randomized tasks with bonus rewards
- Quest completion flow with streak integration
- Notion Quest Log Database integration
- Bot command support (/quests, /complete, /sidequest, /reroll)
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field

from .gamification import GamificationEngine

logger = logging.getLogger(__name__)

class QuestType(Enum):
    """Types of quests in the system"""
    MAIN = "main"
    SIDE = "side"

class QuestDifficulty(Enum):
    """Quest difficulty levels"""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    RARE = "Rare"  # For special side quests

class QuestStatus(Enum):
    """Quest completion states"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

@dataclass
class Quest:
    """Represents a quest with all properties from specification"""
    name: str
    quest_id: str
    description: str
    difficulty: QuestDifficulty
    quest_type: QuestType
    xp_reward: int
    rune_reward: int
    status: QuestStatus = QuestStatus.NOT_STARTED
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    estimated_time: Optional[str] = None
    assigned_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    user_level_at_creation: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quest to dictionary for Notion API"""
        return {
            "name": self.name,
            "quest_id": self.quest_id,
            "description": self.description,
            "difficulty": self.difficulty.value,
            "quest_type": self.quest_type.value,
            "xp_reward": self.xp_reward,
            "rune_reward": self.rune_reward,
            "status": self.status.value,
            "category": self.category,
            "tags": self.tags,
            "estimated_time": self.estimated_time,
            "assigned_date": self.assigned_date.isoformat() if self.assigned_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "user_level_at_creation": self.user_level_at_creation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quest':
        """Create quest from dictionary (from Notion API)"""
        return cls(
            name=data.get("name", ""),
            quest_id=data.get("quest_id", ""),
            description=data.get("description", ""),
            difficulty=QuestDifficulty(data.get("difficulty", "Easy")),
            quest_type=QuestType(data.get("quest_type", "main")),
            xp_reward=data.get("xp_reward", 0),
            rune_reward=data.get("rune_reward", 0),
            status=QuestStatus(data.get("status", "Not Started")),
            category=data.get("category"),
            tags=data.get("tags", []),
            estimated_time=data.get("estimated_time"),
            assigned_date=datetime.fromisoformat(data["assigned_date"]) if data.get("assigned_date") else None,
            completed_date=datetime.fromisoformat(data["completed_date"]) if data.get("completed_date") else None,
            user_level_at_creation=data.get("user_level_at_creation")
        )

class QuestSystem:
    """
    Enhanced Quest & Side Quest System implementing the complete specification
    """
    
    # Main Quest Categories
    MAIN_QUEST_CATEGORIES = [
        "🎵 Music Production",
        "📈 Business / Store", 
        "🧘 Personal Growth"
    ]
    
    # Quest templates organized by category and difficulty
    QUEST_TEMPLATES = {
        "🎵 Music Production": {
            QuestDifficulty.EASY: [
                {"name": "Make 1 loop", "description": "Create a single loop (drums, melody, or texture)", "time": "15-30 min"},
                {"name": "Organize samples", "description": "Organize 5 samples in your library", "time": "10-20 min"},
                {"name": "Adjust mix levels", "description": "Adjust mix levels on 1 track", "time": "15-25 min"},
                {"name": "Export draft", "description": "Export a 30-second draft idea", "time": "5-15 min"}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Post reel on IG", "description": "Create and post a music reel on Instagram", "time": "30-45 min"},
                {"name": "Layer sounds", "description": "Layer sounds for richer texture", "time": "30-60 min"},
                {"name": "Design drum sounds", "description": "Design 2 original drum sounds", "time": "30-45 min"},
                {"name": "Finish arrangement", "description": "Complete arrangement of 1 full song idea", "time": "45-90 min"}
            ],
            QuestDifficulty.HARD: [
                {"name": "Finish one track section", "description": "Complete a full section (verse, chorus, bridge) of a track", "time": "2-4 hours"},
                {"name": "Complete mixdown", "description": "Complete a full mixdown of a track", "time": "2-4 hours"},
                {"name": "Master track", "description": "Master a finished track (basic mastering)", "time": "1-2 hours"},
                {"name": "Submit track", "description": "Submit track to streaming platform or share online", "time": "30-60 min"}
            ]
        },
        "📈 Business / Store": {
            QuestDifficulty.EASY: [
                {"name": "Reply to messages", "description": "Reply to 1 message or comment", "time": "5-10 min"},
                {"name": "Update product", "description": "Update 1 product description in your store", "time": "10-20 min"},
                {"name": "Research trends", "description": "Research 1 trending audio niche", "time": "15-30 min"}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Create promo", "description": "Create and post a promo reel/story", "time": "45-90 min"},
                {"name": "Design cover art", "description": "Design cover art for 1 sample pack", "time": "60-120 min"},
                {"name": "Write blog post", "description": "Write a blog or description post about your work", "time": "45-90 min"}
            ],
            QuestDifficulty.HARD: [
                {"name": "Launch sample pack", "description": "Launch a new sample pack", "time": "2-4 hours"},
                {"name": "IG content streak", "description": "Run a week-long IG content streak", "time": "7 days"},
                {"name": "Reach collaborators", "description": "Reach out to 3 potential collaborators", "time": "60-90 min"}
            ]
        },
        "🧘 Personal Growth": {
            QuestDifficulty.EASY: [
                {"name": "Read 5 pages", "description": "Read 5 pages of a book", "time": "10-15 min"},
                {"name": "Meditate 5min", "description": "Meditate for 5 minutes", "time": "5 min"},
                {"name": "Quick journal", "description": "Journal 3 sentences", "time": "5-10 min"}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Exercise 30min", "description": "Exercise for 30 minutes", "time": "30 min"},
                {"name": "Deep work session", "description": "Complete a deep work session (90 minutes focus)", "time": "90 min"},
                {"name": "Study theory", "description": "Study music theory or production for 30 minutes", "time": "30 min"}
            ],
            QuestDifficulty.HARD: [
                {"name": "Finish book", "description": "Finish a full book", "time": "Multiple sessions"},
                {"name": "7-day streak", "description": "Take on a 7-day streak of daily meditation/journaling", "time": "7 days"},
                {"name": "Build tutorial", "description": "Build and share a tutorial/resource", "time": "2-4 hours"}
            ]
        }
    }
    
    # Side Quest templates with randomized rewards
    SIDE_QUEST_TEMPLATES = [
        {"name": "Take a 20 min nature walk", "description": "Go outside and enjoy nature for 20 minutes", "difficulty": QuestDifficulty.EASY},
        {"name": "Sketch something random in 5 minutes", "description": "Draw or sketch anything that comes to mind", "difficulty": QuestDifficulty.EASY},
        {"name": "Go stargazing for 10 minutes tonight", "description": "Look up at the stars and enjoy the night sky", "difficulty": QuestDifficulty.MEDIUM},
        {"name": "Listen to a new artist and note what inspires you", "description": "Discover new music and write down inspiration", "difficulty": QuestDifficulty.MEDIUM},
        {"name": "Reach out to an old friend and check in", "description": "Send a message to reconnect with someone", "difficulty": QuestDifficulty.MEDIUM},
        {"name": "Try 10 minutes of meditation", "description": "Practice mindfulness meditation", "difficulty": QuestDifficulty.EASY},
        {"name": "Record 3 natural sounds", "description": "Capture interesting sounds from your environment", "difficulty": QuestDifficulty.MEDIUM},
        {"name": "Share a music meme", "description": "Post a funny music-related meme", "difficulty": QuestDifficulty.EASY},
        {"name": "Write down 3 things you're grateful for", "description": "Practice gratitude journaling", "difficulty": QuestDifficulty.EASY},
        {"name": "Clean your workspace", "description": "Organize your creative space before working", "difficulty": QuestDifficulty.EASY},
        {"name": "Teach someone 1 small thing", "description": "Share knowledge you learned today", "difficulty": QuestDifficulty.MEDIUM},
        {"name": "Try a new creative technique", "description": "Experiment with an unfamiliar production method", "difficulty": QuestDifficulty.RARE}
    ]
    
    @staticmethod
    def calculate_main_quest_xp(difficulty: QuestDifficulty, level: int) -> int:
        """
        Calculate XP reward using exact specification formulas:
        - Easy → 5 * (1 + 0.1 * Level) XP
        - Medium → 10 * (1 + 0.15 * Level) XP  
        - Hard → 15 * (1 + 0.2 * Level) XP
        """
        formulas = {
            QuestDifficulty.EASY: lambda lvl: int(5 * (1 + 0.1 * lvl)),
            QuestDifficulty.MEDIUM: lambda lvl: int(10 * (1 + 0.15 * lvl)),
            QuestDifficulty.HARD: lambda lvl: int(15 * (1 + 0.2 * lvl))
        }
        
        return formulas.get(difficulty, formulas[QuestDifficulty.EASY])(level)
    
    @staticmethod
    def calculate_side_quest_xp(difficulty: QuestDifficulty) -> int:
        """
        Calculate randomized side quest XP:
        - Easy: 5–15 XP
        - Medium: 10–25 XP
        - Hard: 20–40 XP
        - Rare: 50+ XP
        """
        ranges = {
            QuestDifficulty.EASY: (5, 15),
            QuestDifficulty.MEDIUM: (10, 25),
            QuestDifficulty.HARD: (20, 40),
            QuestDifficulty.RARE: (50, 75)
        }
        
        min_xp, max_xp = ranges.get(difficulty, (5, 15))
        return random.randint(min_xp, max_xp)
    
    @staticmethod
    def calculate_main_quest_runes(difficulty: QuestDifficulty) -> int:
        """Calculate rune rewards for main quests"""
        base_rewards = {
            QuestDifficulty.EASY: 12,
            QuestDifficulty.MEDIUM: 20,
            QuestDifficulty.HARD: 35
        }
        
        return base_rewards.get(difficulty, 12)
    
    @staticmethod
    def calculate_side_quest_runes(difficulty: QuestDifficulty) -> int:
        """
        Calculate randomized side quest runes (2–5x main quest rewards):
        """
        base_main = QuestSystem.calculate_main_quest_runes(difficulty)
        multiplier = random.uniform(2.0, 5.0)
        return int(base_main * multiplier)
    
    @staticmethod
    def generate_daily_quests(user_level: int) -> List[Quest]:
        """
        Generate 3 daily main quests as per specification:
        - One quest from each main category
        - Difficulty scaled to user level
        - Proper XP/Rune calculations
        """
        quests = []
        
        # Determine difficulty distribution based on level
        if user_level <= 5:
            difficulties = [QuestDifficulty.EASY, QuestDifficulty.EASY, QuestDifficulty.MEDIUM]
        elif user_level <= 15:
            difficulties = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.MEDIUM]
        elif user_level <= 30:
            difficulties = [QuestDifficulty.MEDIUM, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]
        else:
            difficulties = [QuestDifficulty.MEDIUM, QuestDifficulty.HARD, QuestDifficulty.HARD]
        
        # Create one quest per category
        for i, category in enumerate(QuestSystem.MAIN_QUEST_CATEGORIES):
            difficulty = difficulties[i]
            template = random.choice(QuestSystem.QUEST_TEMPLATES[category][difficulty])
            
            quest = Quest(
                name=template["name"],
                quest_id=f"Q{i+1}",
                description=template["description"],
                difficulty=difficulty,
                quest_type=QuestType.MAIN,
                xp_reward=QuestSystem.calculate_main_quest_xp(difficulty, user_level),
                rune_reward=QuestSystem.calculate_main_quest_runes(difficulty),
                category=category,
                estimated_time=template["time"],
                assigned_date=datetime.now(),
                user_level_at_creation=user_level
            )
            
            quests.append(quest)
        
        return quests
    
    @staticmethod
    def generate_side_quest() -> Optional[Quest]:
        """
        Generate a random side quest with bonus rewards
        """
        template = random.choice(QuestSystem.SIDE_QUEST_TEMPLATES)
        
        quest = Quest(
            name=template["name"],
            quest_id="SQ1",
            description=template["description"],
            difficulty=template["difficulty"],
            quest_type=QuestType.SIDE,
            xp_reward=QuestSystem.calculate_side_quest_xp(template["difficulty"]),
            rune_reward=QuestSystem.calculate_side_quest_runes(template["difficulty"]),
            category="🌟 Side Quests",
            estimated_time="Variable",
            assigned_date=datetime.now()
        )
        
        return quest
    
    @staticmethod
    def should_trigger_side_quest(
        user_level: int, 
        last_side_quest_date: Optional[datetime] = None,
        daily_side_quest_chance: float = 0.3
    ) -> bool:
        """
        Determine if a side quest should appear based on:
        - Base probability (30% by default)
        - User level (higher levels get slightly more frequent)
        - Time since last side quest
        """
        # Base probability increases slightly with level
        base_probability = min(daily_side_quest_chance + (user_level * 0.005), 0.5)
        
        # Increase probability if it's been a while
        if last_side_quest_date:
            days_since = (datetime.now() - last_side_quest_date).days
            if days_since >= 2:
                base_probability += 0.2
            elif days_since >= 4:
                base_probability += 0.4
        
        return random.random() < base_probability
    
    @staticmethod
    def complete_quest(
        quest: Quest,
        user_level: int,
        user_runes: int,
        user_total_xp: int,
        current_streak: int,
        last_quest_date: Optional[datetime],
        active_buffs: List = None,
        active_debuffs: List = None
    ) -> Dict[str, Any]:
        """
        Complete a quest and apply all rewards/effects:
        - XP gain with buff/debuff modifiers
        - Rune rewards with modifiers
        - Streak updates (only for main quests)
        - Level-up processing
        """
        if active_buffs is None:
            active_buffs = []
        if active_debuffs is None:
            active_debuffs = []
        
        # Mark quest as completed
        quest.status = QuestStatus.COMPLETED
        quest.completed_date = datetime.now()
        
        # Process XP gain through the gamification engine
        xp_result = GamificationEngine.process_xp_gain(
            current_xp=user_total_xp,
            xp_gain=quest.xp_reward,
            active_buffs=active_buffs,
            active_debuffs=active_debuffs
        )
        
        # Process rune gain through the gamification engine
        rune_result = GamificationEngine.process_rune_transaction(
            current_runes=user_runes,
            rune_change=quest.rune_reward,
            active_buffs=active_buffs,
            active_debuffs=active_debuffs
        )
        
        # Process streak updates (only for main quests)
        streak_result = {"streak_updated": False, "new_streak": current_streak}
        if quest.quest_type == QuestType.MAIN:
            streak_result = GamificationEngine.process_daily_quest_completion(
                user_id=0,  # Not needed for calculation
                current_streak=current_streak,
                last_quest_date=last_quest_date,
                active_buffs=active_buffs
            )
        
        return {
            "quest_completed": quest.to_dict(),
            "xp_result": xp_result,
            "rune_result": rune_result,
            "streak_result": streak_result,
            "total_rewards": {
                "xp_gained": xp_result["modified_xp_gain"],
                "runes_gained": rune_result["modified_rune_change"],
                "levels_gained": xp_result.get("levels_gained", 0),
                "new_level": xp_result.get("new_level", user_level),
                "new_total_xp": xp_result.get("new_total_xp", user_total_xp),
                "new_rune_total": rune_result["new_rune_total"],
                "new_streak": streak_result["new_streak"]
            }
        }
    
    @staticmethod
    def calculate_reroll_cost(user_level: int, difficulty: QuestDifficulty) -> int:
        """
        Calculate Rune cost for rerolling a quest:
        - Base cost increases with difficulty
        - Scales slightly with user level
        """
        base_costs = {
            QuestDifficulty.EASY: 5,
            QuestDifficulty.MEDIUM: 10,
            QuestDifficulty.HARD: 15,
            QuestDifficulty.RARE: 20
        }
        
        base_cost = base_costs.get(difficulty, 5)
        level_multiplier = 1 + (user_level * 0.05)  # 5% increase per level
        
        return int(base_cost * level_multiplier)
    
    @staticmethod
    def reroll_quest(
        original_quest: Quest,
        user_level: int,
        user_runes: int
    ) -> Dict[str, Any]:
        """
        Reroll a quest for Rune cost:
        - Check if user has enough Runes
        - Generate new quest of same category/difficulty
        - Deduct Rune cost
        """
        reroll_cost = QuestSystem.calculate_reroll_cost(user_level, original_quest.difficulty)
        
        if user_runes < reroll_cost:
            return {
                "success": False,
                "error": f"Not enough Runes. Need {reroll_cost}, have {user_runes}",
                "cost": reroll_cost
            }
        
        # Generate new quest
        if original_quest.quest_type == QuestType.MAIN:
            # Find templates for same category and difficulty
            category = original_quest.category
            difficulty = original_quest.difficulty
            
            if category in QuestSystem.QUEST_TEMPLATES and difficulty in QuestSystem.QUEST_TEMPLATES[category]:
                available_templates = QuestSystem.QUEST_TEMPLATES[category][difficulty]
                # Filter out the current quest
                available_templates = [t for t in available_templates if t["name"] != original_quest.name]
                
                if available_templates:
                    template = random.choice(available_templates)
                    
                    new_quest = Quest(
                        name=template["name"],
                        quest_id=original_quest.quest_id,
                        description=template["description"],
                        difficulty=difficulty,
                        quest_type=QuestType.MAIN,
                        xp_reward=QuestSystem.calculate_main_quest_xp(difficulty, user_level),
                        rune_reward=QuestSystem.calculate_main_quest_runes(difficulty),
                        category=category,
                        estimated_time=template["time"],
                        assigned_date=datetime.now(),
                        user_level_at_creation=user_level
                    )
                else:
                    return {
                        "success": False,
                        "error": "No alternative quests available for reroll"
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid quest category or difficulty"
                }
        else:
            # Side quest reroll
            new_quest = QuestSystem.generate_side_quest()
            new_quest.quest_id = original_quest.quest_id
        
        return {
            "success": True,
            "new_quest": new_quest,
            "cost": reroll_cost,
            "remaining_runes": user_runes - reroll_cost
        }
    
    @staticmethod
    def format_quest_dashboard(quests: List[Quest]) -> str:
        """
        Format quests for dashboard display according to specification:
        
        📜 Quests:
        [ ] Q1 — Make 2 loops (Easy) — 15 XP, 12 Runes
        [ ] Q2 — Post reel on IG (Medium) — 35 XP, 20 Runes
        [ ] Q3 — Finish one track section (Hard) — 75 XP, 35 Runes

        ✨ Side Quest:
        [ ] SQ1 — Take a 20 min nature walk (Rare) — 50 XP, 50 Runes
        """
        if not quests:
            return "📜 No active quests available"
        
        # Separate main quests and side quests
        main_quests = [q for q in quests if q.quest_type == QuestType.MAIN and q.status != QuestStatus.COMPLETED]
        side_quests = [q for q in quests if q.quest_type == QuestType.SIDE and q.status != QuestStatus.COMPLETED]
        
        dashboard = ""
        
        # Main quests section
        if main_quests:
            dashboard += "📜 Quests:\n"
            for quest in main_quests:
                status_icon = "✅" if quest.status == QuestStatus.COMPLETED else "[ ]"
                dashboard += f"{status_icon} {quest.quest_id} — {quest.name} ({quest.difficulty.value}) — {quest.xp_reward} XP, {quest.rune_reward} Runes\n"
        
        # Side quests section
        if side_quests:
            if main_quests:
                dashboard += "\n"
            dashboard += "✨ Side Quest:\n"
            for quest in side_quests:
                status_icon = "✅" if quest.status == QuestStatus.COMPLETED else "[ ]"
                dashboard += f"{status_icon} {quest.quest_id} — {quest.name} ({quest.difficulty.value}) — {quest.xp_reward} XP, {quest.rune_reward} Runes\n"
        
        return dashboard.strip()