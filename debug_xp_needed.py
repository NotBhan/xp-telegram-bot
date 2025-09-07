#!/usr/bin/env python3
"""Debug XP needed calculation"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine
from src.leveling_tables import LevelingTables

def debug_xp_needed():
    # Level 5 requirements
    current_level = 5
    working_xp_in_level = 17
    
    next_level_requirement = GamificationEngine.calculate_level_requirement(current_level + 1)
    xp_needed = next_level_requirement - working_xp_in_level
    
    print(f"Current level: {current_level}")
    print(f"XP in current level: {working_xp_in_level}")
    print(f"Next level requirement (Level 6): {next_level_requirement}")
    print(f"XP needed for next: {xp_needed}")
    print(f"Expected: 150 - 17 = 133")
    
    # Check Level 6 requirement
    level_6_req = LevelingTables.XP_THRESHOLDS[6]
    print(f"\\nLevel 6 threshold from table: {level_6_req}")

if __name__ == "__main__":
    debug_xp_needed()