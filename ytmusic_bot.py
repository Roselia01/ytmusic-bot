import discord
from discord import Intents, Client, app_commands
import yt_dlp as youtube_dl
import asyncio
from collections import deque
import random

# - User Settings
GUILD_ID = 'Guild ID Here'
NOW_PLAYING_CHANNEL = 'Discord Channel ID Here'
TOKEN = 'Discord Bot Token Here'

# -  Installation  -
 
# 1. Install dependencies!
#    To install dependencies, open a terminal in python and type:
#    pip install discord
#    pip install yt_dlp
#    pip install python-dotenv
#    pip install PyNaCl

#    (If 'pip install' isn't working, try 'py -m pip install package_name' instead!)

#    Some dependencies like FFMPEG require a seperate method to install.
#    https://youtu.be/JR36oH35Fgg - This video can explain intalling FFMPEG better than I ever could.

# 2. Create Your Bot!
#    Go to https://discord.com/developers/applications and select "New Application".
#    Name it whatever you like, agree to Discord's Developer TOS and click "Create"
#    Select your new application, and then on the left select "Bot" and click "Reset Token"
#    Scroll down and enable "Message Content Intent", Copy down your Token and paste it above in "TOKEN"

# 3. Finalizing The Bot!
#    Next go to "OAuth2" on the developers page, and select "bot" on the URL Generator.
#    For simplicity, just select "Administrator", but this bot only really needs these few permissions;
#    Connect, Speak, Use Voice Activity, Send Messages, and View Channels.

#    Finally, copy the Generated URL and open it. In Discord select the server you want to add your new bot to!
#    To finish up, right click the channel you want to set as the "Now Playing" Channel and copy it's ID.
#    Do the same with the Discord server your bot is in, and paste both of those into their settings above.

#    To start the bot, run this file, enter a Voice Channel and type /play followed by a Youtube Link!



# WARNING!
# Do not go beyond this point unless you know what you're doing!
# You will not need to adjust any values beyond here.

#----------------------------------------------------------------

# Define Variables
intents: Intents = Intents.default()
intents.message_content = True
intents.voice_states = True
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)
current_song = None

# Set up YTDL options
ytdl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': 'in_playlist',
    'socket_timeout': 30
}

ytdl = youtube_dl.YoutubeDL(ytdl_opts)

song_queue = deque()

def format_duration(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    return f'{minutes}:{seconds:02}'

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data):
        super().__init__(source)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        """Download and stream a song from a URL."""
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        filename = data['url']
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    
async def play_next_song(voice_client):
    global current_song
    global formatted_duration

    if song_queue:
        current_song = song_queue.popleft()

        guild = voice_client.guild
        target_channel = guild.get_channel(NOW_PLAYING_CHANNEL)

        if target_channel:
            try:
                # Include the song's duration in the message
                formatted_duration = format_duration(current_song['duration'])
                await target_channel.send(f'# Now Playing :notes:\n:arrow_forward: **{current_song["title"]}** (`{formatted_duration}`)')
            except discord.Forbidden:
                print("Bot lacks permission to send messages in the specified channel.")
            except Exception as e:
                print(f"Error sending message to the specified channel: {e}")
        else:
            print("Specified channel not found.")

        player = await YTDLSource.from_url(current_song['url'])
        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), client.loop))
    else:
        current_song = None
        await voice_client.disconnect()


### COMMANDS

