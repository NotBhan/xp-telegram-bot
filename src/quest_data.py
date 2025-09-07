"""
Quest Data Configuration for XP Telegram Bot

This file contains all quest definitions organized by category and difficulty.
Modify this file to add new quests or update existing ones.
"""

# Quest categories with emojis and descriptions
QUEST_CATEGORIES = {
    "🎵 Music Production": {
        "description": "Creative and technical music-related tasks",
        "focus": "Artistic creation, technical skills, and music industry activities"
    },
    "📈 Business / Store": {
        "description": "Business development and marketing activities", 
        "focus": "Entrepreneurship, marketing, and professional growth"
    },
    "🧘 Personal Growth": {
        "description": "Self-improvement and wellness activities",
        "focus": "Health, learning, and personal development"
    },
    "🌟 Side Quests": {
        "description": "Fun and creative bonus activities",
        "focus": "Variety, creativity, and community engagement"
    }
}

# Comprehensive quest database
QUEST_DATABASE = {
    "🎵 Music Production": {
        "Easy": [
            {
                "name": "🥁 Make 1 loop",
                "description": "Create 1 loop (drums, melody, or texture)",
                "tags": ["creative", "production", "beginner"],
                "estimated_time": "15-30 minutes"
            },
            {
                "name": "📁 Organize samples",
                "description": "Organize 5 samples in your library",
                "tags": ["organization", "workflow", "maintenance"],
                "estimated_time": "10-20 minutes"
            },
            {
                "name": "🎚️ Adjust mix levels",
                "description": "Adjust mix levels on 1 track",
                "tags": ["mixing", "technical", "audio"],
                "estimated_time": "15-25 minutes"
            },
            {
                "name": "💿 Export draft",
                "description": "Export a 30-second draft idea",
                "tags": ["workflow", "output", "demo"],
                "estimated_time": "5-15 minutes"
            }
        ],
        "Medium": [
            {
                "name": "🎼 Finish arrangement",
                "description": "Finish arranging 1 full song idea",
                "tags": ["composition", "structure", "creative"],
                "estimated_time": "45-90 minutes"
            },
            {
                "name": "🔊 Layer sounds",
                "description": "Layer sounds for a richer texture",
                "tags": ["production", "depth", "creative"],
                "estimated_time": "30-60 minutes"
            },
            {
                "name": "📱 Post IG clip",
                "description": "Post a short clip on Instagram",
                "tags": ["social", "marketing", "sharing"],
                "estimated_time": "20-30 minutes"
            },
            {
                "name": "🥁 Design drum sounds",
                "description": "Design 2 original drum sounds",
                "tags": ["sound_design", "creative", "technical"],
                "estimated_time": "30-45 minutes"
            }
        ],
        "Hard": [
            {
                "name": "🎛️ Complete mixdown",
                "description": "Complete a full mixdown of a track",
                "tags": ["mixing", "technical", "professional"],
                "estimated_time": "2-4 hours"
            },
            {
                "name": "🎧 Master track",
                "description": "Master a finished track (basic mastering)",
                "tags": ["mastering", "technical", "finalizing"],
                "estimated_time": "1-2 hours"
            },
            {
                "name": "📦 Build sample pack",
                "description": "Build a mini sample pack (5–10 sounds)",
                "tags": ["production", "package", "commercial"],
                "estimated_time": "3-5 hours"
            },
            {
                "name": "🚀 Submit track",
                "description": "Submit track to streaming platform or share online",
                "tags": ["distribution", "publishing", "milestone"],
                "estimated_time": "30-60 minutes"
            }
        ]
    },
    "📈 Business / Store": {
        "Easy": [
            {
                "name": "💬 Reply to messages",
                "description": "Reply to 1 message or comment",
                "tags": ["communication", "customer_service", "engagement"],
                "estimated_time": "5-10 minutes"
            },
            {
                "name": "📝 Update product",
                "description": "Update 1 product description in your store",
                "tags": ["content", "marketing", "optimization"],
                "estimated_time": "10-20 minutes"
            },
            {
                "name": "🔍 Research trends",
                "description": "Research 1 trending audio niche",
                "tags": ["research", "market_analysis", "trends"],
                "estimated_time": "15-30 minutes"
            }
        ],
        "Medium": [
            {
                "name": "🎬 Create promo",
                "description": "Create and post a promo reel/story",
                "tags": ["content_creation", "marketing", "video"],
                "estimated_time": "45-90 minutes"
            },
            {
                "name": "🎨 Design cover art",
                "description": "Design cover art for 1 sample pack",
                "tags": ["design", "visual", "branding"],
                "estimated_time": "60-120 minutes"
            },
            {
                "name": "✍️ Write blog post",
                "description": "Write a blog or description post about your work",
                "tags": ["content", "writing", "storytelling"],
                "estimated_time": "45-90 minutes"
            }
        ],
        "Hard": [
            {
                "name": "🚀 Launch sample pack",
                "description": "Launch a new sample pack",
                "tags": ["product_launch", "business", "milestone"],
                "estimated_time": "2-4 hours"
            },
            {
                "name": "📸 IG content streak",
                "description": "Run a week-long IG content streak",
                "tags": ["consistency", "marketing", "long_term"],
                "estimated_time": "7 days"
            },
            {
                "name": "🤝 Reach collaborators",
                "description": "Reach out to 3 potential collaborators",
                "tags": ["networking", "collaboration", "outreach"],
                "estimated_time": "60-90 minutes"
            }
        ]
    },
    "🧘 Personal Growth": {
        "Easy": [
            {
                "name": "📖 Read 5 pages",
                "description": "Read 5 pages of a book",
                "tags": ["learning", "reading", "knowledge"],
                "estimated_time": "10-15 minutes"
            },
            {
                "name": "🧘‍♂️ Meditate 5min",
                "description": "Meditate for 5 minutes",
                "tags": ["mindfulness", "wellness", "mental_health"],
                "estimated_time": "5 minutes"
            },
            {
                "name": "📔 Quick journal",
                "description": "Journal 3 sentences",
                "tags": ["reflection", "writing", "self_awareness"],
                "estimated_time": "5-10 minutes"
            }
        ],
        "Medium": [
            {
                "name": "💪 Exercise 30min",
                "description": "Exercise for 30 minutes",
                "tags": ["fitness", "health", "physical"],
                "estimated_time": "30 minutes"
            },
            {
                "name": "🎯 Deep work session",
                "description": "Complete a deep work session (90 minutes focus)",
                "tags": ["productivity", "focus", "skill_building"],
                "estimated_time": "90 minutes"
            },
            {
                "name": "🎼 Study theory",
                "description": "Study music theory or production for 30 minutes",
                "tags": ["learning", "music", "skill_building"],
                "estimated_time": "30 minutes"
            }
        ],
        "Hard": [
            {
                "name": "📚 Finish book",
                "description": "Finish a full book",
                "tags": ["learning", "commitment", "milestone"],
                "estimated_time": "Multiple sessions"
            },
            {
                "name": "🔥 7-day streak",
                "description": "Take on a 7-day streak of daily meditation/journaling",
                "tags": ["consistency", "habit_building", "long_term"],
                "estimated_time": "7 days"
            },
            {
                "name": "🎓 Build tutorial",
                "description": "Build and share a tutorial/resource",
                "tags": ["teaching", "content_creation", "knowledge_sharing"],
                "estimated_time": "2-4 hours"
            }
        ]
    },
    "🌟 Side Quests": {
        "Side": [
            {
                "name": "🚶‍♂️ Record nature sounds",
                "description": "Take a walk outside and record 3 natural sounds",
                "tags": ["nature", "creativity", "field_recording"],
                "estimated_time": "30-60 minutes"
            },
            {
                "name": "😄 Share meme",
                "description": "Share a meme related to music/production",
                "tags": ["humor", "community", "social"],
                "estimated_time": "5-10 minutes"
            },
            {
                "name": "🙏 Gratitude list",
                "description": "Write down 3 things you're grateful for",
                "tags": ["gratitude", "mindfulness", "positivity"],
                "estimated_time": "5-10 minutes"
            },
            {
                "name": "🧹 Clean workspace",
                "description": "Clean your workspace before working",
                "tags": ["organization", "productivity", "environment"],
                "estimated_time": "15-30 minutes"
            },
            {
                "name": "👨‍🏫 Teach something",
                "description": "Teach someone 1 small thing you learned today",
                "tags": ["teaching", "sharing", "community"],
                "estimated_time": "10-20 minutes"
            }
        ]
    }
}

