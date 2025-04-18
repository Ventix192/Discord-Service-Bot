
# Discord Serivce Bot

This modular Python-based Discord bot offers functionality for server welcoming, verification, ticket management, statistics, and chat exports. It is fully configurable and ideal for community and support-focused servers.

## Features

- Welcome messages for new members with structured embeds  
- Verification system using interactive buttons  
- Ticket system with creation, reopen, and management options  
- Automated server statistics updater  
- Chat export functionality using `chat_exporter`  
- Configuration-based module activation  
- Embed messages with server branding and structure  
- View and interaction-based component handling

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Bot

Adjust the `config.py` file to fit your server. Enable or disable modules and define channel IDs, colors, and other settings.

### 3. Start the Bot

```bash
python bot.py
```

## How It Works

- When a user joins the server, a welcome embed is sent to a configured channel.  
- The verify system adds a button for members to confirm their identity (if enabled).  
- The ticket system allows users to open support tickets and optionally reopen closed ones.  
- Server statistics are updated regularly if the feature is enabled.  
- Chat exports can be triggered and are handled via the `chat_exporter` module.  
- All modules are loaded dynamically depending on the configuration.

## Future Enhancements

- GeoIP integration for login origin tracking  
- Persistent database support for ticket logs  
- Event management and announcements  
- Auto-moderation functionality

## Troubleshooting

### Slash commands or buttons not working?
- Ensure Discord intents are correctly set in the bot.
- The bot must have the required permissions.
- Views are only registered when corresponding modules are enabled.

### No welcome messages?
- Make sure the channel ID is correctly configured.
- The bot needs write permissions in the target channel.

---

### Credits

Developed by **pierre.mateke**   
For support, contact `pierre.mateke` on Discord.
