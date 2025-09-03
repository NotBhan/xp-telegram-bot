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