# Reward formulas based on difficulty and level
REWARD_FORMULAS = {
    "Easy": {
        "xp_base": 5,
        "xp_scaling": 0.1,
        "runes": 10
    },
    "Medium": {
        "xp_base": 10,
        "xp_scaling": 0.15,
        "runes": 20
    },
    "Hard": {
        "xp_base": 15,
        "xp_scaling": 0.2,
        "runes": 30
    },
    "Side": {
        "xp_base_min": 8,
        "xp_base_max": 12,
        "xp_scaling": 0.12,
        "runes_min": 15,
        "runes_max": 25
    }
}

# Level-based quest distribution
LEVEL_QUEST_DISTRIBUTION = {
    "beginner": {
        "levels": (1, 3),
        "distribution": ["Easy", "Easy", "Easy"],
        "side_quests": 1
    },
    "novice": {
        "levels": (4, 8),
        "distribution": ["Easy", "Easy", "Medium"],
        "side_quests": (1, 2)
    },
    "intermediate": {
        "levels": (9, 15),
        "distribution": ["Easy", "Medium", "Medium"],
        "side_quests": (1, 2)
    },
    "advanced": {
        "levels": (16, 25),
        "distribution": ["Medium", "Medium", "Hard"],
        "side_quests": (1, 3)
    },
    "expert": {
        "levels": (26, 40),
        "distribution": ["Medium", "Hard", "Hard"],
        "side_quests": (2, 3)
    },
    "master": {
        "levels": (41, float('inf')),
        "distribution": ["Hard", "Hard", "Hard"],
        "side_quests": (2, 3)
    }
}