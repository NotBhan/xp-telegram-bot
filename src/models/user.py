from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class UserProfile:
    user_id: int
    username: str
    first_name: str
    xp: int = 0
    level: int = 1
    streak: int = 0
    runes: int = 0
    title: str = "Novice"
    debuffs: List[str] = None
    last_activity: Optional[datetime] = None
    streak_start_date: Optional[datetime] = None

    def __post_init__(self):
        if self.debuffs is None:
            self.debuffs = []

    def add_xp(self, amount: int) -> dict:
        """Add XP and return level up info"""
        old_level = self.level
        self.xp += amount
        self.level = self.calculate_level(self.xp)
        runes_earned = amount // 10
        self.runes += runes_earned
        
        return {
            "old_level": old_level,
            "new_level": self.level,
            "level_up": self.level > old_level,
            "runes_earned": runes_earned
        }

    def calculate_level(self, xp: int) -> int:
        """Calculate level based on XP"""
        if xp < 100:
            return 1
        return int((xp / 100) ** 0.5) + 1

    def get_title(self) -> str:
        """Get title based on level"""
        titles = [
            "Novice", "Apprentice", "Adventurer", "Hero", "Champion",
            "Legend", "Master", "Grandmaster", "Elder", "Immortal"
        ]
        index = min((self.level - 1) // 25, len(titles) - 1)
        return titles[index]

    def get_progress_to_next_level(self) -> tuple:
        """Get progress to next level (current, total)"""
        if self.level == 1:
            current = self.xp
            total = 100
        else:
            current = self.xp - (self.level - 1) ** 2 * 100
            total = self.level ** 2 * 100 - (self.level - 1) ** 2 * 100
        
        return current, total

    def update_title(self):
        """Update title based on current level"""
        self.title = self.get_title()

    def add_debuff(self, debuff: str):
        """Add a debuff"""
        if debuff not in self.debuffs:
            self.debuffs.append(debuff)

    def remove_debuff(self, debuff: str):
        """Remove a debuff"""
        if debuff in self.debuffs:
            self.debuffs.remove(debuff)