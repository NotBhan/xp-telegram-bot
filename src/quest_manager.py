"""
Quest Management System for XP Telegram Bot

This module provides advanced quest management functionality including
quest selection strategies, side quest triggering, and quest analytics.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from .quest_data import QUEST_DATABASE, REWARD_FORMULAS, LEVEL_QUEST_DISTRIBUTION

logger = logging.getLogger(__name__)

class QuestSelectionStrategy(Enum):
    """Different strategies for selecting daily quests"""
    BALANCED = "balanced"  # Default: balanced difficulty progression
    FOCUSED = "focused"    # Focus on one category
    RANDOM = "random"      # Completely random selection
    ADAPTIVE = "adaptive"  # Adapts based on user completion history

class QuestManager:
    """Advanced quest management with selection strategies and analytics"""
    
    def __init__(self):
        self.selection_strategy = QuestSelectionStrategy.ADAPTIVE
    
    def should_trigger_side_quest(self, user_level: int, last_side_quest_date: Optional[datetime] = None) -> bool:
        """
        Determine if a side quest should be triggered based on:
        - User level (higher levels get more frequent side quests)
        - Time since last side quest
        - Random chance
        """
        # Base probability increases with level
        base_probability = min(0.3 + (user_level * 0.01), 0.7)
        
        # Increase probability if it's been a while since last side quest
        if last_side_quest_date:
            days_since = (datetime.now() - last_side_quest_date).days
            if days_since >= 3:
                base_probability += 0.2
            elif days_since >= 7:
                base_probability += 0.4
        
        return random.random() < base_probability
    
    def get_recommended_daily_quests(
        self, 
        user_level: int, 
        strategy: Optional[QuestSelectionStrategy] = None,
        user_preferences: Optional[Dict[str, float]] = None,
        completion_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recommended daily quests based on strategy and user data
        
        Args:
            user_level: Current user level
            strategy: Quest selection strategy to use
            user_preferences: Dict of category preferences (0.0-1.0)
            completion_history: Recent quest completion data
        """
        if strategy is None:
            strategy = self.selection_strategy
        
        if strategy == QuestSelectionStrategy.BALANCED:
            return self._get_balanced_quests(user_level)
        elif strategy == QuestSelectionStrategy.FOCUSED:
            return self._get_focused_quests(user_level, user_preferences)
        elif strategy == QuestSelectionStrategy.RANDOM:
            return self._get_random_quests(user_level)
        elif strategy == QuestSelectionStrategy.ADAPTIVE:
            return self._get_adaptive_quests(user_level, completion_history, user_preferences)
        else:
            return self._get_balanced_quests(user_level)
    
    def _get_balanced_quests(self, user_level: int) -> List[Dict[str, Any]]:
        """Default balanced quest selection (current implementation)"""
        # This matches the existing logic in create_comprehensive_quests
        difficulty_distribution, side_quest_count = self._get_level_distribution(user_level)
        main_categories = ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"]
        
        quests = []
        for category, difficulty in zip(main_categories, difficulty_distribution):
            quest = self._select_quest_from_category(category, difficulty, user_level)
            if quest:
                quests.append(quest)
        
        return quests
    
    def _get_focused_quests(self, user_level: int, preferences: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Focus on user's preferred category"""
        if not preferences:
            return self._get_balanced_quests(user_level)
        
        # Find preferred category
        preferred_category = max(preferences.keys(), key=lambda k: preferences[k])
        difficulty_distribution, _ = self._get_level_distribution(user_level)
        
        quests = []
        # 2 quests from preferred category, 1 from others
        for i, difficulty in enumerate(difficulty_distribution):
            if i < 2:
                quest = self._select_quest_from_category(preferred_category, difficulty, user_level)
            else:
                # Select from remaining categories
                other_categories = [cat for cat in ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"] 
                                 if cat != preferred_category]
                category = random.choice(other_categories)
                quest = self._select_quest_from_category(category, difficulty, user_level)
            
            if quest:
                quests.append(quest)
        
        return quests
    
    def _get_random_quests(self, user_level: int) -> List[Dict[str, Any]]:
        """Completely random quest selection"""
        difficulty_distribution, _ = self._get_level_distribution(user_level)
        categories = ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"]
        
        quests = []
        for difficulty in difficulty_distribution:
            category = random.choice(categories)
            quest = self._select_quest_from_category(category, difficulty, user_level)
            if quest:
                quests.append(quest)
        
        return quests
    
    def _get_adaptive_quests(
        self, 
        user_level: int, 
        completion_history: Optional[List[Dict]] = None,
        preferences: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Adaptive quest selection based on completion history and preferences
        """
        if not completion_history:
            return self._get_balanced_quests(user_level)
        
        # Analyze completion patterns
        category_success_rates = self._analyze_completion_patterns(completion_history)
        
        # Adjust difficulty based on success rates
        difficulty_distribution, _ = self._get_level_distribution(user_level)
        adjusted_distribution = self._adjust_difficulty_distribution(
            difficulty_distribution, 
            category_success_rates
        )
        
        # Select categories based on preferences and success rates
        categories = self._select_adaptive_categories(category_success_rates, preferences)
        
        quests = []
        for category, difficulty in zip(categories, adjusted_distribution):
            quest = self._select_quest_from_category(category, difficulty, user_level)
            if quest:
                quests.append(quest)
        
        return quests
    
    def _analyze_completion_patterns(self, completion_history: List[Dict]) -> Dict[str, float]:
        """Analyze user's quest completion patterns"""
        category_stats = {}
        
        for quest_data in completion_history[-30:]:  # Last 30 quests
            category = quest_data.get('category', '').split(' - ')[0]  # Remove difficulty suffix
            if category not in category_stats:
                category_stats[category] = {'completed': 0, 'total': 0}
            
            category_stats[category]['total'] += 1
            if quest_data.get('status') == 'Completed':
                category_stats[category]['completed'] += 1
        
        # Calculate success rates
        success_rates = {}
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                success_rates[category] = stats['completed'] / stats['total']
            else:
                success_rates[category] = 0.5  # Default for no data
        
        return success_rates
    
    def _adjust_difficulty_distribution(
        self, 
        base_distribution: List[str], 
        success_rates: Dict[str, float]
    ) -> List[str]:
        """Adjust difficulty based on success rates"""
        avg_success_rate = sum(success_rates.values()) / len(success_rates) if success_rates else 0.5
        
        adjusted = []
        for difficulty in base_distribution:
            if avg_success_rate > 0.8:  # User is doing very well, increase difficulty
                if difficulty == "Easy":
                    adjusted.append("Medium")
                elif difficulty == "Medium":
                    adjusted.append("Hard")
                else:
                    adjusted.append(difficulty)
            elif avg_success_rate < 0.4:  # User is struggling, decrease difficulty
                if difficulty == "Hard":
                    adjusted.append("Medium")
                elif difficulty == "Medium":
                    adjusted.append("Easy")
                else:
                    adjusted.append(difficulty)
            else:
                adjusted.append(difficulty)
        
        return adjusted
    
    def _select_adaptive_categories(
        self, 
        success_rates: Dict[str, float], 
        preferences: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """Select categories based on success rates and preferences"""
        categories = ["🎵 Music Production", "📈 Business / Store", "🧘 Personal Growth"]
        
        if not success_rates and not preferences:
            return categories
        
        # Calculate weighted scores
        category_scores = {}
        for category in categories:
            score = 0.5  # Base score
            
            # Add success rate component (favor categories with moderate success)
            if category in success_rates:
                success_rate = success_rates[category]
                # Favor categories with 60-80% success rate
                if 0.6 <= success_rate <= 0.8:
                    score += 0.3
                elif success_rate < 0.4:  # Give struggling categories a chance
                    score += 0.1
            
            # Add preference component
            if preferences and category in preferences:
                score += preferences[category] * 0.4
            
            category_scores[category] = score
        
        # Sort by score and return in order
        sorted_categories = sorted(categories, key=lambda c: category_scores.get(c, 0.5), reverse=True)
        return sorted_categories
    
    def _select_quest_from_category(self, category: str, difficulty: str, user_level: int) -> Optional[Dict[str, Any]]:
        """Select a specific quest from category and difficulty"""
        if category not in QUEST_DATABASE or difficulty not in QUEST_DATABASE[category]:
            return None
        
        available_quests = QUEST_DATABASE[category][difficulty]
        if not available_quests:
            return None
        
        quest_template = random.choice(available_quests)
        rewards = self._calculate_rewards(difficulty, user_level)
        
        return {
            **quest_template,
            "xp_reward": rewards["xp"],
            "rune_reward": rewards["runes"],
            "category": f"{category} - {difficulty}",
            "difficulty": difficulty,
            "quest_type": "daily",
            "user_level_at_creation": user_level,
            "tags": quest_template.get("tags", []),
            "estimated_time": quest_template.get("estimated_time", "Unknown")
        }
    
    def _calculate_rewards(self, difficulty: str, level: int) -> Dict[str, int]:
        """Calculate rewards using the specified formulas"""
        formula = REWARD_FORMULAS.get(difficulty, REWARD_FORMULAS["Easy"])
        
        if difficulty == "Side":
            base_xp = random.randint(formula["xp_base_min"], formula["xp_base_max"])
            xp_reward = int(base_xp * (1 + formula["xp_scaling"] * level))
            rune_reward = random.randint(formula["runes_min"], formula["runes_max"])
        else:
            xp_reward = int(formula["xp_base"] * (1 + formula["xp_scaling"] * level))
            rune_reward = formula["runes"]
        
        return {"xp": xp_reward, "runes": rune_reward}
    
    def _get_level_distribution(self, level: int) -> Tuple[List[str], int]:
        """Get quest distribution for user level"""
        for tier_name, tier_data in LEVEL_QUEST_DISTRIBUTION.items():
            min_level, max_level = tier_data["levels"]
            if min_level <= level <= max_level:
                distribution = tier_data["distribution"]
                side_quests = tier_data["side_quests"]
                if isinstance(side_quests, tuple):
                    side_quest_count = random.randint(side_quests[0], side_quests[1])
                else:
                    side_quest_count = side_quests
                return distribution, side_quest_count
        
        # Fallback to master level
        master_data = LEVEL_QUEST_DISTRIBUTION["master"]
        return master_data["distribution"], random.randint(2, 3)
    
    def get_quest_analytics(self, completion_history: List[Dict]) -> Dict[str, Any]:
        """Generate quest completion analytics"""
        if not completion_history:
            return {"error": "No completion history available"}
        
        total_quests = len(completion_history)
        completed_quests = len([q for q in completion_history if q.get('status') == 'Completed'])
        completion_rate = completed_quests / total_quests if total_quests > 0 else 0
        
        # Category breakdown
        category_stats = {}
        difficulty_stats = {}
        
        for quest in completion_history:
            category = quest.get('category', '').split(' - ')[0]
            difficulty = quest.get('difficulty', 'Unknown')
            
            # Category stats
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'completed': 0}
            category_stats[category]['total'] += 1
            if quest.get('status') == 'Completed':
                category_stats[category]['completed'] += 1
            
            # Difficulty stats
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'total': 0, 'completed': 0}
            difficulty_stats[difficulty]['total'] += 1
            if quest.get('status') == 'Completed':
                difficulty_stats[difficulty]['completed'] += 1
        
        return {
            "total_quests": total_quests,
            "completed_quests": completed_quests,
            "completion_rate": completion_rate,
            "category_breakdown": category_stats,
            "difficulty_breakdown": difficulty_stats,
            "recommendations": self._generate_recommendations(category_stats, difficulty_stats)
        }
    
    def _generate_recommendations(self, category_stats: Dict, difficulty_stats: Dict) -> List[str]:
        """Generate recommendations based on completion patterns"""
        recommendations = []
        
        # Check category performance
        for category, stats in category_stats.items():
            if stats['total'] > 5:  # Only for categories with enough data
                rate = stats['completed'] / stats['total']
                if rate < 0.3:
                    recommendations.append(f"Consider focusing on {category} quests - low completion rate")
                elif rate > 0.9:
                    recommendations.append(f"Excellent performance in {category}! Try harder challenges")
        
        # Check difficulty performance
        for difficulty, stats in difficulty_stats.items():
            if stats['total'] > 3:
                rate = stats['completed'] / stats['total']
                if rate < 0.3:
                    recommendations.append(f"Consider easier {difficulty} quests")
                elif rate > 0.9:
                    recommendations.append(f"Ready for more challenging {difficulty} quests")
        
        return recommendations if recommendations else ["Keep up the great work!"]

# Global quest manager instance
quest_manager = QuestManager()