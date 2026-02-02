import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration settings
BANNED_WORDS = ["shit", "damn", "badword"]  # Add your banned words here

WELCOME_CHANNEL_NAME = "general"  # Channel name for welcome messages

# Anti-bot protection settings
MAX_JOINS_PER_MINUTE = 5  # Max joins per minute before triggering anti-raid
MAX_MESSAGES_PER_SECOND = 5  # Max messages per second before spam detection
ACCOUNT_AGE_THRESHOLD_HOURS = 24  # Accounts newer than this are considered suspicious

