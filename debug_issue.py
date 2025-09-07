#!/usr/bin/env python3
"""Debug the exact issue in process_xp_gain"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine
from src.leveling_tables import LevelingTables

def debug_exact_issue():
    print("🔍 Debug Exact Issue")
    print("=" * 40)
    
    # Exact scenario
    level_4_cumulative = LevelingTables.CUMULATIVE_XP[4]
    current_total_xp = level_4_cumulative + 120  # 345
    xp_gain = 22
    
    print(f"Starting: Level 4 with 120 XP (total: {current_total_xp})")
    print(f"Gaining: {xp_gain} XP")
    
    # Manual step-through of my new algorithm
    current_level_info = GamificationEngine.calculate_level_from_xp(current_total_xp)
    old_level = current_level_info[0]  # 4
    current_xp_in_level = current_level_info[1]  # 120
    
    print(f"\\n1. Current level: {old_level}")
    print(f"2. XP in current level: {current_xp_in_level}")
    
    # Start with the XP in current level plus the gain
    working_xp_in_level = current_xp_in_level + xp_gain  # 120 + 22 = 142
    current_level = old_level  # 4
    
    print(f"3. Working XP in level: {working_xp_in_level}")
    print(f"4. Current level: {current_level}")
    
    # Level-up check
    next_level = current_level + 1  # 5
    xp_required_for_next = GamificationEngine.calculate_level_requirement(next_level)  # 150
    
    print(f"5. Next level: {next_level}")
    print(f"6. XP required for next level: {xp_required_for_next}")
    print(f"7. Can level up? {working_xp_in_level >= xp_required_for_next} ({working_xp_in_level} >= {xp_required_for_next})")
    
    # Wait, this is wrong! The XP requirement for Level 5 is 150, but we need to check against Level 4's requirement!
    # Let me check what the requirement should be
    level_4_requirement = GamificationEngine.calculate_level_requirement(4)  # 125
    print(f"\\n🚨 ISSUE FOUND!")
    print(f"   Level 4 requirement: {level_4_requirement}")
    print(f"   We have {working_xp_in_level} XP in Level 4")
    print(f"   Should check: {working_xp_in_level} >= {level_4_requirement} = {working_xp_in_level >= level_4_requirement}")
    
    if working_xp_in_level >= level_4_requirement:
        print(f"   ✅ Should level up to Level 5!")
        overflow = working_xp_in_level - level_4_requirement
        print(f"   Overflow XP: {overflow}")
    
    print(f"\\n📝 The issue: I'm checking the requirement for the NEXT level, not the CURRENT level!")

if __name__ == "__main__":
    debug_exact_issue()