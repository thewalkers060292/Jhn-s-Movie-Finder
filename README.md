# Jhns-Movie-Finder

This Discord bot is designed to fetch trending movies and shows from the Trakt server and send notifications to a Discord channel. Users can react to these notifications with a 👍 emoji, signaling the bot to add the movie to a Radarr server for downloading and management.

## Setup

1. Clone this repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt`.
3. Set up your environment variables in a `config.env` file. You need to provide the following:

```
bot_token=YOUR_DISCORD_BOT_TOKEN
CHANNELID=YOUR_DISCORD_CHANNEL_ID
TRAKT_API_URL=https://api.trakt.tv/
TRAKT_CLIENT_ID=YOUR_TRAKT_CLIENT_ID
RADARR_API_URL=YOUR_RADARR_API_URL
RADARR_API_KEY=YOUR_RADARR_API_KEY
USER_TO_MENTION_ID=DISCORD_USER_ID_TO_MENTION
CHECK_TIME=TIME_TO_CHECK_FOR_TRENDING_MOVIES
MOVIE_DIRECTORY=YOUR_MOVIE_DIRECTORY
```

4. Run the bot with `python bot.py`.

The bot will fetch trending movies and shows from the Trakt server each day at the time specified in `CHECK_TIME`, and send a message to the specified Discord channel for each trending movie that is not already in the Radarr server. If a user reacts to one of these messages with a 👍 emoji, the bot will add that movie to the Radarr server.

