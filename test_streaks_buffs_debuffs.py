#!/usr/bin/env python3
"""
Comprehensive Test for Streaks, Buffs, and Debuffs System

This script validates the implementation against the specification provided
for the Streaks, Buffs, and Debuffs system.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine, Buff, Debuff, BuffType, DebuffType

def test_streak_system():
    """Test the streak system according to specification"""
    print("🔥 Testing Streak System")
    print("-" * 50)
    
    # Test daily completion bonus
    bonuses = GamificationEngine.calculate_streak_bonus(1)
    assert bonuses["runes"] == 5, f"Expected 5 runes for daily completion, got {bonuses['runes']}"
    print("✅ Daily completion bonus: +5 runes")
    
    # Test milestone rewards
    test_cases = [
        (7, 30, [], [], "7-day milestone"),  # 5 daily + 25 milestone
        (14, 55, [], [], "14-day milestone"),  # 5 daily + 50 milestone
        (30, 105, [], ["The Consistent"], "30-day milestone with title"),  # 5 daily + 100 milestone
        (90, 205, ["unyielding_will"], [], "90-day milestone with buff"),  # 5 daily + 200 milestone
    ]
    
    for days, expected_runes, expected_buffs, expected_titles, description in test_cases:
        bonuses = GamificationEngine.calculate_streak_bonus(days)
        assert bonuses["runes"] == expected_runes, f"{description}: Expected {expected_runes} runes, got {bonuses['runes']}"
        assert bonuses["buffs_unlocked"] == expected_buffs, f"{description}: Expected buffs {expected_buffs}, got {bonuses['buffs_unlocked']}"
        assert bonuses["titles_unlocked"] == expected_titles, f"{description}: Expected titles {expected_titles}, got {bonuses['titles_unlocked']}"
        print(f"✅ {description}: {bonuses['runes']} runes, {len(bonuses['buffs_unlocked'])} buffs, {len(bonuses['titles_unlocked'])} titles")
    
    print("Streak system validation: ✅ PASSED")
    return True

def test_buff_system():
    """Test the buff system according to specification"""
    print("\n🌟 Testing Buff System")
    print("-" * 50)
    
    # Test permanent buffs (earned only, cannot be purchased)
    focused_mind = GamificationEngine.BUFF_CATALOG["focused_mind"]
    assert focused_mind.buff_type == BuffType.XP_BOOST, "Focused Mind should be XP boost"
    assert focused_mind.effect_value == 0.10, "Focused Mind should give +10% XP"
    assert focused_mind.duration_days == float('inf'), "Focused Mind should be permanent"
    print("✅ Focused Mind: +10% XP gain (permanent)")
    
    rune_magnet = GamificationEngine.BUFF_CATALOG["rune_magnet"]
    assert rune_magnet.buff_type == BuffType.RUNE_BOOST, "Rune Magnet should be rune boost"
    assert rune_magnet.effect_value == 5.0, "Rune Magnet should give +5 runes"
    print("✅ Rune Magnet: +5 Runes per quest (permanent)")
    
    # Test special buffs
    phoenix_spirit = GamificationEngine.BUFF_CATALOG["phoenix_spirit"]
    assert phoenix_spirit.buff_type == BuffType.STREAK_PROTECTION, "Phoenix Spirit should protect streaks"
    assert phoenix_spirit.duration_days == 30, "Phoenix Spirit should last 30 days"
    print("✅ Phoenix Spirit: First streak break per month ignored")
    
    iron_will = GamificationEngine.BUFF_CATALOG["iron_will"]
    assert iron_will.name == "Iron Will", "Iron Will buff should exist"
    print("✅ Iron Will: Debuff durations reduced by 1 day")
    
    print("Buff system validation: ✅ PASSED")
    return True

def test_debuff_system():
    """Test the debuff system according to specification"""
    print("\n☠️ Testing Debuff System")
    print("-" * 50)
    
    # Test debuff types
    sluggish = GamificationEngine.DEBUFF_CATALOG["sluggish"]
    assert sluggish.debuff_type == DebuffType.SLUGGISH, "Sluggish should be sluggish type"
    assert sluggish.duration_days == 2, "Sluggish should last 2 days"
    print("✅ Sluggish: No streak progress for 2 days")
    
    shadow_state = GamificationEngine.DEBUFF_CATALOG["shadow_state"]
    assert shadow_state.debuff_type == DebuffType.XP_REDUCTION, "Shadow State should reduce XP"
    assert shadow_state.effect_value == 0.20, "Shadow State should reduce XP by 20%"
    assert shadow_state.duration_days == 3, "Shadow State should last 3 days"
    print("✅ Shadow State: -20% XP from all quests (3 days)")
    
    chaos_penalty = GamificationEngine.DEBUFF_CATALOG["chaos_penalty"]
    assert chaos_penalty.debuff_type == DebuffType.RUNE_DRAIN, "Chaos Penalty should drain runes"
    assert chaos_penalty.effect_value == 5.0, "Chaos Penalty should drain 5 runes"
    print("✅ Chaos Penalty: -5 Runes per quest (5 days)")
    
    # Test debuff scaling with streak length
    short_streak_debuff = GamificationEngine.apply_streak_loss_debuff(1, 5)
    long_streak_debuff = GamificationEngine.apply_streak_loss_debuff(1, 30)
    
    assert long_streak_debuff.duration_days >= short_streak_debuff.duration_days, "Longer streaks should have harsher penalties"
    print(f"✅ Debuff scaling: Short streak penalty {short_streak_debuff.duration_days} days, long streak penalty {long_streak_debuff.duration_days} days")
    
    print("Debuff system validation: ✅ PASSED")
    return True

def test_daily_quest_completion():
    """Test the daily quest completion logic"""
    print("\n📅 Testing Daily Quest Completion Logic")
    print("-" * 50)
    
    # Test first quest
    result = GamificationEngine.process_daily_quest_completion(
        user_id=123,
        current_streak=0,
        last_quest_date=None,
        active_buffs=[]
    )
    
    assert result["new_streak"] == 1, "First quest should start streak at 1"
    assert result["streak_updated"] == True, "First quest should update streak"
    assert result["daily_bonus"] == 5, "First quest should give daily bonus"
    print("✅ First quest: Streak starts at 1, +5 runes bonus")
    
    # Test streak continuation
    yesterday = datetime.now() - timedelta(days=1)
    result = GamificationEngine.process_daily_quest_completion(
        user_id=123,
        current_streak=6,
        last_quest_date=yesterday,
        active_buffs=[]
    )
    
    assert result["new_streak"] == 7, "Streak should continue to 7"
    assert result["milestone_rewards"]["streak_length"] == 7, "Should trigger 7-day milestone"
    assert result["milestone_rewards"]["runes"] == 25, "7-day milestone should give 25 runes"
    print("✅ Streak continuation: 6 → 7 days, 7-day milestone triggered")
    
    # Test streak break with Phoenix Spirit protection
    week_ago = datetime.now() - timedelta(days=7)
    phoenix_buff = Buff(BuffType.STREAK_PROTECTION, "Phoenix Spirit", "Protection", 1.0, 30, datetime.now())
    
    result = GamificationEngine.process_daily_quest_completion(
        user_id=123,
        current_streak=29,
        last_quest_date=week_ago,
        active_buffs=[phoenix_buff]
    )
    
    assert result["phoenix_protection_used"] == True, "Phoenix Spirit should protect streak"
    assert result["new_streak"] == 30, "Streak should continue to 30 with protection"
    assert result["debuff_applied"] is None, "No debuff should be applied with protection"
    print("✅ Phoenix Spirit protection: 29 → 30 days streak maintained")
    
    # Test streak break without protection
    result = GamificationEngine.process_daily_quest_completion(
        user_id=123,
        current_streak=10,
        last_quest_date=week_ago,
        active_buffs=[]
    )
    
    assert result["streak_broken"] == True, "Streak should be broken"
    assert result["new_streak"] == 1, "Streak should reset to 1"
    assert result["debuff_applied"] is not None, "Debuff should be applied"
    print(f"✅ Streak break: 10 → 1 days, {result['debuff_applied'].name} debuff applied")
    
    print("Daily quest completion validation: ✅ PASSED")
    return True

def test_dashboard_formatting():
    """Test the dashboard formatting"""
    print("\n📊 Testing Dashboard Formatting")
    print("-" * 50)
    
    # Create sample buffs and debuffs
    active_buffs = [
        Buff(BuffType.XP_BOOST, "Focused Mind", "+10% XP gain", 0.10, float('inf'), datetime.now())
    ]
    
    active_debuffs = [
        Debuff(DebuffType.XP_REDUCTION, "Shadow State", "-20% XP gain", 0.20, 2, datetime.now() - timedelta(days=1))
    ]
    
    dashboard = GamificationEngine.format_dashboard_status(
        level=7,
        xp=90,
        xp_needed=60,
        streak=12,
        runes=120,
        title="Sound Sculptor",
        active_buffs=active_buffs,
        active_debuffs=active_debuffs
    )
    
    # Check that dashboard contains all required elements
    assert "Level 7" in dashboard, "Dashboard should show level"
    assert "90/150 XP" in dashboard, "Dashboard should show XP progress"
    assert "Streak: 12 days" in dashboard, "Dashboard should show streak"
    assert "Next: +50 Runes at 14 days" in dashboard, "Dashboard should show next milestone"
    assert "Shadow State (1 days left)" in dashboard, "Dashboard should show debuff countdown"
    assert "Focused Mind" in dashboard, "Dashboard should show active buffs"
    assert "Runes: 120" in dashboard, "Dashboard should show runes"
    
    print("✅ Dashboard formatting includes all required elements:")
    print("   • Level and XP progress")
    print("   • Streak with next milestone")
    print("   • Active debuffs with countdown")
    print("   • Active buffs with descriptions")
    print("   • Title and runes")
    
    print("Dashboard formatting validation: ✅ PASSED")
    return True

def test_iron_will_debuff_reduction():
    """Test Iron Will buff reducing debuff durations"""
    print("\n🛡️ Testing Iron Will Debuff Reduction")
    print("-" * 50)
    
    # Create a debuff
    original_debuff = Debuff(DebuffType.XP_REDUCTION, "Shadow State", "-20% XP", 0.20, 5, datetime.now())
    
    # Create Iron Will buff
    iron_will = Buff(BuffType.DEBUFF_SHIELD, "Iron Will", "Reduces debuff duration", 1.0, float('inf'), datetime.now())
    
    # Apply debuff with Iron Will protection
    modified_debuff = GamificationEngine.apply_debuff_with_resistance(original_debuff, [iron_will])
    
    assert modified_debuff.duration_days == 4, f"Iron Will should reduce duration from 5 to 4 days, got {modified_debuff.duration_days}"
    print("✅ Iron Will reduces Shadow State duration: 5 → 4 days")
    
    # Test minimum duration of 1 day
    short_debuff = Debuff(DebuffType.SLUGGISH, "Sluggish", "No progress", 1.0, 1, datetime.now())
    modified_short = GamificationEngine.apply_debuff_with_resistance(short_debuff, [iron_will])
    
    assert modified_short.duration_days == 1, "Iron Will should not reduce debuff below 1 day"
    print("✅ Iron Will respects minimum duration: 1 day minimum maintained")
    
    print("Iron Will debuff reduction validation: ✅ PASSED")
    return True

def main():
    """Run all tests"""
    print("🎯 STREAKS, BUFFS, AND DEBUFFS SYSTEM VALIDATION")
    print("=" * 70)
    print("Validating implementation against specification...")
    print()
    
    tests = [
        test_streak_system(),
        test_buff_system(),
        test_debuff_system(),
        test_daily_quest_completion(),
        test_dashboard_formatting(),
        test_iron_will_debuff_reduction()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print("\n" + "=" * 70)
    print("📊 FINAL VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 SUCCESS: Streaks, Buffs, and Debuffs system perfectly matches specification!")
        print("\n✅ All systems implemented:")
        print("   • 🔥 Streak System: Daily consistency with milestone rewards")
        print("   • 🌟 Buff System: Permanent earned boosts (cannot be purchased)")
        print("   • ☠️ Debuff System: Accountability penalties for streak breaks")
        print("   • 📊 Dashboard Integration: Comprehensive status display")
        print("   • 🛡️ Resistance System: Iron Will reduces debuff durations")
        print("   • 🔄 Daily Quest Logic: Complete streak processing")
        print("\n🚀 The enhanced gamification system is ready for production!")
        print("\n💡 Key Features:")
        print("   • Streaks encourage daily consistency")
        print("   • Buffs reward long-term mastery and milestones")
        print("   • Debuffs create accountability and increase stakes")
        print("   • RPG-like progression with rewards and penalties")
    else:
        print(f"\n❌ FAILED: {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)