from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

class QuestStatus(Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    FAILED = "Failed"
    EXPIRED = "Expired"

class QuestCategory(Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    ACHIEVEMENT = "Achievement"
    CHALLENGE = "Challenge"

@dataclass
class Quest:
    quest_id: str
    user_id: int
    name: str
    description: str
    xp_reward: int
    rune_reward: int = 0
    category: QuestCategory = QuestCategory.DAILY
    status: QuestStatus = QuestStatus.ACTIVE
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def complete(self) -> dict:
        """Complete the quest and return rewards"""
        if self.status != QuestStatus.ACTIVE:
            return {"success": False, "message": "Quest is not active"}
        
        self.status = QuestStatus.COMPLETED
        self.completed_at = datetime.now()
        
        return {
            "success": True,
            "xp_reward": self.xp_reward,
            "rune_reward": self.rune_reward,
            "message": f"Quest '{self.name}' completed!"
        }

    def is_expired(self) -> bool:
        """Check if quest has expired"""
        if not self.due_date:
            return False
        return datetime.now() > self.due_date

    def get_time_remaining(self) -> Optional[str]:
        """Get time remaining for quest"""
        if not self.due_date:
            return None
        
        remaining = self.due_date - datetime.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        days = remaining.days
        hours = remaining.seconds // 3600
        
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {(remaining.seconds % 3600) // 60}m"
        else:
            return f"{remaining.seconds // 60}m"

    def get_progress_display(self) -> str:
        """Get progress display for quest"""
        if self.status == QuestStatus.COMPLETED:
            return "✅ Completed"
        elif self.status == QuestStatus.FAILED:
            return "❌ Failed"
        elif self.status == QuestStatus.EXPIRED:
            return "⏰ Expired"
        else:
            return "🎯 Active"