# /play <url>
@tree.command(
    name='play',
    description='Plays a song or playlist from YouTube.',
    guild=discord.Object(id=GUILD_ID)
)
async def play(interaction: discord.Interaction, url: str):
    global current_song

    await interaction.response.defer()

    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel

        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)

        if not voice_client:
            voice_client = await channel.connect()

        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            for entry in data['entries']:
                song_queue.append({'title': entry['title'], 'url': entry['url'], 'duration': entry['duration']})
            first_song = song_queue[0]
        else:
            first_song = {'title': data['title'], 'url': data['url'], 'duration': data['duration']}
            song_queue.append(first_song)

        if voice_client.is_playing():
            formatted_duration = format_duration(first_song['duration'])
            await interaction.followup.send(f'# Added to Queue :notes:\n:arrow_forward: **{first_song["title"]}** (`{formatted_duration}`)')
        else:
            current_song = song_queue.popleft()
            player = await YTDLSource.from_url(current_song['url'])
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), client.loop))

            formatted_duration = format_duration(current_song['duration'])
            await interaction.followup.send(f'# Now Playing :notes:\n:arrow_forward: **{current_song["title"]}** (`{formatted_duration}`)')

    else:
        await interaction.followup.send('# :x: You are not in a voice channel.')

# /stop
@tree.command(
    name='stop',
    description='Stops the music and clears the queue.',
    guild=discord.Object(id=GUILD_ID)
)
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()

    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client:
        song_queue.clear()
        voice_client.stop()
        await voice_client.disconnect()
        await interaction.followup.send('# :stop_button: Stopped the music and cleared the queue.')
    else:
        await interaction.followup.send('# :x: I am not connected to a voice channel!')

# /skip
@tree.command(
    name='skip',
    description='Skips the currently playing song.',
    guild=discord.Object(id=GUILD_ID)
)
async def skip(interaction: discord.Interaction):
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message('# :fast_forward: Skipped the current song!')
    else:
        await interaction.response.send_message('# :x: No song is currently playing!')

# /queue
@tree.command(
    name='queue',
    description='Displays the current song queue.',
    guild=discord.Object(id=GUILD_ID)
)
async def queue(interaction: discord.Interaction):
    global current_song

    max_items_to_display = 10

    if current_song:
        current_song_duration = format_duration(current_song['duration'])
        queue_output = f'# Current Song :notes:\n:arrow_forward: **{current_song["title"]}** (`{current_song_duration}`)\n__                                                         __\n# Queue :eject:\n'
    else:
        queue_output = '# Current Song :notes:\n:x: **Nothing is playing!**\n__                                                         __\n# Queue :eject:\n'

    if song_queue:
        queue_output += '\n'.join([
            f'{idx + 1}. {song["title"]} (`{format_duration(song["duration"])}`)'
            for idx, song in enumerate(song_queue)
        ][:max_items_to_display])
        queue_length = len(song_queue)

        if queue_length > max_items_to_display:
            queue_output += f'\n*...and **{queue_length - max_items_to_display}** more song(s) in the queue.*'
    else:
        queue_output += 'The queue is currently empty.'

    await interaction.response.send_message(queue_output)

# /shuffle
@tree.command(
    name='shuffle',
    description='Shuffles the current song queue.',
    guild=discord.Object(id=GUILD_ID)
)
async def shuffle(interaction: discord.Interaction):
    if len(song_queue) > 1:
        shuffled_list = list(song_queue)
        random.shuffle(shuffled_list)
        song_queue.clear()
        song_queue.extend(shuffled_list)

        await interaction.response.send_message('# :twisted_rightwards_arrows: The queue has been shuffled!')
    else:
        await interaction.response.send_message('# :x: There are not enough songs in the queue to shuffle!')

# /clear
@tree.command(
    name='clear',
    description='Clears the current Queue.',
    guild=discord.Object(id=GUILD_ID)
)
async def clear(interaction: discord.Interaction):
    song_queue.clear()
    await interaction.response.send_message('# :white_check_mark: The queue has been cleared!')

### END OF COMMANDS


# Startup
@client.event
async def on_ready() -> None:
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_voice_state_update(member, before, after):
    for voice_client in client.voice_clients:
        if voice_client.guild == member.guild:
            if len(voice_client.channel.members) == 1:
                song_queue.clear()
                voice_client.stop()
                await voice_client.disconnect()
            return

def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()
