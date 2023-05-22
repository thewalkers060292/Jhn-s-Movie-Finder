import os
import discord
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
import pytz
import asyncio

# Load environment variables from the .env file
load_dotenv('config.env')

# Gather our tokens, keys, and config settings from environment variables
TOKEN = os.getenv('bot_token')
CHANNEL_ID = int(os.getenv('CHANNELID'))
TRAKT_API_URL = os.getenv('TRAKT_API_URL')
TRAKT_CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
RADARR_API_URL = os.getenv('RADARR_API_URL')
RADARR_API_KEY = os.getenv('RADARR_API_KEY')
USER_TO_MENTION_ID = int(os.getenv('USER_TO_MENTION_ID'))  # User to ping when new movies are found
CHECK_TIME = os.getenv('CHECK_TIME', '18:00')  # Time to check for trending movies in 24h format. Default is 18:00 (6PM)
MOVIE_DIRECTORY = os.getenv('MOVIE_DIRECTORY', 'I:\\Movies 6')  # The directory where the movies will be stored

# Setup discord client with the required intents
intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
client = discord.Client(intents=intents)

async def get_radarr_movies():
    """
    Fetches all movies from the Radarr server.
    Radarr is a movie collection manager for Usenet and BitTorrent users.
    """
    url = f"{RADARR_API_URL}/movie"
    headers = {'X-Api-Key': RADARR_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            radarr_movies = await resp.json()
    return radarr_movies

async def get_trending():
    """
    Fetches all trending movies and shows from the Trakt server.
    Trakt is a platform that does many things, but primarily keeps track of TV shows and movies you watch.
    """
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': TRAKT_CLIENT_ID
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{TRAKT_API_URL}/movies/trending", headers=headers) as resp:
            trending_movies = await resp.json()
        async with session.get(f"{TRAKT_API_URL}/shows/trending", headers=headers) as resp:
            trending_shows = await resp.json()
    return trending_movies + trending_shows

async def add_to_radarr(id, title):
    """
    Adds a movie to the Radarr server.
    """
    url = f"{RADARR_API_URL}/movie"
    headers = {'X-Api-Key': RADARR_API_KEY}
    data = {
        'title': title,
        'tmdbId': int(id),
        'qualityProfileId': 1,
        'rootFolderPath': MOVIE_DIRECTORY,  # Customize this as per your setup
        'monitored': True,
        'addOptions': {
            'searchForMovie': True
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            return resp.status == 201

async def check_trending_and_notify():
    """
    Checks for trending movies and shows, sends a Discord message if new ones are found.
    """
    user_to_mention = await client.fetch_user(USER_TO_MENTION_ID)
    channel = client.get_channel(CHANNEL_ID)

    trending = await get_trending()
    radarr_movies = await get_radarr_movies()

    radarr_movie_ids = {movie['tmdbId'] for movie in radarr_movies}

    new_movies = []
    for item in trending:
        if 'movie' in item:
            trakt_id = item['movie']['ids']['tmdb']
            msg_content = f"New trending movie: {item['movie']['title']} (ID: {trakt_id})"
            if trakt_id not in radarr_movie_ids:
                new_movies.append(msg_content)
    
    if new_movies:
        for movie in new_movies:
            msg = await channel.send(movie)
            await msg.add_reaction('👍')
        await channel.send(f'{user_to_mention.mention} Here are the new trending movies!')
    else:
        await channel.send("You are all caught up!")

async def time_check():
    """
    Checks every minute if it's time to fetch trending movies and shows.
    """
    while True:
        now = datetime.now(pytz.timezone('US/Eastern'))
        check_hour, check_minute = map(int, CHECK_TIME.split(':'))
        if now.hour == check_hour and now.minute == check_minute:
            await check_trending_and_notify()
            await asyncio.sleep(86400)  # Sleep for 24 hours
        else:
            await asyncio.sleep(60)  # Sleep for 1 minute

@client.event
async def on_reaction_add(reaction, user):
    """
    Event listener for reaction additions. Adds the movie to Radarr if a 👍 reaction is detected.
    """
    if user == client.user or reaction.emoji != '👍' or reaction.message.author != client.user:
        return

    msg_content = reaction.message.content

    title_id_start = msg_content.find("(ID: ") + len("(ID: ")
    title_id_end = msg_content.find(")", title_id_start)
    id = msg_content[title_id_start:title_id_end]

    title_start = msg_content.find("New trending movie: ") + len("New trending movie: ")
    title_end = msg_content.find(" (ID: ", title_start)
    title = msg_content[title_start:title_end]
    
    added = await add_to_radarr(id, title)
    if added:
        await reaction.message.reply("Added to Radarr!")
    else:
        await reaction.message.reply("Failed to add to Radarr.")

@client.event
async def on_ready():
    """
    Event listener for when the bot is ready.
    """
    print(f"We have logged in as {client.user}")
    client.loop.create_task(time_check())

client.run(TOKEN)
