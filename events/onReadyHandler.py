import discord

async def on_ready_handler(bot: discord.Client):
    print(f'✅ Logged in as {bot.user}')
    print(f'✅ Bot ID: {bot.user.id}')
    print(f'✅ Connected to {len(bot.guilds)} guild(s)')
    print('✅ Bot is ready!')

