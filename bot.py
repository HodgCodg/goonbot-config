import discord
from discord.ext import commands
import yt_dlp
import asyncio

# Configuration for yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

# Configuration for FFmpeg
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.queues = {} # {guild_id: [songs]}

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = MusicBot()

@bot.command(name='join')
async def join(ctx):
    """Joins the voice channel the user is currently in."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You need to be in a voice channel first!")

@bot.command(name='leave')
async def leave(ctx):
    """Leaves the voice channel."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        # Clear queue for this guild upon leaving
        if ctx.guild.id in bot.queues:
            bot.queues[ctx.guild.id] = []
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

async def play_next(ctx):
    """Internal helper to play the next song in the queue."""
    guild_id = ctx.guild.id
    if guild_id in bot.queues and bot.queues[guild_id]:
        next_song = bot.queues[guild_id].pop(0)
        
        # Use the same logic as the !play command for actual streaming
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(next_song, download=False)
                url = info['url']
                title = info.get('title', 'Unknown Title')
                
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                await ctx.send(f"Now playing: **{title}**")
            except Exception as e:
                await ctx.send(f"Error playing next song: {e}")
                await play_next(ctx)
    else:
        await ctx.send("Queue is empty.")

@bot.command(name='play')
async def play(ctx, *, search: str):
    """Plays music from a YouTube URL or search query."""
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("You must be in a voice channel!")

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info: # It was a search query
                    info = info['entries'][0]
                
                url = info['url']
                title = info.get('title', 'Unknown Title')
                
                if ctx.voice_client.is_playing():
                    guild_id = ctx.guild.id
                    if guild_id not in bot.queues:
                        bot.queues[guild_id] = []
                    bot.queues[guild_id].append(url)
                    await ctx.send(f"Added to queue: **{title}**")
                else:
                    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                    await ctx.send(f"Now playing: **{title}**")
                    
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")

@bot.command(name='skip')
async def skip(ctx):
    """Skips the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped!")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command(name='stop')
async def stop(ctx):
    """Stops playback and clears the queue."""
    if ctx.voice_client:
        ctx.voice_client.stop()
        guild_id = ctx.guild.id
        if guild_id in bot.queues:
            bot.queues[guild_id] = []
        await ctx.send("Stopped playback and cleared queue.")
    else:
        await ctx.send("I'm not playing anything.")

# Replace 'YOUR_BOT_TOKEN' with your actual token
# bot.run('YOUR_BOT_TOKEN')
# For deployment, it's recommended to use environment variables
import os
token = os.getenv('DISCORD_BOT_TOKEN')
if token:
    bot.run(token)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable not set.")
