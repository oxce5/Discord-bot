import discord
from datetime import datetime, timedelta
from collections import defaultdict

# Track member joins per guild
member_joins = defaultdict(list)
# Track message spam per user
message_spam = defaultdict(list)
# Track suspicious accounts
suspicious_accounts = defaultdict(set)

# Import config values (with defaults if not available)
try:
    from config.config import MAX_JOINS_PER_MINUTE, MAX_MESSAGES_PER_SECOND, ACCOUNT_AGE_THRESHOLD_HOURS
except ImportError:
    # Default values if config not available
    MAX_JOINS_PER_MINUTE = 5
    MAX_MESSAGES_PER_SECOND = 5
    ACCOUNT_AGE_THRESHOLD_HOURS = 24

async def check_raid_protection(member: discord.Member) -> bool:
    """Check if a member join might be part of a raid"""
    guild_id = member.guild.id
    now = datetime.now()
    
    # Add this join to the list
    member_joins[guild_id].append(now)
    
    # Remove joins older than 1 minute
    member_joins[guild_id] = [
        join_time for join_time in member_joins[guild_id]
        if now - join_time < timedelta(minutes=1)
    ]
    
    # Check if too many joins in the last minute
    if len(member_joins[guild_id]) > MAX_JOINS_PER_MINUTE:
        return True
    
    # Check account age
    account_age = now - member.created_at
    if account_age < timedelta(hours=ACCOUNT_AGE_THRESHOLD_HOURS):
        suspicious_accounts[guild_id].add(member.id)
        return True
    
    return False

async def check_spam_protection(message: discord.Message) -> bool:
    """Check if a message is spam"""
    if message.author.bot:
        return False
    
    user_id = message.author.id
    now = datetime.now()
    
    # Add this message to the list
    message_spam[user_id].append(now)
    
    # Remove messages older than 1 second
    message_spam[user_id] = [
        msg_time for msg_time in message_spam[user_id]
        if now - msg_time < timedelta(seconds=1)
    ]
    
    # Check if too many messages in the last second
    if len(message_spam[user_id]) > MAX_MESSAGES_PER_SECOND:
        return True
    
    return False

async def handle_raid_detection(bot: discord.Client, member: discord.Member):
    """Handle detected raid attempt"""
    try:
        # Log the raid attempt
        print(f"⚠️ RAID DETECTED: {member.name} ({member.id}) joined {member.guild.name}")
        
        # Try to kick the member
        try:
            await member.kick(reason="Anti-raid protection: Suspicious account")
            print(f"✅ Kicked {member.name} due to raid protection")
        except discord.Forbidden:
            print(f"❌ No permission to kick {member.name}")
        
        # Notify admins
        for channel in member.guild.text_channels:
            if channel.permissions_for(member.guild.me).send_messages:
                embed = discord.Embed(
                    title="⚠️ Raid Protection Alert",
                    description=f"Detected suspicious account: {member.mention}\nAccount age: {(datetime.now() - member.created_at).days} days",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                break
    except Exception as e:
        print(f"❌ Error handling raid detection: {e}")

async def handle_spam_detection(message: discord.Message):
    """Handle detected spam"""
    try:
        # Delete spam messages
        await message.delete()
        
        # Warn the user
        warning = await message.channel.send(
            f"{message.author.mention} ⚠️ Please slow down! Spam detected.",
            delete_after=5
        )
        
        # If spam continues, consider timeout
        user_id = message.author.id
        spam_count = len(message_spam[user_id])
        
        if spam_count > MAX_MESSAGES_PER_SECOND * 3:
            # Apply timeout (mute) for 10 minutes
            try:
                timeout_until = datetime.now() + timedelta(minutes=10)
                await message.author.timeout(timeout_until, reason="Spam detection")
                await message.channel.send(
                    f"{message.author.mention} has been timed out for 10 minutes due to spam.",
                    delete_after=10
                )
            except discord.Forbidden:
                print(f"❌ No permission to timeout {message.author.name}")
    except Exception as e:
        print(f"❌ Error handling spam detection: {e}")

def clear_old_data():
    """Clear old tracking data periodically"""
    now = datetime.now()
    
    # Clear old member join data
    for guild_id in list(member_joins.keys()):
        member_joins[guild_id] = [
            join_time for join_time in member_joins[guild_id]
            if now - join_time < timedelta(minutes=5)
        ]
        if not member_joins[guild_id]:
            del member_joins[guild_id]
    
    # Clear old message spam data
    for user_id in list(message_spam.keys()):
        message_spam[user_id] = [
            msg_time for msg_time in message_spam[user_id]
            if now - msg_time < timedelta(seconds=10)
        ]
        if not message_spam[user_id]:
            del message_spam[user_id]

