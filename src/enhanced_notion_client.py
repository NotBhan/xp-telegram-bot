"""
Enhanced Notion Client for Quest & Side Quest System

Integrates the new quest system with Notion Quest Log Database
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from notion_client import AsyncClient

from .quest_system import Quest, QuestType, QuestStatus, QuestDifficulty
from .quest_coordinator import QuestCoordinator
from .side_quest_manager import SideQuestManager, SideQuestTrigger
from .gamification import GamificationEngine

logger = logging.getLogger(__name__)

class EnhancedNotionClient:
    """Enhanced Notion client with quest system integration"""
    
    def __init__(self, notion_token: str, quest_db_id: str, xp_db_id: str):
        self.client = AsyncClient(auth=notion_token)
        self.quest_db_id = quest_db_id
        self.xp_db_id = xp_db_id
        self.coordinator = QuestCoordinator()
    
    async def save_quest_to_notion(self, quest: Quest, user_id: int) -> Optional[str]:
        """Save quest to Notion Quest Log Database"""
        try:
            result = await self.client.pages.create(
                parent={"database_id": self.quest_db_id},
                properties={
                    "Name": {"title": [{"text": {"content": quest.name}}]},
                    "Quest ID": {"rich_text": [{"text": {"content": quest.quest_id}}]},
                    "Assignee": {"relation": [{"id": await self._get_user_page_id(user_id)}]},
                    "Status": {"select": {"name": quest.status.value}},
                    "Difficulty": {"select": {"name": quest.difficulty.value}},
                    "XP Reward": {"number": quest.xp_reward},
                    "Rune Reward": {"number": quest.rune_reward},
                    "Description": {"rich_text": [{"text": {"content": quest.description}}]},
                    "Category": {"select": {"name": quest.category}},
                    "Quest Type": {"select": {"name": quest.quest_type.value}},
                    "Assigned Date": {"date": {"start": quest.assigned_date.isoformat()}},
                    "User Level": {"number": quest.user_level_at_creation}
                }
            )
            return result["id"]
        except Exception as e:
            logger.error(f"Failed to save quest to Notion: {e}")
            return None
    
    async def update_quest_status(self, quest_id: str, status: QuestStatus, completed_date: Optional[datetime] = None) -> bool:
        """Update quest status in Notion"""
        try:
            properties = {"Status": {"select": {"name": status.value}}}
            if completed_date:
                properties["Completed Date"] = {"date": {"start": completed_date.isoformat()}}
            
            await self.client.pages.update(page_id=quest_id, properties=properties)
            return True
        except Exception as e:
            logger.error(f"Failed to update quest status: {e}")
            return False
    
    async def create_daily_quests(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and save daily quest set"""
        quest_set = self.coordinator.create_daily_quest_set(user_data)
        
        saved_quests = {"main_quests": [], "side_quest": None}
        
        # Save main quests
        for quest in quest_set["main_quests"]:
            notion_id = await self.save_quest_to_notion(quest, user_id)
            if notion_id:
                quest_dict = quest.to_dict()
                quest_dict["notion_id"] = notion_id
                saved_quests["main_quests"].append(quest_dict)
        
        # Save side quest if exists
        if quest_set["side_quest"]:
            notion_id = await self.save_quest_to_notion(quest_set["side_quest"], user_id)
            if notion_id:
                quest_dict = quest_set["side_quest"].to_dict()
                quest_dict["notion_id"] = notion_id
                saved_quests["side_quest"] = quest_dict
        
        return saved_quests
    
    async def complete_quest(self, quest_notion_id: str, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete quest and apply all rewards"""
        # Get quest from Notion
        quest_page = await self.client.pages.retrieve(page_id=quest_notion_id)
        quest = await self._notion_page_to_quest(quest_page)
        
        if not quest:
            return {"error": "Quest not found"}
        
        # Process completion through coordinator
        completion_result = self.coordinator.completion_processor.complete_quest(
            quest=quest,
            user_data=user_data
        )
        
        # Update quest status in Notion
        await self.update_quest_status(
            quest_notion_id, 
            QuestStatus.COMPLETED, 
            completion_result["quest_completed"]["completion_time"]
        )
        
        # Update user data in XP database
        await self._update_user_from_completion(user_id, completion_result)
        
        return completion_result
    
    async def trigger_side_quest(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Manually trigger a side quest"""
        side_quest = SideQuestManager.generate_side_quest(
            user_level=user_data.get("level", 1),
            trigger=SideQuestTrigger.MANUAL_REQUEST
        )
        
        notion_id = await self.save_quest_to_notion(side_quest, user_id)
        if notion_id:
            quest_dict = side_quest.to_dict()
            quest_dict["notion_id"] = notion_id
            return quest_dict
        
        return None
    
    async def reroll_quest(self, quest_notion_id: str, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reroll a quest for Rune cost"""
        # Get original quest
        quest_page = await self.client.pages.retrieve(page_id=quest_notion_id)
        original_quest = await self._notion_page_to_quest(quest_page)
        
        if not original_quest:
            return {"error": "Quest not found"}
        
        # Process reroll
        from .quest_system import QuestSystem
        reroll_result = QuestSystem.reroll_quest(
            original_quest=original_quest,
            user_level=user_data.get("level", 1),
            user_runes=user_data.get("runes", 0)
        )
        
        if not reroll_result["success"]:
            return reroll_result
        
        # Update quest in Notion
        new_quest = reroll_result["new_quest"]
        await self.client.pages.update(
            page_id=quest_notion_id,
            properties={
                "Name": {"title": [{"text": {"content": new_quest.name}}]},
                "Description": {"rich_text": [{"text": {"content": new_quest.description}}]},
                "XP Reward": {"number": new_quest.xp_reward},
                "Rune Reward": {"number": new_quest.rune_reward}
            }
        )
        
        # Deduct runes from user
        await self._update_user_runes(user_id, -reroll_result["cost"])
        
        return {
            "success": True,
            "new_quest": new_quest.to_dict(),
            "cost": reroll_result["cost"],
            "remaining_runes": reroll_result["remaining_runes"]
        }
    
    async def _notion_page_to_quest(self, page: Dict[str, Any]) -> Optional[Quest]:
        """Convert Notion page to Quest object"""
        try:
            props = page["properties"]
            return Quest(
                name=props["Name"]["title"][0]["text"]["content"],
                quest_id=props["Quest ID"]["rich_text"][0]["text"]["content"],
                description=props["Description"]["rich_text"][0]["text"]["content"],
                difficulty=QuestDifficulty(props["Difficulty"]["select"]["name"]),
                quest_type=QuestType(props["Quest Type"]["select"]["name"]),
                xp_reward=props["XP Reward"]["number"],
                rune_reward=props["Rune Reward"]["number"],
                status=QuestStatus(props["Status"]["select"]["name"]),
                category=props["Category"]["select"]["name"]
            )
        except Exception as e:
            logger.error(f"Failed to convert Notion page to Quest: {e}")
            return None
    
    async def _get_user_page_id(self, user_id: int) -> str:
        """Get user's Notion page ID from XP database"""
        try:
            result = await self.client.databases.query(
                database_id=self.xp_db_id,
                filter={"property": "User ID", "number": {"equals": user_id}}
            )
            return result["results"][0]["id"] if result["results"] else None
        except Exception as e:
            logger.error(f"Failed to get user page ID: {e}")
            return None
    
    async def _update_user_from_completion(self, user_id: int, completion_result: Dict[str, Any]) -> bool:
        """Update user data in XP database from quest completion"""
        try:
            user_page_id = await self._get_user_page_id(user_id)
            if not user_page_id:
                return False
            
            new_totals = completion_result["new_totals"]
            await self.client.pages.update(
                page_id=user_page_id,
                properties={
                    "Level": {"number": new_totals["level"]},
                    "XP": {"number": new_totals["total_xp"]},
                    "Runes": {"number": new_totals["runes"]},
                    "Streak": {"number": new_totals["streak"]},
                    "Last Quest Date": {"date": {"start": new_totals["last_quest_date"]}},
                    "Last Activity": {"date": {"start": datetime.now().isoformat()}}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update user from completion: {e}")
            return False
    
    async def _update_user_runes(self, user_id: int, rune_change: int) -> bool:
        """Update user runes"""
        try:
            user_page_id = await self._get_user_page_id(user_id)
            if not user_page_id:
                return False
            
            # Get current runes
            user_page = await self.client.pages.retrieve(page_id=user_page_id)
            current_runes = user_page["properties"]["Runes"]["number"]
            new_runes = max(0, current_runes + rune_change)
            
            await self.client.pages.update(
                page_id=user_page_id,
                properties={"Runes": {"number": new_runes}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update user runes: {e}")
            return False