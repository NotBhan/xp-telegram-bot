import os
import logging
import httpx
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from notion_client import AsyncClient
from notion_client.errors import APIResponseError, RequestTimeoutError

# Import quest data and management
from ..quest_data import QUEST_DATABASE, REWARD_FORMULAS, LEVEL_QUEST_DISTRIBUTION
from ..quest_manager import quest_manager, QuestSelectionStrategy
from ..gamification import GamificationEngine, Buff, Debuff, Title, Trophy

logger = logging.getLogger(__name__)

class NotionClient:
    """Enhanced Notion client with better error handling and retry logic"""
    
    def __init__(self):
        self.client = AsyncClient(auth=os.getenv('NOTION_TOKEN'))
        self.xp_db = os.getenv('XP_DB_ID')
        self.quest_db = os.getenv('CHALLENGE_DB_ID')
        self.inventory_db = os.getenv('INVENTORY_DB_ID')
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def test_connection(self) -> bool:
        """Test the Notion API connection"""
        try:
            # Test connection by listing databases
            await self.client.search(filter={"property": "object", "value": "database"})
            logger.info("Notion API connection successful")
            return True
        except Exception as e:
            logger.error(f"Notion API connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Notion API: {e}")
    
    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry operation with exponential backoff"""
        import asyncio
        
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except (APIResponseError, RequestTimeoutError, httpx.TimeoutException) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Operation failed after {self.max_retries} attempts: {e}")
                    raise
                
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error in operation: {e}")
                raise

    async def create_user(self, user_id: int, username: str, name: str) -> Optional[Dict[str, Any]]:
        """Create a new user with error handling"""
        try:
            return await self._retry_operation(
                self.client.pages.create,
                parent={"database_id": self.xp_db},
                properties={
                    "User ID": {"number": user_id},
                    "Username": {"rich_text": [{"text": {"content": username}}]},
                    "First Name": {"rich_text": [{"text": {"content": name}}]},
                    "XP": {"number": 0},
                    "Level": {"number": 1},
                    "Runes": {"number": 100},  # Start with 100 runes
                    "Streak": {"number": 0},
                    "Max Streak": {"number": 0},
                    "Last Quest Date": {"date": None},
                    "Current Title": {"select": {"name": "Novice"}},
                    "Active Debuffs": {"multi_select": []},
                    "Active Buffs": {"multi_select": []},
                    "Last Activity": {"date": {"start": datetime.now().isoformat()}}
                }
            )
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with error handling"""
        try:
            res = await self._retry_operation(
                self.client.databases.query,
                database_id=self.xp_db,
                filter={"property": "User ID", "number": {"equals": user_id}}
            )
            return res["results"][0] if res["results"] else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    def calculate_level_threshold(self, level: int) -> int:
        """Calculate XP required for next level with scaling"""
        return level ** 2 * 100

    async def update_user_xp(self, user_id: int, xp_gain: int) -> Optional[Dict[str, Any]]:
        """Update user XP with gamification system integration"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return None
            
            # Get current user data
            current_xp = user["properties"].get("XP", {}).get("number") or 0
            current_level = user["properties"].get("Level", {}).get("number") or 1
            current_runes = user["properties"].get("Runes", {}).get("number") or 0
            
            # Get active buffs and debuffs
            active_buffs = await self.get_active_buffs(user_id)
            active_debuffs = await self.get_active_debuffs(user_id)
            
            # Process XP gain with gamification
            xp_result = GamificationEngine.process_xp_gain(
                current_xp, xp_gain, active_buffs, active_debuffs
            )
            
            # Calculate level up bonuses
            new_runes = current_runes + xp_result["level_up_rune_bonus"]
            
            # Get new title if level changed
            new_title = GamificationEngine.get_title_for_level(xp_result["new_level"])
            
            # Prepare update properties
            update_props = {
                "XP": {"number": xp_result["new_total_xp"]},
                "Level": {"number": xp_result["new_level"]},
                "Runes": {"number": new_runes},
                "Current Title": {"select": {"name": new_title.name}},
                "Last Activity": {"date": {"start": datetime.now().isoformat()}}
            }
            
            # Update in Notion
            result = await self._retry_operation(
                self.client.pages.update,
                page_id=user["id"],
                properties=update_props
            )
            
            # Check for new trophies if level up occurred
            if xp_result["level_up_occurred"]:
                await self.check_and_award_trophies(user_id)
                
                # Award title-specific buffs
                if xp_result["new_level"] in [25, 50, 75, 100]:
                    await self.award_title_buff(user_id, new_title)
            
            # Return comprehensive result
            return {
                **xp_result,
                "new_runes": new_runes,
                "new_title": new_title.name if xp_result["level_up_occurred"] else None,
                "title_unlocked": xp_result["new_level"] in [25, 50, 75, 100]
            }
            
        except Exception as e:
            logger.error(f"Error updating user XP for user {user_id}: {e}")
            return None

    def get_title_for_level(self, level: int) -> str:
        """Get title based on level"""
        titles = {
            1: "Novice",
            25: "Apprentice",
            50: "Expert",
            75: "Master",
            100: "Legend"
        }
        
        applicable_title = "Novice"
        for lvl, title in sorted(titles.items(), reverse=True):
            if level >= lvl:
                applicable_title = title
                break
        return applicable_title

    async def update_streak(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Update daily streak with gamification system"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return None
            
            last_quest_str = user["properties"].get("Last Quest Date", {}).get("date", {}).get("start")
            current_streak = user["properties"].get("Streak", {}).get("number") or 0
            max_streak = user["properties"].get("Max Streak", {}).get("number") or 0
            current_runes = user["properties"].get("Runes", {}).get("number") or 0
            
            today = datetime.now().date()
            streak_result = {"streak_continued": False, "streak_broken": False, "bonuses_earned": {}}
            
            if last_quest_str:
                last_quest_date = datetime.fromisoformat(last_quest_str.replace('Z', '+00:00')).date()
                days_diff = (today - last_quest_date).days
                
                if days_diff == 0:
                    # Already completed quest today, no change
                    streak_result["streak_continued"] = True
                elif days_diff == 1:
                    # Continued streak
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                    streak_result["streak_continued"] = True
                    
                    # Calculate streak bonuses
                    streak_bonuses = GamificationEngine.calculate_streak_bonus(current_streak)
                    if streak_bonuses["runes"] > 0 or streak_bonuses["xp"] > 0:
                        current_runes += streak_bonuses["runes"]
                        streak_result["bonuses_earned"] = streak_bonuses
                        
                        # Award XP bonus
                        if streak_bonuses["xp"] > 0:
                            await self.update_user_xp(user_id, streak_bonuses["xp"])
                else:
                    # Broke streak - apply debuff unless protected
                    streak_result["streak_broken"] = True
                    
                    # Check for streak protection buff
                    active_buffs = await self.get_active_buffs(user_id)
                    streak_protected = any(buff.buff_type.value == "streak_protection" for buff in active_buffs if buff.is_active())
                    
                    if not streak_protected:
                        # Apply streak loss debuff
                        debuff = GamificationEngine.apply_streak_loss_debuff(days_diff)
                        await self.apply_debuff(user_id, debuff)
                        current_streak = 1  # Reset to 1 (completing today's quest)
                        streak_result["debuff_applied"] = debuff.name
                    else:
                        # Consume protection and maintain streak
                        await self.consume_streak_protection(user_id)
                        current_streak += 1  # Continue streak with protection
                        max_streak = max(max_streak, current_streak)
                        streak_result["protection_used"] = True
            else:
                # First quest
                current_streak = 1
                max_streak = 1
                streak_result["first_quest"] = True
            
            # Update user data
            update_result = await self._retry_operation(
                self.client.pages.update,
                page_id=user["id"],
                properties={
                    "Streak": {"number": current_streak},
                    "Max Streak": {"number": max_streak},
                    "Last Quest Date": {"date": {"start": datetime.now().isoformat()}},
                    "Runes": {"number": current_runes},
                    "Last Activity": {"date": {"start": datetime.now().isoformat()}}
                }
            )
            
            # Check for streak milestone trophies
            if current_streak in [7, 30, 100]:
                await self.check_and_award_trophies(user_id)
            
            return {
                **streak_result,
                "new_streak": current_streak,
                "max_streak": max_streak,
                "runes_earned": streak_result["bonuses_earned"].get("runes", 0)
            }
            
        except Exception as e:
            logger.error(f"Error updating streak for user {user_id}: {e}")
            return None
    
    async def consume_streak_protection(self, user_id: int) -> bool:
        """Remove streak protection buff from user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            current_buffs = user["properties"].get("Active Buffs", {}).get("multi_select", [])
            updated_buffs = []
            protection_consumed = False
            
            for buff_entry in current_buffs:
                buff_name = buff_entry["name"]
                if "Streak Guardian" in buff_name and not protection_consumed:
                    protection_consumed = True
                    continue  # Skip this buff (consume it)
                updated_buffs.append(buff_entry)
            
            if protection_consumed:
                await self._retry_operation(
                    self.client.pages.update,
                    page_id=user["id"],
                    properties={
                        "Active Buffs": {"multi_select": updated_buffs}
                    }
                )
                logger.info(f"Consumed streak protection for user {user_id}")
            
            return protection_consumed
            
        except Exception as e:
            logger.error(f"Error consuming streak protection for user {user_id}: {e}")
            return False

    async def apply_debuff(self, user_id: int, debuff_name: str, severity: int = 1):
        """Apply a debuff to the user"""
        user = await self.get_user(user_id)
        if not user:
            return
            
        current_debuffs = user["properties"].get("Active Debuffs", {}).get("multi_select", [])
        debuff_names = [d["name"] for d in current_debuffs]
        
        if debuff_name not in debuff_names:
            debuff_names.append(debuff_name)
            
        await self.client.pages.update(
            page_id=user["id"],
            properties={
                "Active Debuffs": {"multi_select": [{"name": name} for name in debuff_names]}
            }
        )

    async def remove_debuff(self, user_id: int, debuff_name: str):
        """Remove a specific debuff"""
        user = await self.get_user(user_id)
        if not user:
            return
            
        current_debuffs = user["properties"].get("Active Debuffs", {}).get("multi_select", [])
        debuff_names = [d["name"] for d in current_debuffs if d["name"] != debuff_name]
        
        await self.client.pages.update(
            page_id=user["id"],
            properties={
                "Active Debuffs": {"multi_select": [{"name": name} for name in debuff_names]}
            }
        )

    async def apply_buff(self, user_id: int, buff_name: str):
        """Apply a buff to the user"""
        user = await self.get_user(user_id)
        if not user:
            return
            
        current_buffs = user["properties"].get("Active Buffs", {}).get("multi_select", [])
        buff_names = [b["name"] for b in current_buffs]
        
        if buff_name not in buff_names:
            buff_names.append(buff_name)
            
        await self.client.pages.update(
            page_id=user["id"],
            properties={
                "Active Buffs": {"multi_select": [{"name": name} for name in buff_names]}
            }
        )

    async def award_trophy(self, user_id: int, trophy_name: str, description: str):
        """Award a trophy item to user's inventory"""
        trophy_data = {
            "name": trophy_name,
            "type": "Trophy",
            "rarity": "Legendary",
            "description": description,
            "price": 0,
            "effect": "Bragging rights"
        }
        return await self.add_item_to_inventory(user_id, trophy_data)

    async def update_user_runes(self, user_id: int, rune_change: int):
        """Update user runes (positive for gain, negative for spend)"""
        user = await self.get_user(user_id)
        if not user:
            return None
            
        current_runes = user["properties"].get("Runes", {}).get("number") or 0
        new_runes = max(0, current_runes + rune_change)  # Prevent negative runes
        
        return await self.client.pages.update(
            page_id=user["id"],
            properties={
                "Runes": {"number": new_runes},
                "Last Activity": {"date": {"start": datetime.now().isoformat()}}
            }
        )

    async def get_user_stats(self, user_id: int):
        """Get comprehensive user stats for dashboard"""
        user = await self.get_user(user_id)
        if not user:
            return None
            
        properties = user["properties"]
        return {
            "xp": properties.get("XP", {}).get("number") or 0,
            "level": properties.get("Level", {}).get("number") or 1,
            "runes": properties.get("Runes", {}).get("number") or 0,
            "streak": properties.get("Streak", {}).get("number") or 0,
            "max_streak": properties.get("Max Streak", {}).get("number") or 0,
            "title": properties.get("Current Title", {}).get("select", {}).get("name", "Novice"),
            "debuffs": [d["name"] for d in properties.get("Active Debuffs", {}).get("multi_select", [])],
            "buffs": [b["name"] for b in properties.get("Active Buffs", {}).get("multi_select", [])],
            "last_activity": properties.get("Last Activity", {}).get("date", {}).get("start")
        }

    async def get_quests(self, user_id: int):
        """Get quests for a user with robust property handling"""
        try:
            # Try multiple property names for user filtering
            filter_conditions = []
            
            user_properties = ["User ID", "User", "Assigned To", "Player"]
            for prop in user_properties:
                try:
                    # Build filter for this property
                    filter_condition = {
                        "property": prop,
                        "number": {
                            "equals": user_id
                        }
                    }
                    
                    response = await self.client.databases.query(
                        database_id=self.quest_db,
                        filter=filter_condition
                    )
                    
                    # If we get results, this property name works
                    if response.get("results"):
                        return response["results"]
                        
                except Exception as e:
                    # This property doesn't exist, try next one
                    continue
            
            # If no user filter worked, try getting all active quests
            try:
                response = await self.client.databases.query(
                    database_id=self.quest_db,
                    filter={
                        "property": "Status",
                        "select": {
                            "equals": "Active"
                        }
                    }
                )
                return response["results"]
                
            except Exception as e:
                # If no Status property, return all quests
                response = await self.client.databases.query(
                    database_id=self.quest_db
                )
                return response["results"]
                
        except Exception as e:
            logger.error(f"Error fetching quests: {e}")
            return []

    async def create_quest(self, user_id: int, quest_data: dict):
        """Create a quest with enhanced properties and robust error handling"""
        try:
            # Build properties dict with fallback handling
            properties = {
                "Quest Name": {"title": [{"text": {"content": quest_data.get("name", "Quest")}}]},
                "XP Reward": {"number": quest_data.get("xp_reward", 50)},
                "Rune Reward": {"number": quest_data.get("rune_reward", quest_data.get("xp_reward", 50) // 10)},
                "Status": {"select": {"name": "Active"}},
                "Created": {"date": {"start": datetime.now().isoformat()}},
                "Due Date": {"date": {"start": (datetime.now() + timedelta(days=1)).isoformat()}}
            }
            
            # Add User ID with fallback property names
            try:
                properties["User ID"] = {"number": user_id}
            except:
                try:
                    properties["User"] = {"number": user_id}
                except:
                    properties["Assigned To"] = {"number": user_id}
            
            # Add Description if provided
            if quest_data.get("description"):
                properties["Description"] = {"rich_text": [{"text": {"content": quest_data["description"]}}]}
            
            # Add Category if provided
            if quest_data.get("category"):
                properties["Category"] = {"select": {"name": quest_data["category"]}}
            
            # Add Difficulty if provided
            if quest_data.get("difficulty"):
                properties["Difficulty"] = {"select": {"name": quest_data["difficulty"]}}
            
            # Add Quest Type if provided
            if quest_data.get("quest_type"):
                properties["Quest Type"] = {"select": {"name": quest_data["quest_type"]}}
            
            # Add User Level at Creation for analytics
            if quest_data.get("user_level_at_creation"):
                properties["User Level at Creation"] = {"number": quest_data["user_level_at_creation"]}
            
            # Add Tags as multi-select if provided
            if quest_data.get("tags"):
                tag_objects = [{"name": tag} for tag in quest_data["tags"][:5]]  # Limit to 5 tags
                properties["Tags"] = {"multi_select": tag_objects}
            
            # Add Estimated Time if provided
            if quest_data.get("estimated_time"):
                properties["Estimated Time"] = {"rich_text": [{"text": {"content": quest_data["estimated_time"]}}]}
            
            return await self._retry_operation(
                self.client.pages.create,
                parent={"database_id": self.quest_db},
                properties=properties
            )
            
        except Exception as e:
            logger.error(f"Error creating quest for user {user_id}: {e}")
            return None

    async def create_comprehensive_quests(self, user_id: int, level: int = 1):
        """Create comprehensive quests using the new quest data system"""
        import random
        
        def calculate_rewards(difficulty: str, level: int) -> dict:
            """Calculate XP and rune rewards using the new formula system"""
            formula = REWARD_FORMULAS.get(difficulty, REWARD_FORMULAS["Easy"])
            
            if difficulty == "Side":
                base_xp = random.randint(formula["xp_base_min"], formula["xp_base_max"])
                xp_reward = int(base_xp * (1 + formula["xp_scaling"] * level))
                rune_reward = random.randint(formula["runes_min"], formula["runes_max"])
            else:
                xp_reward = int(formula["xp_base"] * (1 + formula["xp_scaling"] * level))
                rune_reward = formula["runes"]
            
            return {"xp": xp_reward, "runes": rune_reward}
        
        def get_level_distribution(level: int) -> tuple:
            """Get quest distribution based on user level"""
            for tier_name, tier_data in LEVEL_QUEST_DISTRIBUTION.items():
                min_level, max_level = tier_data["levels"]
                if min_level <= level <= max_level:
                    distribution = tier_data["distribution"]
                    side_quests = tier_data["side_quests"]
                    if isinstance(side_quests, tuple):
                        side_quest_count = random.randint(side_quests[0], side_quests[1])
                    else:
                        side_quest_count = side_quests
                    return distribution, side_quest_count
            
            # Fallback to master level
            master_data = LEVEL_QUEST_DISTRIBUTION["master"]
            return master_data["distribution"], random.randint(2, 3)
        
        # Get quest distribution for current level
        difficulty_distribution, side_quest_count = get_level_distribution(level)
        
        # Main categories for daily quests
        main_categories = ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"]
        
        daily_quests = []
        
        # Select main quests based on level distribution
        for i, (category, difficulty) in enumerate(zip(main_categories, difficulty_distribution)):
            if category in QUEST_DATABASE and difficulty in QUEST_DATABASE[category]:
                available_quests = QUEST_DATABASE[category][difficulty]
                if available_quests:
                    quest_template = random.choice(available_quests)
                    rewards = calculate_rewards(difficulty, level)
                    
                    quest_data = {
                        **quest_template,
                        "xp_reward": rewards["xp"],
                        "rune_reward": rewards["runes"],
                        "category": f"{category} - {difficulty}",
                        "difficulty": difficulty,
                        "quest_type": "daily",
                        "user_level_at_creation": level,
                        "tags": quest_template.get("tags", []),
                        "estimated_time": quest_template.get("estimated_time", "Unknown")
                    }
                    daily_quests.append(quest_data)
        
        # Add side quests
        side_quests_pool = QUEST_DATABASE["🌟 Side Quests"]["Side"]
        selected_side_quests = random.sample(
            side_quests_pool, 
            min(side_quest_count, len(side_quests_pool))
        )
        
        for side_quest in selected_side_quests:
            rewards = calculate_rewards("Side", level)
            
            quest_data = {
                **side_quest,
                "xp_reward": rewards["xp"],
                "rune_reward": rewards["runes"],
                "category": "🌟 Side Quest",
                "difficulty": "Side",
                "quest_type": "daily",
                "user_level_at_creation": level,
                "tags": side_quest.get("tags", []),
                "estimated_time": side_quest.get("estimated_time", "Unknown")
            }
            daily_quests.append(quest_data)
        
        # Create quests in Notion
        created_quests = []
        for quest_data in daily_quests:
            result = await self.create_quest(user_id, quest_data)
            if result:
                created_quests.append(result)
                logger.info(f"Created quest '{quest_data['name']}' for user {user_id} (Level {level}, {quest_data['difficulty']})")
            else:
                logger.warning(f"Failed to create quest '{quest_data['name']}' for user {user_id}")
        
        logger.info(
            f"Successfully created {len(created_quests)}/{len(daily_quests)} quests for user {user_id} "
            f"(Level {level}): {len([q for q in daily_quests if q['difficulty'] != 'Side'])} main + "
            f"{len([q for q in daily_quests if q['difficulty'] == 'Side'])} side quests"
        )
        
        return created_quests
    
    async def create_side_quest_if_needed(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Create a side quest if conditions are met"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return None
            
            level = user["properties"].get("Level", {}).get("number", 1)
            
            # Get last side quest date
            last_side_quest_date = None
            recent_quests = await self.get_recent_quests(user_id, days=7)
            
            for quest in recent_quests:
                category = quest.get("properties", {}).get("Category", {}).get("select", {}).get("name", "")
                if "Side Quest" in category:
                    created_date = quest.get("properties", {}).get("Created", {}).get("date", {}).get("start")
                    if created_date:
                        try:
                            last_side_quest_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                            break
                        except (ValueError, TypeError):
                            continue
            
            # Check if side quest should be triggered
            if quest_manager.should_trigger_side_quest(level, last_side_quest_date):
                # Select random side quest
                side_quests_pool = QUEST_DATABASE["🌟 Side Quests"]["Side"]
                side_quest = random.choice(side_quests_pool)
                
                # Calculate rewards
                import random
                formula = REWARD_FORMULAS["Side"]
                base_xp = random.randint(formula["xp_base_min"], formula["xp_base_max"])
                xp_reward = int(base_xp * (1 + formula["xp_scaling"] * level))
                rune_reward = random.randint(formula["runes_min"], formula["runes_max"])
                
                quest_data = {
                    **side_quest,
                    "xp_reward": xp_reward,
                    "rune_reward": rune_reward,
                    "category": "🌟 Side Quest",
                    "difficulty": "Side",
                    "quest_type": "side",
                    "user_level_at_creation": level,
                    "tags": side_quest.get("tags", []),
                    "estimated_time": side_quest.get("estimated_time", "Unknown")
                }
                
                result = await self.create_quest(user_id, quest_data)
                if result:
                    logger.info(f"Triggered side quest '{side_quest['name']}' for user {user_id}")
                    return quest_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking/creating side quest for user {user_id}: {e}")
            return None
    
    async def get_recent_quests(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent quests for a user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Try multiple property names for user filtering
            user_properties = ["User ID", "User", "Assigned To", "Player"]
            
            for prop in user_properties:
                try:
                    response = await self._retry_operation(
                        self.client.databases.query,
                        database_id=self.quest_db,
                        filter={
                            "and": [
                                {
                                    "property": prop,
                                    "number": {"equals": user_id}
                                },
                                {
                                    "property": "Created",
                                    "date": {"after": cutoff_date.isoformat()}
                                }
                            ]
                        },
                        sorts=[
                            {
                                "property": "Created",
                                "direction": "descending"
                            }
                        ]
                    )
                    
                    if response.get("results"):
                        return response["results"]
                        
                except Exception:
                    continue
            
            # Fallback: get all recent quests and filter by user
            response = await self._retry_operation(
                self.client.databases.query,
                database_id=self.quest_db,
                filter={
                    "property": "Created",
                    "date": {"after": cutoff_date.isoformat()}
                },
                sorts=[
                    {
                        "property": "Created",
                        "direction": "descending"
                    }
                ]
            )
            
            # Filter by user ID
            user_quests = []
            for quest in response.get("results", []):
                quest_user_id = None
                for prop in user_properties:
                    if prop in quest.get("properties", {}):
                        quest_user_id = quest["properties"][prop].get("number")
                        if quest_user_id == user_id:
                            user_quests.append(quest)
                            break
            
            return user_quests
            
        except Exception as e:
            logger.error(f"Error getting recent quests for user {user_id}: {e}")
            return []
    
    async def get_quest_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get quest completion analytics for a user"""
        try:
            recent_quests = await self.get_recent_quests(user_id, days)
            
            # Transform quest data for analytics
            completion_history = []
            for quest in recent_quests:
                props = quest.get("properties", {})
                
                # Extract quest data
                status = props.get("Status", {}).get("select", {}).get("name", "Unknown")
                category = props.get("Category", {}).get("select", {}).get("name", "Unknown")
                difficulty = props.get("Difficulty", {}).get("select", {}).get("name", "Unknown")
                
                completion_history.append({
                    "status": status,
                    "category": category,
                    "difficulty": difficulty,
                    "quest_id": quest.get("id", "")
                })
            
            return quest_manager.get_quest_analytics(completion_history)
            
        except Exception as e:
            logger.error(f"Error getting quest analytics for user {user_id}: {e}")
            return {"error": f"Failed to get analytics: {e}"}
    
    async def create_adaptive_quests(self, user_id: int, level: int = 1) -> List[Dict[str, Any]]:
        """Create quests using adaptive selection based on user history"""
        try:
            # Get user's completion history
            completion_history = []
            recent_quests = await self.get_recent_quests(user_id, days=30)
            
            for quest in recent_quests:
                props = quest.get("properties", {})
                completion_history.append({
                    "status": props.get("Status", {}).get("select", {}).get("name", "Unknown"),
                    "category": props.get("Category", {}).get("select", {}).get("name", "Unknown"),
                    "difficulty": props.get("Difficulty", {}).get("select", {}).get("name", "Unknown")
                })
            
            # Get recommended quests using adaptive strategy
            recommended_quests = quest_manager.get_recommended_daily_quests(
                user_level=level,
                strategy=QuestSelectionStrategy.ADAPTIVE,
                completion_history=completion_history
            )
            
            # Create quests in Notion
            created_quests = []
            for quest_data in recommended_quests:
                result = await self.create_quest(user_id, quest_data)
                if result:
                    created_quests.append(result)
                    logger.info(f"Created adaptive quest '{quest_data['name']}' for user {user_id}")
            
            logger.info(f"Created {len(created_quests)} adaptive quests for user {user_id}")
            return created_quests
            
        except Exception as e:
            logger.error(f"Error creating adaptive quests for user {user_id}: {e}")
            # Fallback to regular quest creation
            return await self.create_comprehensive_quests(user_id, level)
    
    async def get_active_buffs(self, user_id: int) -> List[Buff]:
        """Get active buffs for a user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return []
            
            buff_data = user["properties"].get("Active Buffs", {}).get("multi_select", [])
            active_buffs = []
            
            for buff_entry in buff_data:
                buff_name = buff_entry.get("name", "")
                # Parse buff data (assuming format: "name|effect|duration|applied_date")
                if "|" in buff_name:
                    parts = buff_name.split("|")
                    if len(parts) >= 4:
                        try:
                            effect_value = float(parts[1])
                            duration = int(parts[2])
                            applied_date = datetime.fromisoformat(parts[3])
                            
                            # Find matching buff template
                            for buff_id, buff_template in GamificationEngine.BUFF_CATALOG.items():
                                if buff_template.name in parts[0]:
                                    buff = Buff(
                                        buff_template.buff_type,
                                        buff_template.name,
                                        buff_template.description,
                                        effect_value,
                                        duration,
                                        applied_date
                                    )
                                    if buff.is_active():
                                        active_buffs.append(buff)
                                    break
                        except (ValueError, TypeError):
                            continue
            
            return active_buffs
            
        except Exception as e:
            logger.error(f"Error getting active buffs for user {user_id}: {e}")
            return []
    
    async def get_active_debuffs(self, user_id: int) -> List[Debuff]:
        """Get active debuffs for a user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return []
            
            debuff_data = user["properties"].get("Active Debuffs", {}).get("multi_select", [])
            active_debuffs = []
            
            for debuff_entry in debuff_data:
                debuff_name = debuff_entry.get("name", "")
                # Parse debuff data (assuming format: "name|effect|duration|applied_date")
                if "|" in debuff_name:
                    parts = debuff_name.split("|")
                    if len(parts) >= 4:
                        try:
                            effect_value = float(parts[1])
                            duration = int(parts[2])
                            applied_date = datetime.fromisoformat(parts[3])
                            
                            # Find matching debuff template
                            for debuff_id, debuff_template in GamificationEngine.DEBUFF_CATALOG.items():
                                if debuff_template.name in parts[0]:
                                    debuff = Debuff(
                                        debuff_template.debuff_type,
                                        debuff_template.name,
                                        debuff_template.description,
                                        effect_value,
                                        duration,
                                        applied_date
                                    )
                                    if debuff.is_active():
                                        active_debuffs.append(debuff)
                                    break
                        except (ValueError, TypeError):
                            continue
            
            return active_debuffs
            
        except Exception as e:
            logger.error(f"Error getting active debuffs for user {user_id}: {e}")
            return []
    
    async def apply_buff(self, user_id: int, buff: Buff) -> bool:
        """Apply a buff to a user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # Get current buffs
            current_buffs = user["properties"].get("Active Buffs", {}).get("multi_select", [])
            buff_names = [buff_entry["name"] for buff_entry in current_buffs]
            
            # Format: "name|effect|duration|applied_date"
            buff_string = f"{buff.name}|{buff.effect_value}|{buff.duration_days}|{buff.applied_date.isoformat()}"
            
            # Avoid duplicate buffs
            if not any(buff.name in name for name in buff_names):
                buff_names.append(buff_string)
                
                await self._retry_operation(
                    self.client.pages.update,
                    page_id=user["id"],
                    properties={
                        "Active Buffs": {"multi_select": [{"name": name} for name in buff_names[-5:]]}  # Keep only 5 most recent
                    }
                )
                
                logger.info(f"Applied buff '{buff.name}' to user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying buff to user {user_id}: {e}")
            return False
    
    async def apply_debuff(self, user_id: int, debuff: Debuff) -> bool:
        """Apply a debuff to a user with buff shield check"""
        try:
            # Check for debuff shields
            active_buffs = await self.get_active_buffs(user_id)
            if GamificationEngine.should_apply_debuff_shield(active_buffs, debuff):
                # Consume debuff shield
                await self.consume_debuff_shield(user_id)
                logger.info(f"Debuff '{debuff.name}' blocked by shield for user {user_id}")
                return False
            
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # Get current debuffs
            current_debuffs = user["properties"].get("Active Debuffs", {}).get("multi_select", [])
            debuff_names = [debuff_entry["name"] for debuff_entry in current_debuffs]
            
            # Format: "name|effect|duration|applied_date"
            debuff_string = f"{debuff.name}|{debuff.effect_value}|{debuff.duration_days}|{debuff.applied_date.isoformat()}"
            
            # Avoid duplicate debuffs
            if not any(debuff.name in name for name in debuff_names):
                debuff_names.append(debuff_string)
                
                await self._retry_operation(
                    self.client.pages.update,
                    page_id=user["id"],
                    properties={
                        "Active Debuffs": {"multi_select": [{"name": name} for name in debuff_names[-5:]]}  # Keep only 5 most recent
                    }
                )
                
                logger.info(f"Applied debuff '{debuff.name}' to user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying debuff to user {user_id}: {e}")
            return False
    
    async def consume_debuff_shield(self, user_id: int) -> bool:
        """Remove one debuff shield buff from user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            current_buffs = user["properties"].get("Active Buffs", {}).get("multi_select", [])
            updated_buffs = []
            shield_consumed = False
            
            for buff_entry in current_buffs:
                buff_name = buff_entry["name"]
                if "Debuff Shield" in buff_name and not shield_consumed:
                    shield_consumed = True
                    continue  # Skip this buff (consume it)
                updated_buffs.append(buff_entry)
            
            if shield_consumed:
                await self._retry_operation(
                    self.client.pages.update,
                    page_id=user["id"],
                    properties={
                        "Active Buffs": {"multi_select": updated_buffs}
                    }
                )
                logger.info(f"Consumed debuff shield for user {user_id}")
            
            return shield_consumed
            
        except Exception as e:
            logger.error(f"Error consuming debuff shield for user {user_id}: {e}")
            return False
    
    async def check_and_award_trophies(self, user_id: int) -> List[Trophy]:
        """Check for and award new trophies"""
        try:
            # Get comprehensive user stats
            user_stats = await self.get_comprehensive_user_stats(user_id)
            
            # Check eligibility
            eligible_trophies = GamificationEngine.check_trophy_eligibility(user_stats)
            
            # Get existing trophies
            existing_trophies = await self.get_user_trophies(user_id)
            existing_trophy_ids = [trophy.trophy_id for trophy in existing_trophies]
            
            # Award new trophies
            new_trophies = []
            for trophy in eligible_trophies:
                if trophy.trophy_id not in existing_trophy_ids:
                    success = await self.award_trophy(user_id, trophy)
                    if success:
                        new_trophies.append(trophy)
            
            return new_trophies
            
        except Exception as e:
            logger.error(f"Error checking trophies for user {user_id}: {e}")
            return []
    
    async def award_trophy(self, user_id: int, trophy: Trophy) -> bool:
        """Award a trophy to user's inventory"""
        try:
            trophy_data = {
                "name": f"{trophy.emoji} {trophy.name}",
                "type": "Trophy",
                "rarity": "Legendary",
                "description": trophy.description,
                "price": 0,
                "effect": f"Achievement: {trophy.requirement}"
            }
            
            result = await self.add_item_to_inventory(user_id, trophy_data)
            if result:
                logger.info(f"Awarded trophy '{trophy.name}' to user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error awarding trophy to user {user_id}: {e}")
            return False
    
    async def award_title_buff(self, user_id: int, title: Title) -> bool:
        """Award special buff for earning a new title"""
        try:
            if title.anti_debuff_perk:
                # Award a special buff based on the title
                if "Immune to Sluggish" in title.anti_debuff_perk:
                    buff = GamificationEngine.BUFF_CATALOG["debuff_shield"]
                elif "Reduces debuff duration" in title.anti_debuff_perk:
                    buff = GamificationEngine.BUFF_CATALOG["focused_mind"]
                else:
                    buff = GamificationEngine.BUFF_CATALOG["streak_guardian"]
                
                buff.applied_date = datetime.now()
                return await self.apply_buff(user_id, buff)
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding title buff for user {user_id}: {e}")
            return False
    
    async def get_comprehensive_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics for trophy checking"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return {}
            
            props = user["properties"]
            
            # Get quest completion stats
            recent_quests = await self.get_recent_quests(user_id, days=365)  # Last year
            completed_quests = len([q for q in recent_quests if q.get("properties", {}).get("Status", {}).get("select", {}).get("name") == "Completed"])
            
            return {
                "level": props.get("Level", {}).get("number", 1),
                "xp": props.get("XP", {}).get("number", 0),
                "runes": props.get("Runes", {}).get("number", 0),
                "streak": props.get("Streak", {}).get("number", 0),
                "max_streak": props.get("Max Streak", {}).get("number", 0),
                "total_quests_completed": completed_quests,
                "total_runes_earned": props.get("Runes", {}).get("number", 0)  # This could be tracked separately
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive stats for user {user_id}: {e}")
            return {}
    
    async def get_user_trophies(self, user_id: int) -> List[Trophy]:
        """Get user's existing trophies"""
        try:
            items = await self.get_inventory(user_id)
            trophies = []
            
            for item_data in items:
                item_type = item_data.get("properties", {}).get("Type", {}).get("select", {}).get("name", "")
                if item_type == "Trophy":
                    name = item_data.get("properties", {}).get("Item Name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
                    description = item_data.get("properties", {}).get("Description", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
                    
                    # Extract trophy ID from name or description
                    trophy_id = name.lower().replace(" ", "_").replace("🏆", "").replace("👑", "").replace("🔥", "").strip()
                    
                    trophy = Trophy(
                        trophy_id=trophy_id,
                        name=name,
                        description=description,
                        emoji="🏆",
                        requirement="Unknown"
                    )
                    trophies.append(trophy)
            
            return trophies
            
        except Exception as e:
            logger.error(f"Error getting trophies for user {user_id}: {e}")
            return []

    async def create_default_quests(self, user_id: int):
        """Override to use comprehensive quest system"""
        user = await self.get_user(user_id)
        level = user["properties"].get("Level", {}).get("number", 1) if user else 1
        return await self.create_comprehensive_quests(user_id, level)

    async def complete_quest(self, quest_id: str):
        """Complete a quest with robust property handling"""
        try:
            quest = await self.client.pages.retrieve(page_id=quest_id)
            if not quest:
                return None
            
            # Extract rewards and user ID with fallback handling
            xp_reward = 0
            user_id = None
            
            # Try multiple property names for XP reward
            xp_properties = ["XP Reward", "XP", "Experience", "Experience Points"]
            for prop in xp_properties:
                if prop in quest["properties"] and quest["properties"][prop].get("number"):
                    xp_reward = quest["properties"][prop]["number"]
                    break
            
            # Try multiple property names for user ID
            user_properties = ["User ID", "User", "Assigned To", "Player"]
            for prop in user_properties:
                if prop in quest["properties"] and quest["properties"][prop].get("number"):
                    user_id = quest["properties"][prop]["number"]
                    break
            
            # Try to get rune reward
            rune_reward = 0
            rune_properties = ["Rune Reward", "Runes", "Currency", "Gold"]
            for prop in rune_properties:
                if prop in quest["properties"] and quest["properties"][prop].get("number"):
                    rune_reward = quest["properties"][prop]["number"]
                    break
            
            if not xp_reward:
                xp_reward = 50  # Default XP
            
            if not rune_reward:
                rune_reward = xp_reward // 10  # Default rune calculation
            
            # Update quest status
            await self.client.pages.update(
                page_id=quest_id,
                properties={
                    "Status": {"select": {"name": "Completed"}},
                    "Completed": {"date": {"start": datetime.now().isoformat()}}
                }
            )
            
            # Update user stats
            if user_id:
                await self.update_user_xp(user_id, xp_reward)
                if rune_reward > 0:
                    await self.update_user_runes(user_id, rune_reward)
                await self.update_streak(user_id)
            
            # Get quest name for response
            quest_name = "Quest"
            try:
                name_properties = ["Quest Name", "Name", "Title"]
                for prop in name_properties:
                    if prop in quest["properties"] and quest["properties"][prop].get("title"):
                        quest_name = quest["properties"][prop]["title"][0]["text"]["content"]
                        break
            except Exception:
                pass
            
            return {
                "xp": xp_reward,
                "runes": rune_reward,
                "name": quest_name,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error completing quest {quest_id}: {e}")
            return None

    async def get_inventory(self, user_id: int):
        res = await self.client.databases.query(
            database_id=self.inventory_db,
            filter={"property": "User ID", "number": {"equals": user_id}}
        )
        return res["results"]

    async def add_item_to_inventory(self, user_id: int, item_data: dict):
        existing = await self.client.databases.query(
            database_id=self.inventory_db,
            filter={
                "and": [
                    {"property": "User ID", "number": {"equals": user_id}},
                    {"property": "Item Name", "title": {"equals": item_data.get("name", "")}}
                ]
            }
        )
        if existing.get("results"):
            item = existing["results"][0]
            qty = item["properties"].get("Quantity", {}).get("number") or 0
            return await self.client.pages.update(
                page_id=item["id"],
                properties={"Quantity": {"number": qty + 1}}
            )
        return await self.client.pages.create(
            parent={"database_id": self.inventory_db},
            properties={
                "Item Name": {"title": [{"text": {"content": item_data.get("name", "Item")}}]},
                "User ID": {"number": user_id},
                "Type": {"select": {"name": item_data.get("type", "Consumable")}},
                "Rarity": {"select": {"name": item_data.get("rarity", "Common")}},
                "Description": {"rich_text": [{"text": {"content": item_data.get("description", "")}}]},
                "Quantity": {"number": 1},
                "Price": {"number": item_data.get("price", 0)},
                "Effect": {"rich_text": [{"text": {"content": item_data.get("effect", "")}}]},
                "Acquired": {"date": {"start": datetime.now().isoformat()}}
            }
        )

    async def get_item(self, item_id: str):
        return await self.client.pages.retrieve(page_id=item_id)

    async def update_item_quantity(self, item_id: str, new_quantity: int):
        if new_quantity > 0:
            return await self.client.pages.update(
                page_id=item_id,
                properties={"Quantity": {"number": new_quantity}}
            )
        else:
            return await self.client.pages.update(page_id=item_id, archived=True)

    async def close(self):
        """Close the Notion client with proper cleanup"""
        try:
            if hasattr(self.client, 'aclose'):
                await self.client.aclose()
            logger.info("Notion client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Notion client: {e}")

    async def update_quest_status(self, quest_id: str, status: str):
        """Update the status of a quest"""
        try:
            url = f"{self.base_url}/pages/{quest_id}"
            
            # Try different property names for status
            status_properties = ["Status", "status", "Status"]
            
            for prop_name in status_properties:
                data = {
                    "properties": {
                        prop_name: {
                            "select": {
                                "name": status.title() if status.lower() in ["active", "completed", "archived"] else status
                            }
                        }
                    }
                }
                
                response = requests.patch(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating quest status: {e}")
            return False