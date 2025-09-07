from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

class ItemType(Enum):
    CONSUMABLE = "Consumable"
    EQUIPMENT = "Equipment"
    COSMETIC = "Cosmetic"
    BOOST = "Boost"
    MATERIAL = "Material"

class ItemRarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"

@dataclass
class Item:
    item_id: str
    user_id: int
    name: str
    type: ItemType
    rarity: ItemRarity
    description: str
    quantity: int = 1
    acquired_at: datetime = None
    used: bool = False
    used_at: Optional[datetime] = None
    effect_description: str = ""
    price: int = 0

    def __post_init__(self):
        if self.acquired_at is None:
            self.acquired_at = datetime.now()

    def use(self) -> dict:
        """Use the item"""
        if self.used:
            return {"success": False, "message": "Item already used"}
        
        if self.quantity <= 0:
            return {"success": False, "message": "No items left"}
        
        self.used = True
        self.used_at = datetime.now()
        self.quantity -= 1
        
        return {
            "success": True,
            "message": f"Used {self.name}",
            "effect": self.effect_description
        }

    def get_rarity_emoji(self) -> str:
        """Get emoji for rarity"""
        rarity_emojis = {
            ItemRarity.COMMON: "⚪",
            ItemRarity.UNCOMMON: "🟢",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡"
        }
        return rarity_emojis.get(self.rarity, "⚪")

    def get_type_emoji(self) -> str:
        """Get emoji for type"""
        type_emojis = {
            ItemType.CONSUMABLE: "🧪",
            ItemType.EQUIPMENT: "⚔️",
            ItemType.COSMETIC: "🎨",
            ItemType.BOOST: "⚡",
            ItemType.MATERIAL: "📦"
        }
        return type_emojis.get(self.type, "📦")

    def get_display_name(self) -> str:
        """Get formatted display name"""
        return f"{self.get_rarity_emoji()}{self.get_type_emoji()} {self.name}"

    def is_available(self) -> bool:
        """Check if item is available for use"""
        return not self.used and self.quantity > 0

    def get_stack_info(self) -> str:
        """Get stack information"""
        if self.quantity > 1:
            return f"x{self.quantity}"
        return ""

    def get_price_display(self) -> str:
        """Get formatted price"""
        return f"{self.price} 💎"

    @classmethod
    def from_notion(cls, notion_data: dict) -> 'Item':
        """Create Item from Notion database entry"""
        try:
            properties = notion_data.get("properties", {})
            
            # Extract basic properties with safe defaults
            item_id = notion_data.get("id", "")
            
            # Extract user ID
            user_id = 0
            if "User ID" in properties:
                user_id = properties["User ID"].get("number", 0)
            
            # Extract name
            name = "Unknown Item"
            if "Item Name" in properties and properties["Item Name"].get("title"):
                name = properties["Item Name"]["title"][0]["text"]["content"]
            elif "Name" in properties and properties["Name"].get("title"):
                name = properties["Name"]["title"][0]["text"]["content"]
            
            # Extract type
            item_type = ItemType.CONSUMABLE
            if "Type" in properties and properties["Type"].get("select"):
                type_name = properties["Type"]["select"]["name"]
                try:
                    item_type = ItemType(type_name)
                except ValueError:
                    item_type = ItemType.CONSUMABLE
            
            # Extract rarity
            rarity = ItemRarity.COMMON
            if "Rarity" in properties and properties["Rarity"].get("select"):
                rarity_name = properties["Rarity"]["select"]["name"]
                try:
                    rarity = ItemRarity(rarity_name)
                except ValueError:
                    rarity = ItemRarity.COMMON
            
            # Extract description
            description = ""
            if "Description" in properties and properties["Description"].get("rich_text"):
                description = properties["Description"]["rich_text"][0]["text"]["content"]
            
            # Extract quantity
            quantity = 1
            if "Quantity" in properties:
                quantity = properties["Quantity"].get("number", 1)
            
            # Extract price
            price = 0
            if "Price" in properties:
                price = properties["Price"].get("number", 0)
            
            # Extract effect description
            effect_description = ""
            if "Effect" in properties and properties["Effect"].get("rich_text"):
                effect_description = properties["Effect"]["rich_text"][0]["text"]["content"]
            
            # Extract acquired date
            acquired_at = datetime.now()
            if "Acquired" in properties and properties["Acquired"].get("date"):
                try:
                    date_str = properties["Acquired"]["date"]["start"]
                    acquired_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    acquired_at = datetime.now()
            
            return cls(
                item_id=item_id,
                user_id=user_id,
                name=name,
                type=item_type,
                rarity=rarity,
                description=description,
                quantity=quantity,
                acquired_at=acquired_at,
                effect_description=effect_description,
                price=price
            )
            
        except Exception as e:
            # Return a default item on error
            return cls(
                item_id=notion_data.get("id", ""),
                user_id=0,
                name="Unknown Item",
                type=ItemType.CONSUMABLE,
                rarity=ItemRarity.COMMON,
                description="An unknown item",
                quantity=1
            )