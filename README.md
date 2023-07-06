# Discord Movie Bot

A Discord bot for checking trending movies and shows from Trakt, checking and managing your movie library on Radarr, and fetching movie trailer links from TMDB.

## Features
- Checks for new trending movies and shows at a certain time every day (default 18:00 or 6PM).
- Can manually run the check when the `!check_trending` command is used.
- Sends a message to a specific Discord channel with the title, TMDB ID, and a YouTube trailer link (if available) for each new trending movie that is not in your Radarr library.
- Adds a ➕ (plus) and ❌ (cross mark) emoji reaction to each message.
  - Clicking the ➕ emoji will add the movie to your Radarr library.
  - Clicking the ❌ emoji will ignore the movie in future checks.

## Setup

1. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/discord-movie-bot.git
    cd discord-movie-bot
    ```

2. Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set the following environment variables in a `config.env` file:

    - `bot_token`: Your Discord bot token.
    - `CHANNELID`: The ID of the Discord channel where the bot should send messages.
    - `TRAKT_API_URL`: The base URL of the Trakt API.
    - `TRAKT_CLIENT_ID`: Your Trakt API client ID.
    - `RADARR_API_URL`: The base URL of your Radarr server's API.
    - `RADARR_API_KEY`: Your Radarr API key.
    - `USER_TO_MENTION_ID`: The ID of the user to ping when new movies are found (optional).
    - `CHECK_TIME`: The time to check for trending movies in 24h format (optional, default is '18:00' or 6PM).
    - `MOVIE_DIRECTORY`: The directory where the movies will be stored (optional).
    - `TMDB_API_KEY`: Your TMDB API key.

    Example:

    ```env
    bot_token=YOUR_DISCORD_BOT_TOKEN
    CHANNELID=YOUR_DISCORD_CHANNEL_ID
    TRAKT_API_URL=https://api.trakt.tv
    TRAKT_CLIENT_ID=YOUR_TRAKT_CLIENT_ID
    RADARR_API_URL=http://localhost:7878/api
    RADARR_API_KEY=YOUR_RADARR_API_KEY
    USER_TO_MENTION_ID=YOUR_USER_ID
    CHECK_TIME=18:00
    MOVIE_DIRECTORY=/path/to/your/movie/directory
    TMDB_API_KEY=YOUR_TMDB_API_KEY
    ```

4. Run the bot:
    ```bash
    python bot.py
    ```

Enjoy your Discord Movie Bot!