#!/usr/bin/env python3
"""
Development test script for XP Telegram Bot

This script helps validate the bot setup and configuration
before running the main application.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.config import config
    from src.notion.notion_client import NotionClient
    from src.exceptions import ConfigurationError
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

async def test_configuration():
    """Test configuration and environment variables"""
    print("🔧 Testing configuration...")
    
    try:
        print(f"✅ Bot token: {'Set' if config.bot_token else 'Missing'}")
        print(f"✅ Notion token: {'Set' if config.notion_token else 'Missing'}")
        print(f"✅ XP DB ID: {'Set' if config.xp_db_id else 'Missing'}")
        print(f"✅ Quest DB ID: {'Set' if config.quest_db_id else 'Missing'}")
        print(f"✅ Challenge DB ID: {'Set' if config.challenge_db_id else 'Missing'}")
        print(f"✅ Inventory DB ID: {'Set' if config.inventory_db_id else 'Missing'}")
        print(f"✅ Debug mode: {config.debug}")
        print(f"✅ Log level: {config.log_level}")
        return True
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return False

async def test_notion_connection():
    """Test Notion API connection"""
    print("\n🔗 Testing Notion connection...")
    
    try:
        notion_client = NotionClient()
        await notion_client.test_connection()
        print("✅ Notion API connection successful")
        await notion_client.close()
        return True
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False

async def test_imports():
    """Test all critical imports"""
    print("\n📦 Testing imports...")
    
    try:
        from aiogram import Bot, Dispatcher
        print("✅ Aiogram imported successfully")
        
        from notion_client import AsyncClient
        print("✅ Notion client imported successfully")
        
        from src.handlers import start, dashboard, quests, inventory, shop
        print("✅ All handlers imported successfully")
        
        from src.models import user, quest, item
        print("✅ All models imported successfully")
        
        from src.utils import calculators, formatters
        print("✅ All utilities imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        ".env",
        "requirements.txt",
        "bot.py",
        "src/__init__.py",
        "src/config.py",
        "src/exceptions.py",
        "src/handlers/__init__.py",
        "src/handlers/start.py",
        "src/handlers/dashboard.py",
        "src/handlers/quests.py",
        "src/handlers/inventory.py",
        "src/handlers/shop.py",
        "src/models/__init__.py",
        "src/models/user.py",
        "src/models/quest.py",
        "src/models/item.py",
        "src/notion/notion_client.py",
        "src/utils/__init__.py",
        "src/utils/calculators.py",
        "src/utils/formatters.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files found")
        return True

async def run_all_tests():
    """Run all tests and report results"""
    print("🚀 XP Telegram Bot - Development Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Configuration", test_configuration),
        ("Imports", test_imports),
        ("Notion Connection", test_notion_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your bot is ready to run.")
        print("Run the bot with: python bot.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)