import discord
from utils.anti_bot import (
    check_raid_protection,
    check_spam_protection,
    handle_raid_detection,
    handle_spam_detection
)

async def anti_bot_join_handler(bot: discord.Client, member: discord.Member):
    """Handle member joins with anti-bot protection"""
    is_raid = await check_raid_protection(member)
    
    if is_raid:
        await handle_raid_detection(bot, member)
        return True  # Indicates suspicious activity
    
    return False

async def anti_bot_message_handler(message: discord.Message):
    """Handle messages with spam protection"""
    is_spam = await check_spam_protection(message)
    
    if is_spam:
        await handle_spam_detection(message)
        return True  # Indicates spam detected
    
    return False

