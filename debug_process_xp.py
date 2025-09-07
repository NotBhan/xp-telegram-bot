#!/usr/bin/env python3
"""Debug the process_xp_gain function specifically"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine
from src.leveling_tables import LevelingTables

def debug_process_xp_gain():
    print("🔍 Debugging process_xp_gain Function")
    print("=" * 50)
    
    # Set up the scenario
    level_4_cumulative = LevelingTables.CUMULATIVE_XP[4]
    current_total_xp = level_4_cumulative + 120  # Level 4 with 120 XP
    xp_gain = 22
    
    print(f"🎯 Input:")
    print(f"   Current total XP: {current_total_xp}")
    print(f"   XP gain: {xp_gain}")
    
    # Step through the process_xp_gain logic manually
    print(f"\n🔧 Step-by-step processing:")
    
    # Get current level
    current_level_info = GamificationEngine.calculate_level_from_xp(current_total_xp)
    old_level = current_level_info[0]
    print(f"   1. Old level: {old_level}")
    
    # Add XP gain
    working_xp = current_total_xp + xp_gain
    print(f"   2. Working XP after gain: {working_xp}")
    
    # Check level from working XP
    working_level_info = GamificationEngine.calculate_level_from_xp(working_xp)
    print(f"   3. Working level info: Level {working_level_info[0]}, XP in level: {working_level_info[1]}")
    
    # Manual level-up check
    current_level = old_level
    print(f"\n🔄 Level-up Loop Simulation:")
    iteration = 0
    
    temp_xp = working_xp
    while iteration < 3:  # Prevent infinite loop
        iteration += 1
        print(f"\n   Iteration {iteration}:")
        
        # Get current level and XP distribution
        level_info = GamificationEngine.calculate_level_from_xp(temp_xp)
        temp_level = level_info[0]
        xp_in_level = level_info[1]
        
        print(f"     Current level from XP: {temp_level}")
        print(f"     XP in current level: {xp_in_level}")
        
        # Get XP requirement for next level
        next_level = temp_level + 1
        xp_required_for_next = GamificationEngine.calculate_level_requirement(next_level)
        
        print(f"     Next level: {next_level}")
        print(f"     XP required for next: {xp_required_for_next}")
        print(f"     Can level up? {xp_in_level >= xp_required_for_next}")
        
        if xp_in_level >= xp_required_for_next:
            print(f"     ✅ Leveling up to {next_level}!")
            current_level = next_level
            temp_xp = temp_xp - xp_required_for_next
            print(f"     Remaining XP after level-up: {temp_xp}")
        else:
            print(f"     ❌ Cannot level up, stopping loop")
            break
    
    print(f"\n🎊 Final Result:")
    print(f"   Final level: {current_level}")
    print(f"   Final XP: {temp_xp}")
    
    # Compare with actual function result
    print(f"\n🔧 Actual Function Result:")
    result = GamificationEngine.process_xp_gain(
        current_xp=current_total_xp,
        xp_gain=xp_gain,
        active_buffs=[],
        active_debuffs=[]
    )
    
    print(f"   Old level: {result['old_level']}")
    print(f"   New level: {result['new_level']}")
    print(f"   Levels gained: {result['levels_gained']}")
    print(f"   Total XP: {result['new_total_xp']}")
    print(f"   XP in level: {result['xp_in_current_level']}")

if __name__ == "__main__":
    debug_process_xp_gain()