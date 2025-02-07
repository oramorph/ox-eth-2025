import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from app import db
from models import Message, ServerStats, WeeklyReport
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    update_stats.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Store message in database
    new_message = Message(
        discord_message_id=str(message.id),
        channel_id=str(message.channel.id),
        author_id=str(message.author.id),
        content=message.content,
        timestamp=message.created_at
    )
    
    db.session.add(new_message)
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Error storing message: {e}")
        db.session.rollback()

    await bot.process_commands(message)

@tasks.loop(hours=24)
async def update_stats():
    """Update daily server statistics"""
    for guild in bot.guilds:
        # Count today's messages
        today = datetime.utcnow().date()
        message_count = Message.query.filter(
            Message.timestamp >= today
        ).count()

        # Count active users
        active_users = (
            Message.query.filter(Message.timestamp >= today)
            .with_entities(Message.author_id)
            .distinct()
            .count()
        )

        stats = ServerStats(
            server_id=str(guild.id),
            total_messages=message_count,
            active_users=active_users,
            date=today
        )
        
        db.session.add(stats)
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
            db.session.rollback()

def start_bot():
    # Get token from environment variable
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("Discord bot token not found in environment variables")
        return
    bot.run(token)