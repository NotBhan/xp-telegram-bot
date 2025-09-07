#!/usr/bin/env python3
"""Debug script to understand the XP calculation issue"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.leveling_tables import LevelingTables

def debug_xp_calculation():
    print("🔍 Debugging XP Calculation")
    print("=" * 50)
    
    # Expected scenario from specification
    print("📋 Specification Example:")
    print("   User at Level 4 with 120/125 XP")
    print("   Completes Medium Quest: +22 XP")
    print("   Expected: Level 5 with 17/150 XP")
    print()
    
    # Calculate cumulative XP for Level 4 with 120 XP
    level_4_cumulative = LevelingTables.CUMULATIVE_XP[4]  # XP to reach Level 4
    current_total_xp = level_4_cumulative + 120  # 120 XP into Level 4
    
    print(f"🧮 Initial Calculation:")
    print(f"   Level 4 cumulative XP: {level_4_cumulative}")
    print(f"   XP in Level 4: 120")
    print(f"   Total current XP: {current_total_xp}")
    
    # Verify current position
    current_info = LevelingTables.get_level_from_xp(current_total_xp)
    print(f"   Verification: Level {current_info['level']}, XP in level: {current_info['xp_in_current_level']}")
    print()
    
    # Add 22 XP
    new_total_xp = current_total_xp + 22
    print(f"➕ After adding 22 XP:")
    print(f"   New total XP: {new_total_xp}")
    
    # Check where this puts us
    new_info = LevelingTables.get_level_from_xp(new_total_xp)
    print(f"   New level: {new_info['level']}")
    print(f"   XP in current level: {new_info['xp_in_current_level']}")
    print(f"   XP needed for next: {new_info['xp_needed_for_next']}")
    print()
    
    # Manual level-up check
    print("🎯 Manual Level-up Check:")
    level_4_threshold = LevelingTables.XP_THRESHOLDS[4]  # XP required for Level 4
    xp_in_level_4 = 120 + 22  # 142 XP total in Level 4
    
    print(f"   Level 4 XP requirement: {level_4_threshold}")
    print(f"   XP in Level 4 after quest: {xp_in_level_4}")
    print(f"   Can level up? {xp_in_level_4 >= level_4_threshold}")
    
    if xp_in_level_4 >= level_4_threshold:
        overflow_xp = xp_in_level_4 - level_4_threshold
        print(f"   Overflow XP for Level 5: {overflow_xp}")
        level_5_threshold = LevelingTables.XP_THRESHOLDS[5]
        print(f"   Level 5 XP requirement: {level_5_threshold}")
        print(f"   Expected final state: Level 5 with {overflow_xp}/{level_5_threshold} XP")
    
    print()
    
    # Check the table structure
    print("📊 XP Table (Levels 1-6):")
    print("Level | Threshold | Cumulative")
    print("-" * 30)
    for level in range(1, 7):
        threshold = LevelingTables.XP_THRESHOLDS[level]
        cumulative = LevelingTables.CUMULATIVE_XP[level]
        print(f"{level:5} | {threshold:9} | {cumulative:10}")

if __name__ == "__main__":
    debug_xp_calculation()