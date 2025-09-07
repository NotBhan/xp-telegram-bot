"""
Side Quest System for XP Telegram Bot

This module implements the randomized Side Quest system with bonus rewards
and variety mechanics as specified in the requirements.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .quest_system import Quest, QuestType, QuestDifficulty, QuestStatus

logger = logging.getLogger(__name__)

class SideQuestTrigger(Enum):
    """Different triggers for side quest appearance"""
    DAILY_RANDOM = "daily_random"      # Random chance each day
    STREAK_REWARD = "streak_reward"    # Reward for maintaining streaks
    LEVEL_MILESTONE = "level_milestone" # Appears at level milestones
    MANUAL_REQUEST = "manual_request"   # User manually requests via /sidequest
    SURPRISE = "surprise"              # Completely random surprise

class SideQuestTheme(Enum):
    """Thematic categories for side quests"""
    CREATIVITY = "creativity"           # Creative exploration
    WELLNESS = "wellness"              # Health and mindfulness
    SOCIAL = "social"                  # Community and connection
    LEARNING = "learning"              # Education and skill building
    FUN = "fun"                        # Light-hearted activities
    CHALLENGE = "challenge"            # Unique challenges

class SideQuestManager:
    """
    Advanced Side Quest System with randomization, themes, and bonus rewards
    """
    
    # Comprehensive side quest templates organized by theme and difficulty
    SIDE_QUEST_CATALOG = {
        SideQuestTheme.CREATIVITY: {
            QuestDifficulty.EASY: [
                {"name": "Sketch something random in 5 minutes", "description": "Draw or sketch anything that comes to mind", "tags": ["art", "quick"]},
                {"name": "Record 3 natural sounds", "description": "Capture interesting sounds from your environment", "tags": ["audio", "nature"]},
                {"name": "Write a haiku about your mood", "description": "Create a short poem reflecting how you feel", "tags": ["writing", "poetry"]},
                {"name": "Take a creative photo", "description": "Capture something beautiful or interesting", "tags": ["photography", "art"]},
                {"name": "Hum a melody and record it", "description": "Create a simple tune and save it", "tags": ["music", "melody"]}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Try a new creative technique", "description": "Experiment with an unfamiliar production method", "tags": ["learning", "technique"]},
                {"name": "Create a 30-second story", "description": "Write or record a very short story", "tags": ["writing", "storytelling"]},
                {"name": "Make a beat with household items", "description": "Create rhythm using objects around you", "tags": ["music", "experimental"]},
                {"name": "Design a simple logo or icon", "description": "Create a visual design for something", "tags": ["design", "visual"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Create art in a style you've never tried", "description": "Explore a completely new artistic medium", "tags": ["exploration", "challenge"]},
                {"name": "Collaborate with AI on a creative project", "description": "Use AI tools to enhance your creativity", "tags": ["AI", "collaboration", "modern"]}
            ]
        },
        
        SideQuestTheme.WELLNESS: {
            QuestDifficulty.EASY: [
                {"name": "Take a 20 min nature walk", "description": "Go outside and enjoy nature for 20 minutes", "tags": ["nature", "exercise"]},
                {"name": "Try 10 minutes of meditation", "description": "Practice mindfulness meditation", "tags": ["mindfulness", "mental_health"]},
                {"name": "Write down 3 things you're grateful for", "description": "Practice gratitude journaling", "tags": ["gratitude", "positivity"]},
                {"name": "Do 5 minutes of stretching", "description": "Stretch your body and relax", "tags": ["physical", "relaxation"]},
                {"name": "Drink a full glass of water mindfully", "description": "Focus completely on hydrating", "tags": ["hydration", "mindfulness"]}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Take a cold shower", "description": "Challenge yourself with cold water therapy", "tags": ["challenge", "health"]},
                {"name": "Practice breathing exercises for 15 minutes", "description": "Focus on controlled breathing techniques", "tags": ["breathing", "wellness"]},
                {"name": "Organize your workspace mindfully", "description": "Clean and arrange your creative space intentionally", "tags": ["organization", "environment"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Try a new form of exercise", "description": "Explore a physical activity you've never done", "tags": ["fitness", "exploration"]},
                {"name": "Practice digital detox for 2 hours", "description": "Disconnect from all devices and be present", "tags": ["detox", "mindfulness"]}
            ]
        },
        
        SideQuestTheme.SOCIAL: {
            QuestDifficulty.EASY: [
                {"name": "Reach out to an old friend and check in", "description": "Send a message to reconnect with someone", "tags": ["friendship", "connection"]},
                {"name": "Share a music meme", "description": "Post a funny music-related meme", "tags": ["humor", "community"]},
                {"name": "Give someone a genuine compliment", "description": "Make someone's day with kind words", "tags": ["kindness", "positivity"]},
                {"name": "Comment thoughtfully on someone's post", "description": "Engage meaningfully with someone's content", "tags": ["engagement", "support"]}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Teach someone 1 small thing", "description": "Share knowledge you learned today", "tags": ["teaching", "sharing"]},
                {"name": "Ask for feedback on your work", "description": "Get input from someone you trust", "tags": ["feedback", "growth"]},
                {"name": "Join a community discussion", "description": "Participate in an online or offline group conversation", "tags": ["community", "discussion"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Start a creative collaboration", "description": "Reach out to begin a joint project", "tags": ["collaboration", "initiative"]},
                {"name": "Mentor someone for 30 minutes", "description": "Share your expertise to help someone grow", "tags": ["mentoring", "leadership"]}
            ]
        },
        
        SideQuestTheme.LEARNING: {
            QuestDifficulty.EASY: [
                {"name": "Learn 5 new words in another language", "description": "Expand your vocabulary", "tags": ["language", "education"]},
                {"name": "Watch a 10-minute educational video", "description": "Learn something new from YouTube or similar", "tags": ["video", "education"]},
                {"name": "Read about an artist you don't know", "description": "Discover someone new in your field", "tags": ["research", "inspiration"]},
                {"name": "Learn one new keyboard shortcut", "description": "Improve your workflow efficiency", "tags": ["productivity", "tools"]}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Try a new software or app", "description": "Explore a tool you've never used", "tags": ["technology", "tools"]},
                {"name": "Read an article about your industry", "description": "Stay updated with industry knowledge", "tags": ["industry", "reading"]},
                {"name": "Study a song structure you admire", "description": "Analyze how your favorite track is built", "tags": ["analysis", "music_theory"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Complete a micro-course online", "description": "Finish a short educational program", "tags": ["course", "certification"]},
                {"name": "Reverse-engineer a technique", "description": "Figure out how something was made", "tags": ["analysis", "reverse_engineering"]}
            ]
        },
        
        SideQuestTheme.FUN: {
            QuestDifficulty.EASY: [
                {"name": "Dance to your favorite song", "description": "Let loose and move to music", "tags": ["dancing", "joy"]},
                {"name": "Make a silly face in the mirror", "description": "Embrace your playful side", "tags": ["humor", "self_expression"]},
                {"name": "Play with a pet for 10 minutes", "description": "Enjoy animal companionship", "tags": ["pets", "play"]},
                {"name": "Tell yourself a joke", "description": "Make yourself laugh", "tags": ["humor", "self_care"]}
            ],
            QuestDifficulty.MEDIUM: [
                {"name": "Create a funny remix of a serious song", "description": "Add humor to existing music", "tags": ["remix", "humor"]},
                {"name": "Have a conversation with yourself", "description": "Practice being your own best friend", "tags": ["self_talk", "reflection"]},
                {"name": "Sing in a silly voice", "description": "Experiment with vocal expression", "tags": ["vocals", "play"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Create a parody of something popular", "description": "Make a humorous version of trending content", "tags": ["parody", "creativity"]},
                {"name": "Invent a new genre name", "description": "Come up with the next big music category", "tags": ["innovation", "naming"]}
            ]
        },
        
        SideQuestTheme.CHALLENGE: {
            QuestDifficulty.MEDIUM: [
                {"name": "Create something in under 5 minutes", "description": "Speed creativity challenge", "tags": ["speed", "pressure"]},
                {"name": "Use only 3 sounds to make a beat", "description": "Constraint-based creation", "tags": ["constraints", "minimalism"]},
                {"name": "Work standing up for 30 minutes", "description": "Change your physical working position", "tags": ["posture", "change"]}
            ],
            QuestDifficulty.RARE: [
                {"name": "Create music using only your voice", "description": "Make a track with vocal sounds only", "tags": ["vocals", "acapella"]},
                {"name": "Produce backwards (start with mastering)", "description": "Reverse your normal workflow", "tags": ["workflow", "reverse"]},
                {"name": "Make a track in a genre you dislike", "description": "Challenge your musical comfort zone", "tags": ["genre", "discomfort_zone"]},
                {"name": "Create something with your non-dominant hand", "description": "Use your opposite hand for creative work", "tags": ["dexterity", "challenge"]}
            ]
        }
    }
    
    @staticmethod
    def calculate_side_quest_rewards(difficulty: QuestDifficulty, trigger: SideQuestTrigger) -> Dict[str, int]:
        """
        Calculate randomized rewards for side quests with bonus multipliers:
        - Base ranges per difficulty
        - Trigger-based multipliers
        - Random variance for excitement
        """
        
        # Base reward ranges per difficulty (as per specification)
        base_ranges = {
            QuestDifficulty.EASY: {"xp": (5, 15), "runes": (10, 30)},
            QuestDifficulty.MEDIUM: {"xp": (10, 25), "runes": (20, 50)},
            QuestDifficulty.HARD: {"xp": (20, 40), "runes": (40, 80)},
            QuestDifficulty.RARE: {"xp": (50, 75), "runes": (100, 150)}
        }
        
        # Get base range
        xp_range = base_ranges[difficulty]["xp"]
        rune_range = base_ranges[difficulty]["runes"]
        
        # Generate base rewards
        base_xp = random.randint(xp_range[0], xp_range[1])
        base_runes = random.randint(rune_range[0], rune_range[1])
        
        # Apply trigger-based multipliers
        multipliers = {
            SideQuestTrigger.DAILY_RANDOM: 1.0,
            SideQuestTrigger.STREAK_REWARD: 1.3,    # 30% bonus for streak rewards
            SideQuestTrigger.LEVEL_MILESTONE: 1.5,  # 50% bonus for milestones
            SideQuestTrigger.MANUAL_REQUEST: 0.9,   # 10% penalty for manual requests
            SideQuestTrigger.SURPRISE: 1.8          # 80% bonus for surprise quests
        }
        
        multiplier = multipliers.get(trigger, 1.0)
        
        # Apply random variance (±10%)
        variance = random.uniform(0.9, 1.1)
        final_multiplier = multiplier * variance
        
        final_xp = int(base_xp * final_multiplier)
        final_runes = int(base_runes * final_multiplier)
        
        return {
            "xp": final_xp,
            "runes": final_runes,
            "base_xp": base_xp,
            "base_runes": base_runes,
            "multiplier": final_multiplier,
            "trigger": trigger.value
        }
    
    @staticmethod
    def should_trigger_side_quest(
        user_level: int,
        current_streak: int,
        last_side_quest_date: Optional[datetime] = None,
        trigger_type: SideQuestTrigger = SideQuestTrigger.DAILY_RANDOM
    ) -> bool:
        """Determine if a side quest should be triggered based on various factors"""
        
        if trigger_type == SideQuestTrigger.MANUAL_REQUEST:
            return True  # Always honor manual requests
        
        # Check cooldown (minimum 1 day between side quests)
        if last_side_quest_date:
            hours_since = (datetime.now() - last_side_quest_date).total_seconds() / 3600
            if hours_since < 24:
                return False
        
        # Calculate base probability based on trigger type
        base_probabilities = {
            SideQuestTrigger.DAILY_RANDOM: 0.25,      # 25% daily chance
            SideQuestTrigger.STREAK_REWARD: 0.8,      # 80% chance for streak rewards
            SideQuestTrigger.LEVEL_MILESTONE: 0.9,    # 90% chance for milestones
            SideQuestTrigger.SURPRISE: 0.05           # 5% chance for true surprises
        }
        
        base_probability = base_probabilities.get(trigger_type, 0.25)
        
        # Adjust probability based on user level (higher levels get more frequent side quests)
        level_bonus = min(user_level * 0.01, 0.15)  # Max 15% bonus
        
        # Streak bonus
        streak_bonus = 0
        if current_streak >= 7:
            streak_bonus = 0.1  # 10% bonus for week+ streaks
        if current_streak >= 30:
            streak_bonus = 0.2  # 20% bonus for month+ streaks
        
        # Time since last side quest bonus
        time_bonus = 0
        if last_side_quest_date:
            days_since = (datetime.now() - last_side_quest_date).days
            if days_since >= 3:
                time_bonus = 0.2
            elif days_since >= 7:
                time_bonus = 0.4
        
        final_probability = base_probability + level_bonus + streak_bonus + time_bonus
        final_probability = min(final_probability, 0.95)  # Cap at 95%
        
        return random.random() < final_probability
    
    @staticmethod
    def generate_side_quest(
        user_level: int,
        trigger: SideQuestTrigger = SideQuestTrigger.DAILY_RANDOM,
        preferred_theme: Optional[SideQuestTheme] = None,
        excluded_themes: List[SideQuestTheme] = None
    ) -> Quest:
        """Generate a randomized side quest with specified parameters"""
        
        if excluded_themes is None:
            excluded_themes = []
        
        # Select theme
        available_themes = [theme for theme in SideQuestTheme if theme not in excluded_themes]
        
        if preferred_theme and preferred_theme in available_themes:
            selected_theme = preferred_theme
        else:
            # Weight themes based on user level
            theme_weights = {
                SideQuestTheme.FUN: 1.0,
                SideQuestTheme.CREATIVITY: 1.2,
                SideQuestTheme.WELLNESS: 1.0,
                SideQuestTheme.SOCIAL: 0.8,
                SideQuestTheme.LEARNING: 1.0 + (user_level * 0.02),  # Increases with level
                SideQuestTheme.CHALLENGE: 0.5 + (user_level * 0.03)  # Increases more with level
            }
            
            weighted_themes = []
            for theme in available_themes:
                weight = theme_weights.get(theme, 1.0)
                weighted_themes.extend([theme] * int(weight * 10))
            
            selected_theme = random.choice(weighted_themes)
        
        # Select difficulty based on trigger and user level
        if trigger == SideQuestTrigger.SURPRISE:
            # Surprise quests can be rare
            difficulty_weights = [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.RARE]
            difficulty = random.choice(difficulty_weights)
        elif user_level >= 20:
            # Higher level users get harder side quests
            difficulty = random.choices(
                [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.RARE],
                weights=[20, 60, 20]
            )[0]
        else:
            # Lower level users get easier side quests
            difficulty = random.choices(
                [QuestDifficulty.EASY, QuestDifficulty.MEDIUM],
                weights=[60, 40]
            )[0]
        
        # Get quest template
        theme_catalog = SideQuestManager.SIDE_QUEST_CATALOG.get(selected_theme, {})
        difficulty_quests = theme_catalog.get(difficulty, [])
        
        # Fallback to easier difficulty if none available
        if not difficulty_quests and difficulty == QuestDifficulty.RARE:
            difficulty_quests = theme_catalog.get(QuestDifficulty.MEDIUM, [])
            difficulty = QuestDifficulty.MEDIUM
        
        if not difficulty_quests:
            difficulty_quests = theme_catalog.get(QuestDifficulty.EASY, [])
            difficulty = QuestDifficulty.EASY
        
        if not difficulty_quests:
            # Ultimate fallback - use a simple default
            template = {
                "name": "Take a moment to appreciate something beautiful",
                "description": "Find beauty in your current environment",
                "tags": ["mindfulness", "appreciation"]
            }
        else:
            template = random.choice(difficulty_quests)
        
        # Calculate rewards
        rewards = SideQuestManager.calculate_side_quest_rewards(difficulty, trigger)
        
        # Create quest object
        quest = Quest(
            name=template["name"],
            quest_id="SQ1",
            description=template["description"],
            difficulty=difficulty,
            quest_type=QuestType.SIDE,
            xp_reward=rewards["xp"],
            rune_reward=rewards["runes"],
            category=f"🌟 Side Quests - {selected_theme.value.title()}",
            tags=template.get("tags", []) + [trigger.value, selected_theme.value],
            estimated_time="Variable",
            assigned_date=datetime.now(),
            user_level_at_creation=user_level
        )
        
        return quest
    
    @staticmethod
    def get_side_quest_analytics(completed_side_quests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user's side quest completion patterns"""
        
        if not completed_side_quests:
            return {"error": "No side quest history available"}
        
        total_completed = len(completed_side_quests)
        
        # Theme preferences
        theme_counts = {}
        difficulty_counts = {}
        trigger_counts = {}
        
        total_xp = 0
        total_runes = 0
        
        for quest in completed_side_quests:
            # Extract theme from category or tags
            category = quest.get("category", "")
            tags = quest.get("tags", [])
            
            # Count themes
            for theme in SideQuestTheme:
                if theme.value in category.lower() or theme.value in tags:
                    theme_counts[theme.value] = theme_counts.get(theme.value, 0) + 1
                    break
            
            # Count difficulties
            difficulty = quest.get("difficulty", "Easy")
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            
            # Count triggers
            for tag in tags:
                if any(trigger.value == tag for trigger in SideQuestTrigger):
                    trigger_counts[tag] = trigger_counts.get(tag, 0) + 1
                    break
            
            # Accumulate rewards
            total_xp += quest.get("xp_reward", 0)
            total_runes += quest.get("rune_reward", 0)
        
        # Calculate preferences (most common themes)
        preferred_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_side_quests_completed": total_completed,
            "total_xp_from_side_quests": total_xp,
            "total_runes_from_side_quests": total_runes,
            "average_xp_per_side_quest": total_xp / total_completed if total_completed > 0 else 0,
            "average_runes_per_side_quest": total_runes / total_completed if total_completed > 0 else 0,
            "theme_distribution": theme_counts,
            "difficulty_distribution": difficulty_counts,
            "trigger_distribution": trigger_counts,
            "preferred_themes": preferred_themes,
            "recommendations": SideQuestManager._generate_side_quest_recommendations(
                theme_counts, difficulty_counts, total_completed
            )
        }
    
    @staticmethod
    def _generate_side_quest_recommendations(
        theme_counts: Dict[str, int],
        difficulty_counts: Dict[str, int],
        total_completed: int
    ) -> List[str]:
        """Generate personalized side quest recommendations"""
        recommendations = []
        
        if total_completed < 5:
            recommendations.append("Try completing more side quests to unlock personalized recommendations!")
            return recommendations
        
        # Analyze theme preferences
        if theme_counts:
            most_common_theme = max(theme_counts, key=theme_counts.get)
            least_common_themes = [theme for theme, count in theme_counts.items() if count <= 1]
            
            recommendations.append(f"You enjoy {most_common_theme} side quests! More are available.")
            
            if least_common_themes:
                recommendations.append(f"Try exploring: {', '.join(least_common_themes[:2])} for variety.")
        
        # Analyze difficulty preferences
        if difficulty_counts:
            easy_count = difficulty_counts.get("Easy", 0)
            rare_count = difficulty_counts.get("Rare", 0)
            
            if rare_count == 0 and total_completed >= 10:
                recommendations.append("Ready for a rare side quest challenge?")
            elif easy_count / total_completed > 0.7:
                recommendations.append("Consider trying medium difficulty side quests for better rewards!")
        
        return recommendations if recommendations else ["Keep exploring side quests for variety and bonus rewards!"]
    
    @staticmethod
    def get_next_side_quest_suggestion(
        user_level: int,
        completion_history: List[Dict[str, Any]],
        current_streak: int,
        last_side_quest_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get intelligent suggestion for next side quest"""
        
        suggestion = {
            "should_offer": False,
            "trigger_type": None,
            "recommended_theme": None,
            "estimated_rewards": {},
            "reason": ""
        }
        
        # Check if we should offer a side quest
        current_time = datetime.now()
        
        # Streak-based triggers
        if current_streak > 0 and current_streak % 7 == 0:  # Every 7 days
            suggestion["should_offer"] = True
            suggestion["trigger_type"] = SideQuestTrigger.STREAK_REWARD
            suggestion["reason"] = f"Reward for {current_streak}-day streak!"
        
        # Level milestone triggers
        elif user_level > 0 and user_level % 10 == 0:  # Every 10 levels
            suggestion["should_offer"] = True
            suggestion["trigger_type"] = SideQuestTrigger.LEVEL_MILESTONE
            suggestion["reason"] = f"Celebration for reaching level {user_level}!"
        
        # Daily random chance
        elif SideQuestManager.should_trigger_side_quest(
            user_level, current_streak, last_side_quest_date, SideQuestTrigger.DAILY_RANDOM
        ):
            suggestion["should_offer"] = True
            suggestion["trigger_type"] = SideQuestTrigger.DAILY_RANDOM
            suggestion["reason"] = "Random side quest opportunity!"
        
        # Surprise chance (very rare)
        elif random.random() < 0.02:  # 2% chance
            suggestion["should_offer"] = True
            suggestion["trigger_type"] = SideQuestTrigger.SURPRISE
            suggestion["reason"] = "🎉 Surprise side quest appeared!"
        
        if suggestion["should_offer"]:
            # Analyze completion history for theme recommendation
            if completion_history:
                analytics = SideQuestManager.get_side_quest_analytics(completion_history)
                if analytics.get("preferred_themes"):
                    # Sometimes suggest preferred theme, sometimes suggest new theme
                    if random.random() < 0.6:  # 60% chance for preferred
                        preferred_theme_name = analytics["preferred_themes"][0][0]
                        for theme in SideQuestTheme:
                            if theme.value == preferred_theme_name:
                                suggestion["recommended_theme"] = theme
                                break
            
            # Estimate rewards
            difficulty = QuestDifficulty.MEDIUM  # Default estimation
            rewards = SideQuestManager.calculate_side_quest_rewards(
                difficulty, suggestion["trigger_type"]
            )
            suggestion["estimated_rewards"] = rewards
        
        return suggestion