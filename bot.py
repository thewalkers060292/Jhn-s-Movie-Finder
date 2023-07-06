import os
import sys
import traceback
import json
import discord
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
from discord.ext import commands
import pytz
import asyncio

# Load environment variables from the .env file
load_dotenv('config.env')

IGNORE_LIST = 'ignore_list.txt'

# Setup discord client with the required intents
intents = discord.Intents.all()

# Create a Bot instance instead of a Client
client = commands.Bot(command_prefix='!', intents=intents)

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
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

@client.command(name='check_trending')
async def check_trending(ctx):
    """
    A command to manually run the check_trending_and_notify function.
    """
    print("Manual check for trending movies and shows initiated...")
    await ctx.send("🔍 Manually scanning for trending movies and shows...")
    await check_trending_and_notify()

async def get_movie_trailer(id):
    print(f"[{datetime.datetime.now()}] Fetching trailer for movie with ID: {id}...")
    """
    Fetches movie trailer details from the TMDB API for a given movie ID.
    """
    url = f"https://api.themoviedb.org/3/movie/{id}/videos"
    params = {'api_key': TMDB_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()

    # Extract the Youtube trailer URL if it exists
    for result in data.get('results', []):
        if result['site'] == 'YouTube':
            return f"https://www.youtube.com/watch?v={result['key']}"

    return None  # Return None if no Youtube trailer was found

async def get_radarr_movies():
    print("Fetching all movies from Radarr...")
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
    print("Fetching all trending movies and shows from Trakt...")
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
        async with session.get(f"{TRAKT_API_URL}/movies/trending?limit=20", headers=headers) as resp:
            trending_movies = await resp.json()
        async with session.get(f"{TRAKT_API_URL}/shows/trending?limit=20", headers=headers) as resp:
            trending_shows = await resp.json()
    return trending_movies + trending_shows

async def add_to_radarr(id, title):
    print(f"Attempting to add movie (ID: {id}, Title: {title}) to Radarr...")
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
    print("Executing check_trending_and_notify() function...")
    """
    Checks for trending movies and shows, sends a Discord message with all the current trending movies and an option to add them to Radarr.
    """

    # Load the ignore list
    if os.path.exists(IGNORE_LIST):
        with open(IGNORE_LIST, 'r') as f:
            ignore_list = {int(line.strip()) for line in f}
    else:
        ignore_list = set()

    channel = client.get_channel(CHANNEL_ID)

    await channel.send("🔍 Scanning the horizon for trending movies and shows...")
    trending = await get_trending()

    await channel.send("🎬 Accessing Radarr's library...")
    radarr_movies = await get_radarr_movies()

    await channel.send("📝 Preparing the checklist of movies already in Radarr...")
    radarr_movie_ids = {movie['tmdbId'] for movie in radarr_movies}

    await channel.send("🎥 Assembling a list of cinematic gems that are trending right now...")
    trending_movies = []
    for item in trending:
        if 'movie' in item:
            trakt_id = item['movie']['ids']['tmdb']
            title = item['movie']['title']
            trending_movies.append((trakt_id, title))

    await channel.send(f"📊 Found {len(trending_movies)} movies that are causing a buzz!")
    if trending_movies:
        trending_list = "\n".join(f"**{title}** (ID: {trakt_id})" for trakt_id, title in trending_movies)
        await channel.send("📬 Delivering the list of trending movies to you...")
        await channel.send(f"🍿 Grab your popcorn! Here are the movies creating waves:\n{trending_list}")
    else:
        await channel.send("😔 It seems quiet on the movie front. No trending movies found.")

    new_movies = []
    for trakt_id, title in trending_movies:
        if trakt_id not in radarr_movie_ids and trakt_id not in ignore_list:
            new_movies.append((trakt_id, title))

    if new_movies:
        await channel.send(f"⚠️ Found {len(new_movies)} movies that are not in your Radarr library!")
        for trakt_id, title in new_movies:
            # Fetch the movie trailer details
            url = f"https://api.themoviedb.org/3/movie/{trakt_id}/videos"
            params = {'api_key': TMDB_API_KEY}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

            # Extract the Youtube trailer URL if it exists
            trailer_url = None
            for result in data.get('results', []):
                if result['site'] == 'YouTube':
                    trailer_url = f"https://www.youtube.com/watch?v={result['key']}"

            if trailer_url:  # If a trailer exists
                msg_content = f"New trending movie: {title} (ID: {trakt_id})\nTrailer: {trailer_url}"
            else:
                msg_content = f"New trending movie: {title} (ID: {trakt_id})"
            
            msg = await channel.send(msg_content)
            await msg.add_reaction('➕')  # Replaced with 'plus' emoji
            await msg.add_reaction('❌')  # Replaced with 'cross mark' emoji
    else:
        await channel.send("👏 You're up-to-date with the trends! No new movies found.")

async def time_check():
    print("Time check initiated...")
    """
    Checks every minute if it's time to fetch trending movies and shows.
    """
    last_checked_date = None
    while True:
        now = datetime.now(pytz.timezone('US/Eastern'))
        check_hour, check_minute = map(int, CHECK_TIME.split(':'))
        if now.hour == check_hour and now.minute == check_minute:
            if last_checked_date != now.date():
                await check_trending_and_notify()
                last_checked_date = now.date()
        await asyncio.sleep(60)  # Sleep for 1 minute

@client.event
async def on_reaction_add(reaction, user):
    print(f"Reaction added: {reaction.emoji}, User: {user}")
    """
    Event listener for reaction additions. Adds the movie to Radarr if a ➕ reaction is detected, and ignores the movie if a ❌ reaction is detected.
    """
    if user == client.user or reaction.message.author != client.user:
        return

    msg_content = reaction.message.content

    title_id_start = msg_content.find("(ID: ") + len("(ID: ")
    title_id_end = msg_content.find(")", title_id_start)
    id = msg_content[title_id_start:title_id_end]

    title_end = msg_content.find(" (ID: ")
    title = msg_content[len("New trending movie: "):title_end]
    
    if reaction.emoji == '➕':  # If reaction is 'plus' emoji
        added = await add_to_radarr(id, title)
        if added:
            await reaction.message.reply("Added to Radarr!")
        else:
            await reaction.message.reply("Failed to add to Radarr.")
    elif reaction.emoji == '❌':  # If reaction is 'cross mark' emoji
        with open(IGNORE_LIST, 'a') as f:
            f.write(f"{id}\n")
        await reaction.message.reply(f"Ignored {title}!")

@client.event
async def on_ready():
    """
    Event listener for when the bot is ready.
    """
    print(f"We have logged in as {client.user}")
    client.loop.create_task(time_check())

client.run(TOKEN)
