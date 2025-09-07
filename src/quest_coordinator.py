"""
Quest Coordinator for XP Telegram Bot

This module orchestrates the complete quest assignment and completion flow,
integrating main quests, side quests, streaks, and the gamification engine.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .quest_system import QuestSystem, Quest, QuestType, QuestStatus, QuestDifficulty
from .side_quest_manager import SideQuestManager, SideQuestTrigger
from .gamification import GamificationEngine, Buff, Debuff

logger = logging.getLogger(__name__)

class QuestAssignmentStrategy:
    """Strategies for assigning daily quests"""
    
    @staticmethod
    def get_daily_quest_assignment(
        user_level: int,
        completion_history: List[Dict[str, Any]] = None,
        current_streak: int = 0,
        active_buffs: List[Buff] = None,
        ng_plus_data = None
    ) -> List[Quest]:
        """
        Generate optimal daily quest assignment:
        - 3 main quests (one per category)
        - Difficulty scaled to user performance
        - Rewards calculated with NG+ scaling
        """
        if completion_history is None:
            completion_history = []
        if active_buffs is None:
            active_buffs = []
        
        # Generate recommendation based on user data
        recommendations = GamificationEngine.generate_quest_recommendations(
            user_level=user_level,
            completion_history=completion_history,
            current_streak=current_streak,
            active_buffs=active_buffs,
            ng_plus_data=ng_plus_data
        )
        
        # Generate quests using recommended difficulties
        suggested_difficulties = recommendations.get("suggested_difficulties", ["Easy", "Medium", "Hard"])
        
        # Convert string difficulties to enum
        difficulty_mapping = {
            "Easy": QuestDifficulty.EASY,
            "Medium": QuestDifficulty.MEDIUM,
            "Hard": QuestDifficulty.HARD
        }
        
        difficulties = [difficulty_mapping.get(d, QuestDifficulty.EASY) for d in suggested_difficulties]
        
        # Generate base quests
        main_quests = []
        categories = QuestSystem.MAIN_QUEST_CATEGORIES
        
        for i, category in enumerate(categories):
            difficulty = difficulties[i] if i < len(difficulties) else QuestDifficulty.MEDIUM
            
            # Get available templates for this category/difficulty
            templates = QuestSystem.QUEST_TEMPLATES.get(category, {}).get(difficulty, [])
            
            if not templates:
                # Fallback to easier difficulty
                templates = QuestSystem.QUEST_TEMPLATES.get(category, {}).get(QuestDifficulty.EASY, [])
                difficulty = QuestDifficulty.EASY
            
            if templates:
                import random
                template = random.choice(templates)
                
                # Calculate rewards with NG+ scaling
                base_xp = QuestSystem.calculate_main_quest_xp(difficulty, user_level)
                base_runes = QuestSystem.calculate_main_quest_runes(difficulty)
                
                if ng_plus_data:
                    scaled_rewards = GamificationEngine.calculate_ng_plus_quest_rewards(
                        base_xp=5 if difficulty == QuestDifficulty.EASY else 10 if difficulty == QuestDifficulty.MEDIUM else 15,
                        base_runes=base_runes,
                        level=user_level,
                        difficulty=difficulty.value,
                        ng_plus_data=ng_plus_data
                    )
                    final_xp = scaled_rewards["xp"]
                    final_runes = scaled_rewards["runes"]
                else:
                    final_xp = base_xp
                    final_runes = base_runes
                
                quest = Quest(
                    name=template["name"],
                    quest_id=f"Q{i+1}",
                    description=template["description"],
                    difficulty=difficulty,
                    quest_type=QuestType.MAIN,
                    xp_reward=final_xp,
                    rune_reward=final_runes,
                    category=category,
                    estimated_time=template.get("time", "Variable"),
                    assigned_date=datetime.now(),
                    user_level_at_creation=user_level
                )
                
                main_quests.append(quest)
        
        return main_quests
    
    @staticmethod
    def should_assign_side_quest(
        user_level: int,
        current_streak: int,
        last_side_quest_date: Optional[datetime] = None,
        completion_history: List[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[SideQuestTrigger]]:
        """Determine if a side quest should be assigned and why"""
        
        # Get suggestion from side quest manager
        suggestion = SideQuestManager.get_next_side_quest_suggestion(
            user_level=user_level,
            completion_history=completion_history or [],
            current_streak=current_streak,
            last_side_quest_date=last_side_quest_date
        )
        
        if suggestion["should_offer"]:
            return True, suggestion["trigger_type"]
        
        return False, None
    
    @staticmethod
    def assign_side_quest(
        user_level: int,
        trigger: SideQuestTrigger,
        completion_history: List[Dict[str, Any]] = None
    ) -> Quest:
        """Assign an appropriate side quest"""
        
        # Analyze user preferences if history available
        preferred_theme = None
        if completion_history:
            analytics = SideQuestManager.get_side_quest_analytics(completion_history)
            if analytics.get("preferred_themes"):
                # Use preferred theme 60% of the time
                import random
                if random.random() < 0.6:
                    preferred_theme_name = analytics["preferred_themes"][0][0]
                    from .side_quest_manager import SideQuestTheme
                    for theme in SideQuestTheme:
                        if theme.value == preferred_theme_name:
                            preferred_theme = theme
                            break
        
        return SideQuestManager.generate_side_quest(
            user_level=user_level,
            trigger=trigger,
            preferred_theme=preferred_theme
        )

class QuestCompletionProcessor:
    """Handles quest completion with full integration"""
    
    @staticmethod
    def complete_quest(
        quest: Quest,
        user_data: Dict[str, Any],
        active_buffs: List[Buff] = None,
        active_debuffs: List[Debuff] = None,
        ng_plus_data = None
    ) -> Dict[str, Any]:
        """
        Process complete quest completion flow:
        - Mark quest as completed
        - Calculate and apply XP/Rune rewards
        - Update streaks (main quests only)
        - Trigger level-ups if applicable
        - Apply milestone rewards
        - Update user statistics
        """
        if active_buffs is None:
            active_buffs = []
        if active_debuffs is None:
            active_debuffs = []
        
        # Extract user data
        user_level = user_data.get("level", 1)
        user_total_xp = user_data.get("total_xp", 0)
        user_runes = user_data.get("runes", 0)
        current_streak = user_data.get("streak", 0)
        last_quest_date = user_data.get("last_quest_date")
        
        # Mark quest as completed
        quest.status = QuestStatus.COMPLETED
        quest.completed_date = datetime.now()
        
        # Process quest completion through gamification engine
        completion_result = GamificationEngine.process_quest_completion_with_streaks(
            quest_type=quest.quest_type.value,
            quest_difficulty=quest.difficulty.value,
            base_xp=quest.xp_reward,
            base_runes=quest.rune_reward,
            user_level=user_level,
            current_streak=current_streak,
            last_quest_date=last_quest_date,
            active_buffs=active_buffs,
            active_debuffs=active_debuffs,
            ng_plus_data=ng_plus_data
        )
        
        # Process XP gain and potential level-ups
        new_total_xp = user_total_xp + completion_result["quest_rewards"]["final_xp"]
        
        # Calculate level progression with overflow handling
        xp_result = GamificationEngine.process_xp_gain(
            current_xp=user_total_xp,
            xp_gain=completion_result["quest_rewards"]["final_xp"],
            active_buffs=active_buffs,
            active_debuffs=active_debuffs,
            ng_plus_data=ng_plus_data
        )
        
        # Process rune gain
        rune_result = GamificationEngine.process_rune_transaction(
            current_runes=user_runes,
            rune_change=completion_result["quest_rewards"]["final_runes"],
            active_buffs=active_buffs,
            active_debuffs=active_debuffs
        )
        
        # Get streak result
        streak_result = completion_result["streak_update"]
        
        # Prepare comprehensive result
        result = {
            "quest_completed": {
                "quest": quest.to_dict(),
                "completion_time": quest.completed_date.isoformat()
            },
            "rewards": {
                "base_quest_xp": quest.xp_reward,
                "base_quest_runes": quest.rune_reward,
                "final_xp_gained": completion_result["quest_rewards"]["final_xp"],
                "final_runes_gained": completion_result["quest_rewards"]["final_runes"],
                "xp_multiplier": completion_result["quest_rewards"]["xp_multiplier"],
                "effects_applied": completion_result["effects_applied"]
            },
            "level_progression": {
                "old_level": xp_result.get("old_level", user_level),
                "new_level": xp_result.get("new_level", user_level),
                "levels_gained": xp_result.get("levels_gained", 0),
                "level_up_occurred": xp_result.get("level_up_occurred", False),
                "new_total_xp": xp_result.get("new_total_xp", new_total_xp),
                "xp_in_current_level": xp_result.get("xp_in_current_level", 0),
                "xp_needed_for_next": xp_result.get("xp_needed_for_next", 0)
            },
            "streak_update": streak_result,
            "new_totals": {
                "level": xp_result.get("new_level", user_level),
                "total_xp": xp_result.get("new_total_xp", new_total_xp),
                "runes": rune_result["new_rune_total"],
                "streak": streak_result["new_streak"],
                "last_quest_date": quest.completed_date.isoformat()
            },
            "milestone_rewards": {},
            "special_effects": []
        }
        
        # Check for milestone rewards from level-ups
        if xp_result.get("level_up_occurred", False):
            result["milestone_rewards"]["level_up"] = {
                "levels_gained": xp_result.get("levels_gained", 0),
                "level_up_rune_bonus": xp_result.get("level_up_rune_bonus", 0),
                "level_up_details": xp_result.get("level_up_details", [])
            }
        
        # Check for streak milestone rewards
        if streak_result.get("milestone_rewards"):
            result["milestone_rewards"]["streak"] = streak_result["milestone_rewards"]
        
        # Check for title unlocks
        if xp_result.get("title_unlocked", False):
            result["special_effects"].append({
                "type": "title_unlock",
                "title": xp_result.get("new_title", ""),
                "level": xp_result.get("new_level", user_level)
            })
        
        # Check for new buff unlocks from streaks
        if streak_result.get("buffs_unlocked"):
            for buff_name in streak_result["buffs_unlocked"]:
                result["special_effects"].append({
                    "type": "buff_unlock",
                    "buff": buff_name,
                    "source": "streak_milestone"
                })
        
        # Check for trophy eligibility
        updated_stats = {
            "total_quests_completed": user_data.get("total_quests_completed", 0) + 1,
            "side_quests_completed": user_data.get("side_quests_completed", 0) + (1 if quest.quest_type == QuestType.SIDE else 0),
            "max_streak": max(user_data.get("max_streak", 0), streak_result["new_streak"]),
            "total_xp": result["new_totals"]["total_xp"],
            "level": result["new_totals"]["level"]
        }
        
        eligible_trophies = GamificationEngine.check_trophy_eligibility(updated_stats)
        if eligible_trophies:
            result["special_effects"].append({
                "type": "trophy_eligibility",
                "trophies": [trophy.to_dict() if hasattr(trophy, 'to_dict') else str(trophy) for trophy in eligible_trophies]
            })
        
        return result
    
    @staticmethod
    def batch_complete_quests(
        quests: List[Quest],
        user_data: Dict[str, Any],
        active_buffs: List[Buff] = None,
        active_debuffs: List[Debuff] = None,
        ng_plus_data = None
    ) -> Dict[str, Any]:
        """Complete multiple quests in sequence, maintaining state"""
        
        batch_result = {
            "total_quests_completed": 0,
            "total_xp_gained": 0,
            "total_runes_gained": 0,
            "levels_gained": 0,
            "quest_results": [],
            "final_user_state": {},
            "batch_milestones": []
        }
        
        # Process each quest sequentially
        current_user_data = user_data.copy()
        
        for quest in quests:
            if quest.status != QuestStatus.COMPLETED:
                quest_result = QuestCompletionProcessor.complete_quest(
                    quest=quest,
                    user_data=current_user_data,
                    active_buffs=active_buffs,
                    active_debuffs=active_debuffs,
                    ng_plus_data=ng_plus_data
                )
                
                # Update tracking
                batch_result["total_quests_completed"] += 1
                batch_result["total_xp_gained"] += quest_result["rewards"]["final_xp_gained"]
                batch_result["total_runes_gained"] += quest_result["rewards"]["final_runes_gained"]
                batch_result["levels_gained"] += quest_result["level_progression"]["levels_gained"]
                batch_result["quest_results"].append(quest_result)
                
                # Update current user data for next quest
                current_user_data.update(quest_result["new_totals"])
                current_user_data["total_quests_completed"] = current_user_data.get("total_quests_completed", 0) + 1
        
        batch_result["final_user_state"] = current_user_data
        
        # Check for batch-level milestones
        if batch_result["levels_gained"] >= 3:
            batch_result["batch_milestones"].append({
                "type": "multi_level_up",
                "levels": batch_result["levels_gained"],
                "bonus": "Multi-level achievement!"
            })
        
        if batch_result["total_quests_completed"] >= 3:
            batch_result["batch_milestones"].append({
                "type": "quest_sweep",
                "count": batch_result["total_quests_completed"],
                "bonus": "Perfect quest completion!"
            })
        
        return batch_result

class QuestCoordinator:
    """Main coordinator for the complete quest system"""
    
    def __init__(self):
        self.assignment_strategy = QuestAssignmentStrategy()
        self.completion_processor = QuestCompletionProcessor()
    
    def create_daily_quest_set(
        self,
        user_data: Dict[str, Any],
        completion_history: List[Dict[str, Any]] = None,
        active_buffs: List[Buff] = None,
        ng_plus_data = None
    ) -> Dict[str, Any]:
        """
        Create a complete daily quest set:
        - 3 main quests
        - Optional side quest based on triggers
        """
        if completion_history is None:
            completion_history = []
        if active_buffs is None:
            active_buffs = []
        
        user_level = user_data.get("level", 1)
        current_streak = user_data.get("streak", 0)
        last_side_quest_date = user_data.get("last_side_quest_date")
        
        quest_set = {
            "main_quests": [],
            "side_quest": None,
            "assignment_date": datetime.now().isoformat(),
            "assignment_metadata": {}
        }
        
        # Generate main quests
        main_quests = self.assignment_strategy.get_daily_quest_assignment(
            user_level=user_level,
            completion_history=completion_history,
            current_streak=current_streak,
            active_buffs=active_buffs,
            ng_plus_data=ng_plus_data
        )
        
        quest_set["main_quests"] = main_quests
        
        # Check for side quest assignment
        should_assign, trigger = self.assignment_strategy.should_assign_side_quest(
            user_level=user_level,
            current_streak=current_streak,
            last_side_quest_date=last_side_quest_date,
            completion_history=completion_history
        )
        
        if should_assign and trigger:
            side_quest = self.assignment_strategy.assign_side_quest(
                user_level=user_level,
                trigger=trigger,
                completion_history=completion_history
            )
            quest_set["side_quest"] = side_quest
            quest_set["assignment_metadata"]["side_quest_trigger"] = trigger.value
        
        # Add metadata
        quest_set["assignment_metadata"].update({
            "user_level": user_level,
            "current_streak": current_streak,
            "quest_count": len(main_quests) + (1 if quest_set["side_quest"] else 0),
            "total_possible_xp": sum(q.xp_reward for q in main_quests) + (quest_set["side_quest"].xp_reward if quest_set["side_quest"] else 0),
            "total_possible_runes": sum(q.rune_reward for q in main_quests) + (quest_set["side_quest"].rune_reward if quest_set["side_quest"] else 0)
        })
        
        return quest_set
    
    def get_quest_status_summary(self, quests: List[Quest]) -> Dict[str, Any]:
        """Get comprehensive status summary of quest list"""
        
        summary = {
            "total_quests": len(quests),
            "completed_quests": 0,
            "pending_quests": 0,
            "in_progress_quests": 0,
            "main_quests": 0,
            "side_quests": 0,
            "total_xp_available": 0,
            "total_runes_available": 0,
            "completion_rate": 0.0,
            "quest_breakdown": {
                "easy": 0,
                "medium": 0,
                "hard": 0,
                "rare": 0
            }
        }
        
        for quest in quests:
            # Count by status
            if quest.status == QuestStatus.COMPLETED:
                summary["completed_quests"] += 1
            elif quest.status == QuestStatus.IN_PROGRESS:
                summary["in_progress_quests"] += 1
            else:
                summary["pending_quests"] += 1
            
            # Count by type
            if quest.quest_type == QuestType.MAIN:
                summary["main_quests"] += 1
            else:
                summary["side_quests"] += 1
            
            # Count by difficulty
            difficulty_key = quest.difficulty.value.lower()
            if difficulty_key in summary["quest_breakdown"]:
                summary["quest_breakdown"][difficulty_key] += 1
            
            # Accumulate rewards for pending quests
            if quest.status != QuestStatus.COMPLETED:
                summary["total_xp_available"] += quest.xp_reward
                summary["total_runes_available"] += quest.rune_reward
        
        # Calculate completion rate
        if summary["total_quests"] > 0:
            summary["completion_rate"] = summary["completed_quests"] / summary["total_quests"]
        
        return summary
    
    def recommend_next_action(
        self,
        quests: List[Quest],
        user_data: Dict[str, Any],
        active_buffs: List[Buff] = None
    ) -> Dict[str, Any]:
        """Recommend what the user should do next based on quest state"""
        
        if active_buffs is None:
            active_buffs = []
        
        pending_quests = [q for q in quests if q.status != QuestStatus.COMPLETED]
        
        recommendation = {
            "action": "none",
            "quest_id": None,
            "reason": "",
            "priority": "normal",
            "estimated_rewards": {}
        }
        
        if not pending_quests:
            recommendation["action"] = "all_complete"
            recommendation["reason"] = "All quests completed! Check back tomorrow for new quests."
            return recommendation
        
        # Analyze active buffs for recommendations
        has_xp_boost = any(buff.buff_type.value == "xp_boost" and buff.is_active() for buff in active_buffs)
        has_rune_boost = any(buff.buff_type.value == "rune_boost" and buff.is_active() for buff in active_buffs)
        
        # Sort quests by recommendation priority
        def quest_priority_score(quest):
            score = 0
            
            # Prioritize main quests for streaks
            if quest.quest_type == QuestType.MAIN:
                score += 10
            
            # Prioritize based on active buffs
            if has_xp_boost and quest.xp_reward > 20:
                score += 5
            if has_rune_boost and quest.rune_reward > 25:
                score += 5
            
            # Prioritize easier quests for momentum
            if quest.difficulty == QuestDifficulty.EASY:
                score += 3
            elif quest.difficulty == QuestDifficulty.MEDIUM:
                score += 2
            
            return score
        
        # Get highest priority quest
        best_quest = max(pending_quests, key=quest_priority_score)
        
        recommendation["action"] = "complete_quest"
        recommendation["quest_id"] = best_quest.quest_id
        recommendation["estimated_rewards"] = {
            "xp": best_quest.xp_reward,
            "runes": best_quest.rune_reward
        }
        
        # Generate reason
        if best_quest.quest_type == QuestType.MAIN:
            recommendation["reason"] = f"Complete {best_quest.quest_id} to maintain your streak"
            recommendation["priority"] = "high"
        elif has_xp_boost and best_quest.xp_reward > 20:
            recommendation["reason"] = f"XP boost active - great time for {best_quest.quest_id}"
            recommendation["priority"] = "high"
        elif best_quest.difficulty == QuestDifficulty.EASY:
            recommendation["reason"] = f"Build momentum with easy quest {best_quest.quest_id}"
        else:
            recommendation["reason"] = f"Continue with {best_quest.quest_id}"
        
        return recommendation