#!/usr/bin/env python3
"""
Enhanced Streaks, Buffs, and Debuffs System Demo

This script demonstrates the complete enhanced gamification system with
streaks, buffs, debuffs, and dashboard integration according to specification.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine, Buff, Debuff, BuffType, DebuffType

def demo_streak_progression():
    """Demonstrate streak progression and milestone rewards"""
    print("🔥 STREAK SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    print("Simulating a user's streak progression over time...")
    print()
    
    # Simulate daily quest completions
    scenarios = [
        (1, "First quest ever"),
        (7, "One week milestone"),
        (14, "Two week milestone"),
        (30, "One month milestone - Title unlock"),
        (90, "Three month milestone - Buff unlock"),
    ]
    
    for days, description in scenarios:
        bonuses = GamificationEngine.calculate_streak_bonus(days)
        
        print(f"📅 Day {days}: {description}")
        print(f"   💎 Runes earned: {bonuses['runes']}")
        
        if bonuses['titles_unlocked']:
            print(f"   🏅 Title unlocked: {bonuses['titles_unlocked'][0]}")
        
        if bonuses['buffs_unlocked']:
            print(f"   ✨ Buff unlocked: {bonuses['buffs_unlocked'][0]}")
        
        print()
    
    print("🎯 Streak system encourages daily consistency with meaningful rewards!")
    print()

def demo_buff_system():
    """Demonstrate the buff system"""
    print("✨ BUFF SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    print("Available buffs (earned only, cannot be purchased):")
    print()
    
    for buff_id, buff in GamificationEngine.BUFF_CATALOG.items():
        duration_text = "Permanent" if buff.duration_days == float('inf') else f"{buff.duration_days} days"
        print(f"🌟 {buff.name}")
        print(f"   Effect: {buff.description}")
        print(f"   Duration: {duration_text}")
        print(f"   Type: {buff.buff_type.value}")
        print()
    
    print("💡 Buffs represent permanent, passive boosts tied to milestones!")
    print()

def demo_dashboard_display():
    """Demonstrate the enhanced dashboard display"""
    print("📊 DASHBOARD INTEGRATION DEMONSTRATION")
    print("=" * 60)
    
    print("Example dashboard display with streaks, buffs, and debuffs:")
    print()
    
    # Create sample active effects
    active_buffs = [
        Buff(BuffType.XP_BOOST, "Focused Mind", "+10% XP gain", 0.10, float('inf'), datetime.now()),
        Buff(BuffType.RUNE_BOOST, "Rune Magnet", "+5 Runes per quest", 5.0, float('inf'), datetime.now())
    ]
    
    active_debuffs = [
        Debuff(DebuffType.XP_REDUCTION, "Shadow State", "-20% XP gain", 0.20, 2, datetime.now() - timedelta(days=1))
    ]
    
    dashboard = GamificationEngine.format_dashboard_status(
        level=12,
        xp=45,
        xp_needed=105,  # Level 12 needs 300 XP, user has 45
        streak=18,
        runes=275,
        title="Sound Sculptor",
        active_buffs=active_buffs,
        active_debuffs=active_debuffs
    )
    
    print(dashboard)
    print()
    print("🎆 Dashboard shows comprehensive gamification status at a glance!")
    print()

def main():
    """Run the complete demonstration"""
    print("🎮 ENHANCED STREAKS, BUFFS, AND DEBUFFS SYSTEM")
    print("="*70)
    print("Live demonstration of the implemented specification")
    print("="*70)
    print()
    
    demo_streak_progression()
    demo_buff_system()
    demo_dashboard_display()
    
    print("🎆 DEMONSTRATION COMPLETE")
    print("="*70)
    print("🚀 The enhanced gamification system creates an RPG-like experience:")
    print("• 🔥 Streaks encourage daily consistency")
    print("• ✨ Buffs reward long-term mastery and milestones")
    print("• ☠️ Debuffs create accountability and increase stakes")
    print("• 📊 Dashboard provides comprehensive status display")
    print()
    print("🎯 Result: Productivity feels like an engaging RPG adventure!")

if __name__ == "__main__":
    main()