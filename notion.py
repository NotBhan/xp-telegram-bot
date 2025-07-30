from notion_client import Client
from config import NOTION_TOKEN, XP_DB_ID, QUEST_DB_ID, INVENTORY_DB_ID, DEBUFF_DB_ID

notion = Client(auth=NOTION_TOKEN)

def get_user_entry(user_id):
    results = notion.databases.query(
        database_id=XP_DB_ID,
        filter={"property": "UserID", "rich_text": {"equals": str(user_id)}}
    )
    return results["results"][0] if results["results"] else None

def update_xp(user_page_id, new_xp):
    notion.pages.update(user_page_id, properties={
        "XP": {"number": new_xp}
    })

def update_level(user_page_id, new_level):
    notion.pages.update(user_page_id, properties={
        "Level": {"number": new_level}
    })

def log_quest(user_page_id, title, difficulty, xp, runes):
    notion.pages.create(parent={"database_id": QUEST_DB_ID}, properties={
        "Title": {"title": [{"text": {"content": title}}]},
        "Difficulty": {"select": {"name": difficulty}},
        "XP": {"number": xp},
        "Runes": {"number": runes},
        "Player": {"relation": [{"id": user_page_id}]}
    })

def update_inventory(user_page_id, item, quantity):
    notion.pages.create(parent={"database_id": INVENTORY_DB_ID}, properties={
        "Title": {"title": [{"text": {"content": item}}]},
        "Player": {"relation": [{"id": user_page_id}]},
        "Quantity": {"number": quantity}
    })
