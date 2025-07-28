# Discord Voice Channel Bot

A Discord bot that monitors voice channels and disconnects users who are both self-muted and self-deafened, with whitelist capabilities and customizable messages.

## Features

- Automatically disconnects users who are both self-muted and self-deafened
- Whitelist system to exempt specific users
- Customizable kick messages
- Logging system for disconnections
- Join message notifications
- Modern Discord UI with slash commands
- Administrator-only controls

## Commands

All commands require administrator permissions:

- `/settings` - Opens the settings menu with UI buttons
- `/whitelist_add @user` - Add a user to the whitelist
- `/whitelist_remove @user` - Remove a user from the whitelist
- `/list_whitelist` - View all whitelisted users
- `/set_log_channel #channel` - Set the logging channel
- `/set_kick_message message` - Set custom kick message

## Docker Setup

The bot is available on Docker Hub:

```bash
docker pull skuldgerry/dc-bot:1.1.0
```

```yaml
services:
   discord-bot:
      image: skuldgerry/dc-bot:1.1.0
      restart: unless-stopped
      container_name: DC-BOT
      environment:
         - BOT_TOKEN=your_bot_token_here
      volumes:
         - ./config:/app/config
```


After starting the container, check the console logs for the bot's invite link. You can use this link to invite the bot to your server with all required permissions.

### Required Permissions

The bot requires the following permissions:
- Administrator (for command access)
- View Channels
- Send Messages
- Manage Messages
- Read Message History
- Move Members
- Send Messages in Threads

## Setup

1. Create a Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Get your bot token
3. Deploy using Docker:
   - Create a directory for the bot
   - Create a docker-compose.yml file with the example above
   - Run `docker-compose up -d`
4. Check the docker logs for the invite link:
   ```bash
   docker logs discord-bot
   ```
5. Use the invite link from the logs to add the bot to your server
6. Use `/settings` to configure the bot

## Configuration

The bot stores its configuration in the `config` directory, which is persisted through the Docker volume mount. Each server (guild) has its own configuration directory containing:
- settings.json: Bot settings, kick message, log channel
- whitelist.json: List of whitelisted users

## Support

For issues or suggestions, please open an issue on GitHub.

## Built With AI

This bot was developed with the assistance of OpenAI's AI technology. From implementing modern Discord features to solving specific challenges in the code, AI played a significant role in the development of this bot.

## License

This project is open source and available under the MIT License.
