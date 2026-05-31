import discord
from discord.ext import commands
import yt_dlp
import asyncio

# Suppress yt-dlp warnings
yt_dlp.utils.bug_reports_message = lambda *args, **kwargs: ''

# yt-dlp options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    """Music commands for playing audio from YouTube"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Store queues per guild
    
    def get_queue(self, guild_id):
        """Get or create a queue for a guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]
    
    async def play_next(self, ctx):
        """Play the next song in the queue"""
        queue = self.get_queue(ctx.guild.id)
        if queue:
            url = queue.pop(0)
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(
                    player,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                    ) if e is None else None
                )
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{player.title}]({url})",
                    color=discord.Color.green()
                )
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                if player.duration:
                    minutes, seconds = divmod(player.duration, 60)
                    embed.add_field(name="Duration", value=f"{int(minutes)}:{int(seconds):02d}", inline=True)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ Error playing song: {e}")
                await self.play_next(ctx)  # Try next song
        else:
            # No more songs, disconnect after a delay
            await asyncio.sleep(300)  # Wait 5 minutes
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                await ctx.send("🔌 Disconnected from voice channel (inactive).")
    
    @commands.command(name="play", aliases=["p"])
    @commands.has_permissions(view_channel=True, send_messages=True, connect=True, speak=True)
    async def play(self, ctx, *, query: str):
        """Play a song from YouTube. Usage: !play <song name or URL>"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
        
        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is None:
            try:
                await voice_channel.connect()
            except Exception as e:
                await ctx.send(f"❌ Could not connect to voice channel: {e}")
                return
        elif ctx.voice_client.channel != voice_channel:
            await ctx.send("❌ I'm already in a different voice channel!")
            return
        
        # Check if it's a URL or search query
        if not query.startswith(('http://', 'https://')):
            # It's a search query, we'll let yt-dlp handle it
            query = f"ytsearch:{query}"
        
        try:
            # Show loading message
            loading_msg = await ctx.send("🔍 Searching for song...")
            
            # Extract info to get the title
            loop = self.bot.loop
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(query, download=False)
            )
            
            if 'entries' in data:
                data = data['entries'][0]
            
            title = data.get('title', 'Unknown')
            webpage_url = data.get('webpage_url') or data.get('url')
            
            if not webpage_url:
                await loading_msg.edit(content="❌ Could not find a valid URL for this song.")
                return
            
            queue = self.get_queue(ctx.guild.id)
            
            # If already playing, add to queue
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                queue.append(webpage_url)
                embed = discord.Embed(
                    title="➕ Added to Queue",
                    description=f"[{title}]({webpage_url})",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Position in Queue", value=len(queue), inline=True)
                await loading_msg.edit(content="", embed=embed)
            else:
                # Play immediately
                player = await YTDLSource.from_url(webpage_url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(
                    player,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                    ) if e is None else None
                )
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{player.title}]({webpage_url})",
                    color=discord.Color.green()
                )
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                if player.duration:
                    minutes, seconds = divmod(player.duration, 60)
                    embed.add_field(name="Duration", value=f"{int(minutes)}:{int(seconds):02d}", inline=True)
                await loading_msg.edit(content="", embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="stop", aliases=["disconnect", "leave"])
    @commands.has_permissions(view_channel=True, send_messages=True)
    async def stop(self, ctx):
        """Stop the music and disconnect from voice channel"""
        if ctx.voice_client:
            self.get_queue(ctx.guild.id).clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Stopped and disconnected from voice channel.")
        else:
            await ctx.send("❌ I'm not in a voice channel!")
    
    @commands.command(name="pause")
    @commands.has_permissions(view_channel=True, send_messages=True)
    async def pause(self, ctx):
        """Pause the currently playing song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("❌ Nothing is playing!")
    
    @commands.command(name="resume")
    @commands.has_permissions(view_channel=True, send_messages=True)
    async def resume(self, ctx):
        """Resume the paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("❌ Nothing is paused!")
    
    @commands.command(name="skip", aliases=["next"])
    @commands.has_permissions(view_channel=True, send_messages=True)
    async def skip(self, ctx):
        """Skip the currently playing song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped.")
        else:
            await ctx.send("❌ Nothing is playing!")
    
    @commands.command(name="queue", aliases=["q"])
    @commands.has_permissions(view_channel=True, send_messages=True)
    async def queue(self, ctx):
        """Show the current music queue"""
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("📭 Queue is empty.")
            return
        
        embed = discord.Embed(
            title="📋 Music Queue",
            description=f"{len(queue)} song(s) in queue",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @play.error
    @stop.error
    @pause.error
    @resume.error
    @skip.error
    @queue.error
    async def music_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            await ctx.send(f"❌ Missing required permissions: {', '.join(missing_perms)}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Please provide a song name or URL. Usage: `!play <song name or URL>`")

async def setup(bot):
    await bot.add_cog(Music(bot))
