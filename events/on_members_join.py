import discord
from config.config import WELCOME_CHANNEL_NAME

async def welcome_handler(member: discord.Member):
    """Handle new member joins"""
    # Try to find the welcome channel by name
    channel = discord.utils.get(member.guild.channels, name=WELCOME_CHANNEL_NAME)
    
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}! 🎉")
    else:
        # Fallback: send DM if channel not found
        try:
            await member.send(f"Welcome to {member.guild.name}! 🎉")
        except discord.Forbidden:
            # Can't send DM, just log it
            print(f"Could not send welcome message to {member.name}")

