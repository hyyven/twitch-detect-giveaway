# About

This is a twitch bot designed to monitor the chats of multiple twitch channels in real time and detect when there's a giveaway. When viewers start spamming a specific command like `!giveaway`, `!claim`, ... the bot detects the anomaly in the message history and sends a notification to a specified discord server via a webhook. 

The bot periodically checks the live status of the target channels and dynamically joins or leaves their chats, ensuring it only monitors channels that are streaming.

# Setup

To run this project, you need to rename `.env_exemple` in `.env` and fill in the values. Here is a breakdown of each constant:

### Twitch api credentials
To get your app id and secret, you must register a developer application on twitch. You can follow the [official twitch tuto](https://dev.twitch.tv/docs/authentication/register-app) to create one.
- `TWITCH_APP_ID`: The client id of your twitch developer application required to authenticate and use the twitch api.
- `TWITCH_APP_SECRET`: The client secret of your twitch developer application.

### File paths & text files format
- `TARGET_CHANNEL_FILE`: Path to the file containing the list of twitch channels to monitor.
  - Format: One channel name per line. Empty lines are ignored. Do not include URLs or the `@` symbol, only the exact channel login name.
  - Example:
    ```
    shroud
    ninja
    ```
- `BAN_WORDS_FILE`: Path to the text file containing commands to ignore.
  - Format: One command per line. You can specify global banned words or channel-specific ones.
  - Global word ban: If a command (like `!lurk`) is spammed in every channels, simply add `!lurk` on a new line.
  - Channel specific Ban: If a specific channel have a command (like `!socials`) that viewers spam randomly, you can ignore it locally without affecting other channels by adding `!socials:channel_name` (e.g., `!socials:ninja`).

### Discord Integration
- `DISCORD_PING`: The discord role id/user id that should be pinged when a giveaway is detected.
- `WEBHOOK_URL`: The url of the discord webhook where notifications will be sent.

### Detection Tuning & Limits
- `NBR_OF_OCCURENCE`: The number of occurence of identical commands starting with `!` needed to trigger a giveaway notification. (default: 6)
- `NOTIF_COOLDOWN`: The cooldown period in seconds before the bot can send another notification for the same channel. Prevents spamming the discord server. (default: 300)
- `MAX_MESSAGES_HISTORY`: The number of recent messages kept in memory for each channel. (default: 20)
- `MAX_HELIX_PAGE`: The maximum number of channels to fetch in a single twitch API request when checking for live status. Do not exceed 100 as per twitch API limits. (default: 100)

# Tuning

A single set of detection variables can not fit all streams. Depending on the size of the channels you monitor, you might need to adjust the `.env` settings to avoid false positives or missed giveaways.

* For Massive Channels (>10k viewers):
    In huge chats, a giveaway command is spammed hundreds of times per second, but regular messages are also very frequent.
    * Suggestion: Increase `MAX_MESSAGES_HISTORY` to `50` or `100` and increase `NBR_OF_OCCURENCE` to `15` or `20`. This ensures normal chat behavior doesn't push the giveaway commands out of the history before triggering the alert.

* For Small Channels (<500 viewers):
    In slower chats, it might take a while for 6 people to type the giveaway command.
    * Suggestion: Keep `MAX_MESSAGES_HISTORY` at `20`, but lower `NBR_OF_OCCURENCE` to `3` or `4` to catch smaller giveaways.

  