# XP Tracking Telegram Bot with Notion Integration

This Telegram bot helps you track your experience points (XP), level up, and manage your progress using a Notion database as a backend. It's designed to be a fun and interactive way to gamify your tasks and goals.

## Features

- **XP Tracking**: Automatically track your XP and level.
- **Gamified Progression**: Level up and earn titles as you gain XP.
- **Quest System**: Complete daily and weekly quests for bonus XP.
- **Shop & Inventory**: Purchase items with in-game currency (runes) and manage your inventory.
- **Notion Backend**: All your data is stored and managed in a Notion database.
- **Interactive Dashboard**: A beautiful and user-friendly dashboard to view your stats.

## Bot Commands

- `/start` - Start the bot and create your profile.
- `/dashboard` - View your current XP, level, and progress.
- `/quests` - View and complete available quests.
- `/shop` - Browse and purchase items from the shop.
- `/inventory` - View and use items from your inventory.

## Notion Integration

The bot uses a Notion database to store user data, including:

- User profiles (XP, level, runes, etc.)
- Quests and their completion status
- Inventory and purchased items

## Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/your-username/xp-telegram-bot.git
   cd xp-telegram-bot
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up your Notion database**:
   - Duplicate the [Notion template](https://www.notion.so/your-template-link) to your Notion workspace.
   - Create a Notion integration and get your `NOTION_TOKEN`.
   - Get the `DATABASE_ID` for each of the duplicated databases (Users, Quests, Inventory).

4. **Create a Telegram bot**:
   - Talk to the [BotFather](https://t.me/botfather) on Telegram to create a new bot.
   - Get your `TELEGRAM_BOT_TOKEN`.

5. **Configure environment variables**:
   - Create a `.env` file by copying the `.env.example` file:
     ```
     cp .env.example .env
     ```
   - Add your tokens and database IDs to the `.env` file.

## Running the Bot

Once you've completed the setup, you can run the bot with the following command:

```
python src/bot.py
```

## Development

To install the development dependencies, run:

```
_**`pip install -r requirements-dev.txt`**_
```

This will install `black` for code formatting. Before committing, run `black .` to format the code.

## Configuration

All configuration is done through the `.env` file. The following variables are available:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
- `NOTION_TOKEN`: Your Notion integration token.
- `NOTION_USERS_DB_ID`: The ID of your Notion Users database.
- `NOTION_QUESTS_DB_ID`: The ID of your Notion Quests database.
- `NOTION_INVENTORY_DB_ID`: The ID of your Notion Inventory database.

## Troubleshooting

- **Bot not starting**: Check that your `TELEGRAM_BOT_TOKEN` is correct.
- **Error connecting to Notion**: Ensure your `NOTION_TOKEN` and `DATABASE_ID`s are correct and that your integration has access to the databases.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Support

If you have any questions or need help, feel free to open an issue.

## Acknowledgements

- [aiogram](https://github.com/aiogram/aiogram)
- [notion-client](https://github.com/ramnes/notion-sdk-py)