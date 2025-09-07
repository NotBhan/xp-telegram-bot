#!/usr/bin/env python3
"""
New Game+ (NG+) System Complete Demo

This script demonstrates the full NG+ system with examples
of progression, scaling, and prestige rewards.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine, NewGamePlusData, Buff, Debuff, BuffType, DebuffType

def demo_ng_plus_eligibility():
    """Demonstrate NG+ unlock requirements"""
    print("🔒 NEW GAME+ UNLOCK REQUIREMENTS")
    print("=" * 60)
    
    print("NG+ becomes available when a user reaches Level 100!")
    print()
    
    scenarios = [
        (50, "Halfway there..."),
        (75, "Getting close..."),
        (99, "So close!"),
        (100, "🎉 NG+ UNLOCKED!")
    ]
    
    for level, message in scenarios:
        eligible = GamificationEngine.can_start_new_game_plus(level, 0)
        status = "✅ ELIGIBLE" if eligible else "❌ Not eligible"
        print(f"Level {level:3}: {status} - {message}")
    
    print()

def demo_ng_plus_scaling():
    """Demonstrate NG+ difficulty scaling"""
    print("⚖️ NEW GAME+ DIFFICULTY SCALING")
    print("=" * 60)
    
    print("Difficulty scales with each NG+ cycle:")
    print()
    print("Cycle | XP Scaling | Quest Rewards | Debuff Severity")
    print("------|------------|---------------|----------------")
    
    for cycle in range(0, 6):
        if cycle == 0:
            ng_data = None
            xp_scaling = "Base (100%)"
            quest_scaling = "Base (100%)"
            debuff_scaling = "Base (100%)"
        else:
            ng_data = NewGamePlusData(
                cycle=cycle, total_completions=cycle,
                carried_over_titles=[], carried_over_buffs=[],
                carried_over_trophies=[], prestige_rewards=[],
                started_date=datetime.now()
            )
            xp_scaling = f"+{int((ng_data.get_xp_scaling_multiplier() - 1) * 100)}%"
            quest_scaling = f"+{int((ng_data.get_quest_scaling_multiplier() - 1) * 100)}%"
            debuff_scaling = f"+{int((ng_data.get_debuff_scaling_multiplier() - 1) * 100)}%"
        
        cycle_name = f"NG+{cycle}" if cycle > 0 else "Base"
        print(f"{cycle_name:5} | {xp_scaling:10} | {quest_scaling:13} | {debuff_scaling}")
    
    print()
    print("📈 Higher cycles = Greater challenge but better rewards!")
    print()

def demo_prestige_rewards():
    """Demonstrate NG+ prestige reward system"""
    print("🏆 NEW GAME+ PRESTIGE REWARDS")
    print("=" * 60)
    
    print("Each NG+ cycle grants unique permanent rewards:")
    print()
    
    prestige_info = {
        1: ("The Reborn", "Additional buff slot unlocked"),
        2: ("Endless Challenger", "Rune Shop discounts (-10%)"),
        3: ("Eternal Flame", "Immune to first debuff each month"),
        4: ("Legend of the Cycle", "Legendary status trophy"),
        5: ("Ascended", "Permanent +5 runes per quest")
    }
    
    for cycle, (title, reward) in prestige_info.items():
        rewards = GamificationEngine.get_ng_plus_prestige_rewards(cycle)
        
        print(f"🌟 NG+{cycle}: {title}")
        print(f"   Reward: {reward}")
        print(f"   Status: {'✅ Implemented' if rewards['titles'] or rewards['buffs'] or rewards['special_effects'] else '⏳ Planned'}")
        print()

def demo_ng_plus_progression():
    """Demonstrate NG+ progression example"""
    print("🔄 NEW GAME+ PROGRESSION EXAMPLE")
    print("=" * 60)
    
    print("User Journey: Level 100 → NG+1 restart")
    print()
    
    # Before NG+
    print("📊 BEFORE NG+ (Level 100 completion):")
    print("   Level: 100")
    print("   Total XP: 127,500")
    print("   Runes: 2,500")
    print("   Streak: 45 days")
    print("   Titles: Legendary Champion, Expert Craftsman")
    print("   Buffs: Focused Mind, Rune Magnet, Unyielding Will")
    print("   Trophies: 12 earned")
    print()
    
    # NG+ Decision
    print("🎉 NG+ UNLOCK PROMPT:")
    print("┌─────────────────────────────────────────────┐")
    print("│ Congratulations! You've completed Level 100 │")
    print("│ Would you like to enter New Game+?          │")
    print("│                                             │")
    print("│ 🔁 Restart at Level 1 with harder challenges│")
    print("│ but keep your Titles, Buffs, and Trophies! │")
    print("│                                             │")
    print("│    [✅ Start NG+1]    [❌ Stay Level 100]   │")
    print("└─────────────────────────────────────────────┘")
    print()
    
    # After NG+ Reset
    ng_data = GamificationEngine.create_new_game_plus_data(
        current_ng_cycle=0,
        carried_titles=["Legendary Champion", "Expert Craftsman"],
        carried_buffs=["focused_mind", "rune_magnet", "unyielding_will"],
        carried_trophies=["First Steps", "Week Warrior", "Quest Master", "Level Champion"]
    )
    
    print("🔄 AFTER NG+1 RESET:")
    print("   Level: 1 (RESET)")
    print("   Total XP: 0 (RESET)")
    print("   Runes: 100 (RESET to base)")
    print("   Streak: 0 (RESET)")
    print("   ✅ Carried Over:")
    print("     • Titles: Legendary Champion, Expert Craftsman, The Reborn")
    print("     • Buffs: Focused Mind, Rune Magnet, Unyielding Will")
    print("     • Trophies: All 12 previous trophies")
    print("   🌟 New Benefits:")
    print(f"     • XP Requirements: +{int((ng_data.get_xp_scaling_multiplier() - 1) * 100)}% (harder)")
    print(f"     • Quest Rewards: +{int((ng_data.get_quest_scaling_multiplier() - 1) * 100)}% (better)")
    print("     • Additional buff slot unlocked")
    print()

def demo_ng_plus_dashboard():
    """Demonstrate NG+ dashboard display"""
    print("📊 NEW GAME+ DASHBOARD DISPLAY")
    print("=" * 60)
    
    # Create NG+2 scenario
    ng_data = NewGamePlusData(
        cycle=2,
        total_completions=2,
        carried_over_titles=["Legendary Champion", "The Reborn", "Endless Challenger"],
        carried_over_buffs=["focused_mind", "rune_magnet", "eternal_flame"],
        carried_over_trophies=["First Steps", "Week Warrior", "Quest Master"],
        prestige_rewards=["ng_plus_2", "rune_shop_discount"],
        started_date=datetime.now()
    )
    
    # Sample active effects
    active_buffs = [
        Buff(BuffType.XP_BOOST, "Focused Mind", "+10% XP gain", 0.10, float('inf'), datetime.now()),
        Buff(BuffType.DEBUFF_SHIELD, "Eternal Flame", "Immune to first debuff each month", 1.0, float('inf'), datetime.now())
    ]
    
    active_debuffs = [
        Debuff(DebuffType.XP_REDUCTION, "Shadow State", "-22% XP gain (NG+2 Enhanced)", 0.22, 5, datetime.now())
    ]
    
    dashboard = GamificationEngine.format_ng_plus_dashboard_status(
        level=8,
        xp=45,
        xp_needed=155,  # Scaled for NG+2
        streak=12,
        runes=250,
        title="Endless Challenger",
        active_buffs=active_buffs,
        active_debuffs=active_debuffs,
        ng_plus_data=ng_data
    )
    
    print("Example NG+2 Dashboard:")
    print("┌─────────────────────────────────────────┐")
    for line in dashboard.split('\n'):
        print(f"│ {line:<39} │")
    print("└─────────────────────────────────────────┘")
    print()

def demo_quest_scaling():
    """Demonstrate quest reward scaling"""
    print("💎 QUEST REWARD SCALING EXAMPLE")
    print("=" * 60)
    
    print("Medium Quest (Level 10) Rewards Across NG+ Cycles:")
    print()
    print("Cycle | Base XP | Scaled XP | Base Runes | Scaled Runes")
    print("------|---------|-----------|------------|-------------")
    
    base_xp = 10
    base_runes = 20
    level = 10
    
    for cycle in range(0, 4):
        if cycle == 0:
            ng_data = None
        else:
            ng_data = NewGamePlusData(
                cycle=cycle, total_completions=cycle,
                carried_over_titles=[], carried_over_buffs=[],
                carried_over_trophies=[], prestige_rewards=[],
                started_date=datetime.now()
            )
        
        rewards = GamificationEngine.calculate_ng_plus_quest_rewards(
            base_xp, base_runes, level, "Medium", ng_data
        )
        
        base_calc_xp = int(base_xp * (1 + 0.15 * level))  # Medium quest formula
        cycle_name = f"NG+{cycle}" if cycle > 0 else "Base"
        
        print(f"{cycle_name:5} | {base_calc_xp:7} | {rewards['xp']:9} | {base_runes:10} | {rewards['runes']:11}")
    
    print()
    print("📈 Higher NG+ cycles provide proportionally better rewards!")
    print()

def main():
    """Run the complete NG+ demonstration"""
    print("🎮 NEW GAME+ (NG+) SYSTEM COMPLETE DEMONSTRATION")
    print("=" * 70)
    print("Live showcase of infinite replayability and prestige progression")
    print("=" * 70)
    print()
    
    demo_ng_plus_eligibility()
    demo_ng_plus_scaling()
    demo_prestige_rewards()
    demo_ng_plus_progression()
    demo_ng_plus_dashboard()
    demo_quest_scaling()
    
    print("🎆 NEW GAME+ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("🚀 The NG+ system provides:")
    print("• 🔒 Clear unlock requirement (Level 100)")
    print("• ⚖️ Progressive difficulty scaling")
    print("• 🏆 Meaningful prestige rewards")
    print("• 🔄 Complete reset with selective carry-over")
    print("• ♾️ Infinite replayability")
    print()
    print("🎯 Result: Players never run out of meaningful progression!")

if __name__ == "__main__":
    main()