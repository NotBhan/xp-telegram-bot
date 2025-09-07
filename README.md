# XP Tracking Telegram Bot

A professional gamified Telegram bot that tracks user experience points (XP), quests, and inventory using Notion as a backend database. Built with Python 3.8+ and modern async practices.

---

## 🚀 Features

- **XP Tracking System**: Level up through XP gains with title progression
- **Quest Management**: Daily, weekly, and custom quest system with rewards
- **Inventory & Shop**: Item collection and trading system with runes currency
- **Streak System**: Daily activity tracking with bonus rewards
- **Notion Integration**: Seamless data persistence using Notion databases
- **Professional Architecture**: Modular design with proper error handling

---

## 🛠️ Tech Stack

- **Python 3.8+**
- **Aiogram 3.x** (Modern Telegram Bot Framework)
- **Notion API** (Database backend)
- **AsyncIO** (Asynchronous programming)
- **Python-dotenv** (Environment management)
- **HTTPX** (Modern HTTP client)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token from [BotFather](https://core.telegram.org/bots#botfather)
- Notion Integration Token from [Notion Integrations](https://www.notion.so/my-integrations)
- Notion workspace with required databases

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd xp-telegram-bot
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Notion Databases

Create the following databases in your Notion workspace:

#### XP Database
Required properties:
- `User ID` (Number)
- `Username` (Rich Text)
- `First Name` (Rich Text)
- `XP` (Number)
- `Level` (Number)
- `Runes` (Number)
- `Streak` (Number)
- `Max Streak` (Number)
- `Current Title` (Select: Novice, Apprentice, Expert, Master, Legend)
- `Active Buffs` (Multi-select)
- `Active Debuffs` (Multi-select)
- `Last Activity` (Date)
- `Last Quest Date` (Date)

#### Quest Database
Required properties:
- `Quest Name` (Title)
- `User ID` (Number)
- `Description` (Rich Text)
- `XP Reward` (Number)
- `Rune Reward` (Number)
- `Status` (Select: Active, Completed, Failed, Expired)
- `Category` (Select: 🎵 Music Production - Easy/Medium/Hard, 📈 Business / Store - Easy/Medium/Hard, 🧘 Personal Growth - Easy/Medium/Hard, 🌟 Side Quest)
- `Difficulty` (Select: Easy, Medium, Hard, Side)
- `Quest Type` (Select: daily, weekly, monthly, achievement)
- `User Level at Creation` (Number)
- `Tags` (Multi-select: creative, production, business, wellness, etc.)
- `Estimated Time` (Rich Text)
- `Created` (Date)
- `Due Date` (Date)

#### Inventory Database
Required properties:
- `Item Name` (Title)
- `User ID` (Number)
- `Type` (Select: Consumable, Equipment, Cosmetic, Boost, Material)
- `Rarity` (Select: Common, Uncommon, Rare, Epic, Legendary)
- `Description` (Rich Text)
- `Quantity` (Number)
- `Price` (Number)
- `Effect` (Rich Text)
- `Acquired` (Date)

### 5. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here

# Notion API Configuration
NOTION_TOKEN=your_notion_integration_token

# Notion Database IDs (copy from database URLs)
XP_DB_ID=your_xp_database_id
QUEST_DB_ID=your_quest_database_id
CHALLENGE_DB_ID=your_challenge_database_id
INVENTORY_DB_ID=your_inventory_database_id

# Optional Settings
BOT_NAME="XP Tracker Bot"
DEBUG=false
LOG_LEVEL=INFO
```

### 6. Run the Bot

```bash
# Development mode
python bot.py

# Or using module syntax
python -m bot
```

---

## 🎮 Gamification System

The bot features a comprehensive gamification system designed to motivate consistency and make daily progress fun:

### 💫 XP & Levels
- **Progressive Scaling**: XP requirements increase with each level (base 50 XP, +25% per level)
- **Overflow Handling**: Excess XP automatically carries over to the next level
- **Visual Progress**: Real-time progress bars show advancement toward next level
- **Level Rewards**: Bonus runes awarded for each level up (50 runes per level)

### 🔥 Streak System
- **Daily Consistency**: Build streaks by completing at least one quest per day
- **Milestone Bonuses**: Special rewards at 7, 30, and 100-day milestones
- **Streak Protection**: Special buffs can protect against streak loss
- **Progressive Penalties**: Missing days applies debuffs based on duration

### 💰 Runes (Currency)
Earn runes through:
- Quest completion (10-30 runes based on difficulty)
- Streak milestones (25-500 runes for major streaks)
- Level ups (50 runes per level)
- Challenge victories

Spend runes on:
- Consumable items in the shop
- Special boosts and power-ups
- Emergency streak protection

### 🏆 Titles & Trophies

#### **Titles** (Earned every 25 levels)
- **Level 1**: 🌱 Novice - "Beginning your journey"
- **Level 25**: 🎭 Apprentice of Shadows - "Mastering the basics" + Immune to Sluggish debuff
- **Level 50**: 🔨 Expert Craftsman - "Skilled in your domain" + Reduces debuff duration
- **Level 75**: 🔥 Master of Elements - "Command over fundamentals" + Immune to Chaos Penalty
- **Level 100**: 👑 Legendary Champion - "Reached the pinnacle" + Immune to all debuffs

#### **Trophies** (Permanent achievements)
- 🏃 **First Steps**: Complete your first quest
- ⚡ **Week Warrior**: Maintain a 7-day streak
- 🔥 **Unyielding Flame**: Complete a 30-day streak
- 🏆 **Quest Master**: Complete 100 quests
- 💰 **Rune Collector**: Accumulate 1000 runes
- 👑 **Level Champion**: Reach level 50

### ✨ Buffs (Earned Only)
Positive effects that enhance gameplay:
- **🧠 Focused Mind**: +10% XP gain for 7 days
- **🧢 Rune Magnet**: +5 Runes per quest for 5 days
- **🛡️ Debuff Shield**: Negates next debuff (14 days)
- **🛡️ Streak Guardian**: Protects streak for 24h (1 day)
- **⚔️ Quest Master**: Double quest rewards for 3 days

### ☠️ Debuffs (Applied for Failures)
Negative effects for missing streaks:
- **🐌 Sluggish**: -20% XP gain for 3 days (missing 1 day)
- **🌀 Chaos Penalty**: Rune gain halved for 5 days (missing 2-3 days)
- **💧 Rune Drain**: -2 Runes per quest for 2 days
- **💫 XP Reduction**: -30% XP gain (missing 4+ days)

### 📊 Dashboard Integration
The enhanced dashboard displays:
- Current level with XP progress bar
- Active buffs and debuffs with remaining duration
- Streak status and milestone progress
- Recent trophy achievements
- Next title requirements
- Comprehensive gamification status

---

The bot features a comprehensive quest system with multiple categories and difficulties:

### 🎵 Music Production Quests
- **Easy**: Loop creation, sample organization, basic mixing
- **Medium**: Song arrangement, sound layering, social sharing
- **Hard**: Full production, mastering, distribution

### 📈 Business / Store Quests  
- **Easy**: Communication, product updates, market research
- **Medium**: Content creation, promotional materials
- **Hard**: Product launches, marketing campaigns, networking

### 🧘 Personal Growth Quests
- **Easy**: Reading, meditation, journaling
- **Medium**: Exercise, focused work, skill development  
- **Hard**: Long-term projects, habit streaks, knowledge sharing

### 🌟 Side Quests
Random fun activities that appear occasionally:
- Nature recording, workspace cleaning
- Gratitude practices, teaching others
- Creative expression, community engagement

### ⚙️ Reward Formula
Rewards scale dynamically with your level:

- **Easy Quest**: `5 × (1 + 0.1 × level)` XP + 10 Runes
- **Medium Quest**: `10 × (1 + 0.15 × level)` XP + 20 Runes  
- **Hard Quest**: `15 × (1 + 0.2 × level)` XP + 30 Runes
- **Side Quest**: Randomized XP + Runes (scaled with level)

### 🎮 Quest Progression
As you level up, quest difficulty automatically adapts:
- **Levels 1-3**: Mostly easy quests to build habits
- **Levels 4-8**: Introduction of medium challenges
- **Levels 9-15**: Balanced mix of difficulties
- **Levels 16-25**: Focus on medium and hard quests
- **Levels 26-40**: Primarily challenging content
- **Levels 41+**: Expert-level quest distribution

### 🧠 Smart Quest Features

#### **Adaptive Quest Selection**
- Analyzes your completion history to create personalized quests
- Adjusts difficulty based on your success rates
- Focuses on categories where you need improvement
- Use `/adaptive` to get AI-powered quest recommendations

#### **Side Quest System**
- Randomly triggered based on your level and activity
- Higher-level players get more frequent side quests
- Bonus rewards for spontaneous completion
- Triggered automatically after completing main quests

#### **Quest Analytics**
- Detailed performance tracking with `/analytics`
- Category and difficulty breakdown
- Success rate analysis
- Personalized improvement recommendations
- 30-day completion history

#### **Integration Features**
- Pre-populated in Notion database with all metadata
- Difficulty categorization (Easy, Medium, Hard, Side)
- Random daily quest selection (1 Easy, 1 Medium, 1 Hard typical)
- Side quests triggered on interval days
- Tags and estimated time for better planning

---

### Basic Commands
- `/start` - Register your profile and begin your adventure
- `/dashboard` - View your stats, level, XP, and current status
- `/quests` - See available quests and complete them
- `/inventory` - Check your items and use consumables
- `/shop` - Browse and purchase items with runes
- `/refresh` - Get new daily quests
- `/analytics` - View detailed quest completion analytics
- `/adaptive` - Create personalized quests based on your history

### Gameplay Loop
1. **Start** with `/start` to create your profile
2. **Check quests** with `/quests` to see daily objectives
3. **Complete activities** in real life (exercise, reading, work, etc.)
4. **Mark quests complete** to earn XP and runes
5. **Level up** and unlock new titles and abilities
6. **Shop for items** to enhance your gameplay experience
7. **Maintain streaks** for bonus rewards

---

## 🛠️ Development

### Project Structure
```
xp-telegram-bot/
├── src/
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   ├── handlers/          # Command handlers
│   │   ├── start.py
│   │   ├── dashboard.py
│   │   ├── quests.py
│   │   ├── inventory.py
│   │   └── shop.py
│   ├── models/            # Data models
│   │   ├── user.py
│   │   ├── quest.py
│   │   └── item.py
│   ├── notion/            # Notion API client
│   │   └── notion_client.py
│   └── utils/             # Utility functions
│       ├── calculators.py
│       └── formatters.py
├── bot.py                 # Main bot entry point
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

### Code Quality Features
- **Type Hints**: Full type annotation support
- **Error Handling**: Comprehensive exception handling with retry logic
- **Logging**: Structured logging with configurable levels
- **Configuration**: Environment-based configuration management
- **Async/Await**: Modern asynchronous Python patterns
- **Modular Design**: Clean separation of concerns

---

## 📚 Troubleshooting

### Common Issues

#### "BOT_TOKEN not found" Error
- Ensure your `.env` file exists and contains the correct bot token
- Get a new token from [@BotFather](https://t.me/BotFather) if needed
- Check that the token starts with a number followed by a colon

#### "Notion API connection failed" Error
- Verify your `NOTION_TOKEN` is correct
- Ensure your Notion integration has access to the required databases
- Check that all database IDs are correctly copied from Notion URLs

#### Database Property Errors
- Verify all required properties exist in your Notion databases
- Check property names match exactly (case-sensitive)
- Ensure property types are correct (Number, Rich Text, Select, etc.)

#### Quest Creation Issues
- Check that the Quest database has all required properties
- Verify the bot has write access to the database
- Review logs for specific error messages

### Debug Mode
Enable debug mode for detailed logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Log Files
Check `bot.log` for detailed error information and debugging data.

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with proper tests
4. **Follow the code style**: Use type hints and proper error handling
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Add type hints to all functions
- Include proper error handling
- Write descriptive commit messages
- Update documentation for new features
- Test your changes thoroughly

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

If you encounter issues or have questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing [Issues](../../issues)
3. Create a new issue with detailed information
4. Include log files and error messages

---

## 🚀 Roadmap

- [ ] Web dashboard for quest management
- [ ] Achievement system
- [ ] Guild/team features
- [ ] Integration with fitness trackers
- [ ] Mobile app companion
- [ ] Advanced analytics and reporting

---

**Made with ❤️ for gamified productivity**