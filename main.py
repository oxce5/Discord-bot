import discord
from discord.ext import commands
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from config.config import DISCORD_TOKEN
from events.onReadyHandler import on_ready_handler
from events.on_members_join import welcome_handler
from events.on_message_censor import censor_handler
from events.anti_bot_handler import anti_bot_join_handler, anti_bot_message_handler

load_dotenv()

# Setup logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Configure intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.reactions = True
intents.voice_states = True

class TestBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

        self.ai_api_url = "https://python-api-tfs6.onrender.com/gpt4o1"

    async def _send_discord_text(self, channel: discord.abc.Messageable, text: str):
        if not text:
            return

        # Discord messages have a 2000 character limit.
        for i in range(0, len(text), 2000):
            await channel.send(text[i:i + 2000])

    async def _handle_ai_message(self, message: discord.Message) -> bool:
        content = (message.content or "").strip()
        if not content:
            return False

        lowered = content.lower()
        if not (lowered == "ai" or lowered.startswith("ai ")):
            return False

        prompt = content[2:].lstrip()
        if not prompt:
            await message.channel.send("Usage: ai <prompt>")
            return True

        uid = str(message.author.id)
        timeout = aiohttp.ClientTimeout(total=45)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.ai_api_url, params={"prompt": prompt, "uid": uid}) as resp:
                    if resp.status != 200:
                        await message.channel.send(f"AI API error (HTTP {resp.status}).")
                        return True

                    data = await resp.json(content_type=None)

            reply = ""
            if isinstance(data, dict):
                reply = str(data.get("reply") or "")

            if not reply:
                await message.channel.send("AI API returned no reply.")
                return True

            await self._send_discord_text(message.channel, reply)
            return True
        except asyncio.TimeoutError:
            await message.channel.send("AI API timed out.")
            return True
        except aiohttp.ClientError:
            await message.channel.send("AI API request failed.")
            return True

    async def setup_hook(self):
        # Load command extensions
        await self.load_extension("commands.help_command")
        await self.load_extension("commands.role_management")
        await self.load_extension("commands.webhook_management")
        await self.load_extension("commands.music")
        print("✅ Bot setup complete.")
        print("✅ Loaded command extensions: help_command, role_management, webhook_management, music")

    async def on_ready(self):
        await on_ready_handler(self)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        
        # Anti-bot spam protection
        spam_detected = await anti_bot_message_handler(message)
        if spam_detected:
            return  # Don't process commands if spam was detected
        
        # Message censorship
        was_deleted = await censor_handler(message=message, bot=self)
        if was_deleted:
            return

        # Prefixless AI command: "ai <prompt>"
        ai_handled = await self._handle_ai_message(message)
        if ai_handled:
            return

        await self.process_commands(message)

    async def on_member_join(self, member: discord.Member):
        # Anti-bot raid protection
        raid_detected = await anti_bot_join_handler(self, member)
        if not raid_detected:
            # Only send welcome if not a raid
            await welcome_handler(member)

bot = TestBot()

# Basic commands
@bot.command()
@commands.has_permissions(view_channel=True, send_messages=True)
async def hello(ctx):
    """Say hello to the bot"""
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
@commands.has_permissions(
    view_channel=True,
    send_messages=True,
    embed_links=True,
    add_reactions=True,
    use_external_emojis=True
)
async def poll(ctx, *, question):
    """Create a poll with thumbs up/down reactions"""
    embed = discord.Embed(title="New Poll", description=question, color=discord.Color.blue())
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

@bot.command()
@commands.has_permissions(view_channel=True, send_messages=True)
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency}ms")

@bot.command()
@commands.has_permissions(view_channel=True, send_messages=True, embed_links=True)
async def info(ctx):
    """Get bot information"""
    embed = discord.Embed(
        title="Bot Information",
        description="A test Discord bot",
        color=discord.Color.green()
    )
    embed.add_field(name="Server", value=ctx.guild.name, inline=True)
    embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
    embed.add_field(name="Bot User", value=bot.user.name, inline=True)
    await ctx.send(embed=embed)

@hello.error
@poll.error
@ping.error
@info.error
async def basic_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
        await ctx.send(f"Missing required permissions: {', '.join(missing_perms)}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(" Please provide all required arguments. Use `!help` for command usage.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.INFO)

