from config.config import BANNED_WORDS
import discord

async def censor_handler(message: discord.Message, bot: discord.Client):
    """Handle message censorship"""
    if message.author.bot:
        return
    
    content = message.content.lower()
    
    # Check for banned words
    if any(word in content for word in BANNED_WORDS):
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} ⚠️ Your message contained inappropriate language and was removed.",
                delete_after=5
            )
        except discord.Forbidden:
            # Bot doesn't have permission to delete messages
            print(f"Could not delete message from {message.author.name}")

