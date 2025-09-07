#!/usr/bin/env python3
"""
New Game+ (NG+) System Basic Test

This script validates the core NG+ system implementation.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gamification import GamificationEngine, NewGamePlusData

def test_basic_ng_plus():
    """Test basic NG+ functionality"""
    print("Testing New Game+ System")
    print("=" * 40)
    
    # Test eligibility
    print("1. Testing NG+ eligibility:")
    eligible_100 = GamificationEngine.can_start_new_game_plus(100, 5000)
    not_eligible_50 = GamificationEngine.can_start_new_game_plus(50, 1000)
    
    print(f"   Level 100: {eligible_100} (should be True)")
    print(f"   Level 50: {not_eligible_50} (should be False)")
    
    # Test NG+ data creation
    print("\n2. Testing NG+ data creation:")
    ng_data = GamificationEngine.create_new_game_plus_data(
        current_ng_cycle=0,
        carried_titles=["Champion"],
        carried_buffs=["focused_mind"],
        carried_trophies=["First Steps"]
    )
    
    print(f"   Created NG+{ng_data.cycle}")
    print(f"   XP scaling: {ng_data.get_xp_scaling_multiplier()}")
    print(f"   Quest scaling: {ng_data.get_quest_scaling_multiplier()}")
    
    # Test scaling calculations
    print("\n3. Testing scaling calculations:")
    base_xp = GamificationEngine.calculate_level_requirement(5, None)
    scaled_xp = GamificationEngine.calculate_level_requirement(5, ng_data)
    
    print(f"   Level 5 XP (base): {base_xp}")
    print(f"   Level 5 XP (NG+1): {scaled_xp}")
    print(f"   Scaling factor: {scaled_xp/base_xp:.2f}")
    
    # Test prestige rewards
    print("\n4. Testing prestige rewards:")
    rewards = GamificationEngine.get_ng_plus_prestige_rewards(1)
    print(f"   NG+1 titles: {rewards['titles']}")
    print(f"   NG+1 special effects: {rewards['special_effects']}")
    
    print("\nBasic NG+ test completed successfully!")
    return True

if __name__ == "__main__":
    test_basic_ng_plus()