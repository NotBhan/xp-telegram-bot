import os
import logging
from datetime import datetime, timedelta
from notion_client import AsyncClient

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self):
        self.client = AsyncClient(auth=os.getenv('NOTION_TOKEN'))
        self.xp_db = os.getenv('XP_DB_ID')
        self.quest_db = os.getenv('QUEST_DB_ID')
        self.inventory_db = os.getenv('INVENTORY_DB_ID')

    async def create_user(self, user_id, username, name):
        return await self.client.pages.create(
            parent={"database_id": self.xp_db},
            properties={
                "User ID": {"number": user_id},
                "Username": {"title": [{"text": {"content": username}}]},
                "First Name": {"rich_text": [{"text": {"content": name}}]},
                "XP": {"number": 0},
                "Level": {"number": 1},
                "Runes": {"number": 0},
                "Last Activity": {"date": {"start": datetime.now().isoformat()}}
            }
        )

    async def get_user(self, user_id):
        res = await self.client.databases.query(
            database_id=self.xp_db,
            filter={"property": "User ID", "number": {"equals": user_id}}
        )
        return res["results"][0] if res["results"] else None

    async def update_xp(self, user_id, xp_gain):
        return await self.update_user_xp(user_id, xp_gain)

    async def update_user_xp(self, user_id, xp_gain):
        user = await self.get_user(user_id)
        if not user:
            return None
        current_xp = user["properties"].get("XP", {}).get("number") or 0
        new_xp = current_xp + xp_gain
        level = 1
        total = 0
        while total <= new_xp:
            total += level ** 2 * 100
            level += 1
        level = max(1, level - 1)
        return await self.client.pages.update(
            page_id=user["id"],
            properties={
                "XP": {"number": new_xp},
                "Level": {"number": level},
                "Last Activity": {"date": {"start": datetime.now().isoformat()}}
            }
        )

    async def update_user_runes(self, user_id, new_runes: int):
        user = await self.get_user(user_id)
        if not user:
            return None
        return await self.client.pages.update(
            page_id=user["id"],
            properties={
                "Runes": {"number": new_runes},
                "Last Activity": {"date": {"start": datetime.now().isoformat()}}
            }
        )

    async def get_quests(self, user_id):
        res = await self.client.databases.query(
            database_id=self.quest_db,
            filter={"property": "User ID", "number": {"equals": user_id}}
        )
        return res["results"]

    async def create_quest(self, user_id: int, quest_data: dict):
        return await self.client.pages.create(
            parent={"database_id": self.quest_db},
            properties={
                "Quest Name": {"title": [{"text": {"content": quest_data.get("name", "Quest")}}]},
                "User ID": {"number": user_id},
                "Description": {"rich_text": [{"text": {"content": quest_data.get("description", "")}}]},
                "XP Reward": {"number": quest_data.get("xp_reward", 50)},
                "Rune Reward": {"number": quest_data.get("xp_reward", 50) // 10},
                "Category": {"select": {"name": quest_data.get("category", "Daily")}},
                "Status": {"select": {"name": "Active"}},
                "Created": {"date": {"start": datetime.now().isoformat()}},
                "Due Date": {"date": {"start": (datetime.now() + timedelta(days=1)).isoformat()}}
            }
        )

    async def complete_quest(self, quest_id: str):
        quest = await self.client.pages.retrieve(page_id=quest_id)
        if not quest:
            return None
        xp_reward = quest["properties"].get("XP Reward", {}).get("number") or 0
        user_id = quest["properties"].get("User ID", {}).get("number")
        await self.client.pages.update(
            page_id=quest_id,
            properties={
                "Status": {"select": {"name": "Completed"}},
                "Completed": {"date": {"start": datetime.now().isoformat()}}
            }
        )
        if xp_reward and user_id:
            await self.update_user_xp(user_id, xp_reward)
        return {"xp_earned": xp_reward, "user_id": user_id}

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
        await self.client.aclose()