import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from app import db, app
from models import Message, ServerStats
import os
from sqlalchemy import func
from analytics import get_top_topics, get_active_members
import discord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Create bot instance with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for tracking member activity
intents.guilds = True   # Required for server information
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    
    # Fetch historical messages
    with app.app_context():
        for guild in bot.guilds:
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=1000):
                        if message.author != bot.user:
                            new_message = Message(
                                discord_message_id=str(message.id),
                                channel_id=str(channel.id),
                                author_id=str(message.author.id),
                                content=message.content,
                                timestamp=message.created_at
                            )
                            try:
                                db.session.add(new_message)
                                db.session.commit()
                            except:
                                db.session.rollback()
                except Exception as e:
                    logger.error(f"Error fetching history for channel {channel}: {e}")
                    
    update_stats.start()

@bot.command(name='stats')
async def stats(ctx, days: int = 7):
    """Get server stats for the specified number of days"""
    async with ctx.typing():
        with app.app_context():
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            messages = db.session.query(Message).filter(
                Message.timestamp >= start_date
            ).all()
            
            total_messages = len(messages)
            unique_users = len(set(msg.author_id for msg in messages))
            top_topics = get_top_topics(messages)
            active_users = get_active_members(messages)

            embed = discord.Embed(title=f"Server Stats - Last {days} days", color=0x00ff00)
            embed.add_field(name="Total Messages", value=str(total_messages), inline=True)
            embed.add_field(name="Unique Users", value=str(unique_users), inline=True)
            
            top_topics_str = "\n".join(f"{topic}: {count}" for topic, count in top_topics[:5])
            embed.add_field(name="Top Topics", value=top_topics_str or "No topics yet", inline=False)
            
            active_users_str = "\n".join(f"<@{user_id}>: {count}" for user_id, count in active_users[:5])
            embed.add_field(name="Most Active Users", value=active_users_str or "No active users", inline=False)
            
            await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)
    
    # Only store non-command messages
    if not message.content.startswith(bot.command_prefix):
        with app.app_context():
            try:
                new_message = Message(
                    discord_message_id=str(message.id),
                    channel_id=str(message.channel.id),
                    author_id=str(message.author.id),
                    content=message.content,
                    timestamp=message.created_at,
                    reply_to_id=str(message.reference.message_id) if message.reference else None,
                    reply_to_author_id=str(message.reference.resolved.author.id) if message.reference and message.reference.resolved else None
                )
                db.session.add(new_message)
                db.session.commit()
                logger.info(f"Stored message {message.id} from {message.author}")
            except Exception as e:
                logger.debug(f"Message {message.id} already exists or error: {e}")
                db.session.rollback()

@tasks.loop(hours=24)
async def update_stats():
    """Update daily server statistics"""
    with app.app_context():
        for guild in bot.guilds:
            today = datetime.utcnow().date()

            # Count today's messages
            message_count = db.session.query(Message).filter(
                func.date(Message.timestamp) == today
            ).count()

            # Count active users
            active_users = db.session.query(Message.author_id).filter(
                func.date(Message.timestamp) == today
            ).distinct().count()

            stats = ServerStats(
                server_id=str(guild.id),
                total_messages=message_count,
                active_users=active_users,
                date=today
            )

            db.session.add(stats)
            try:
                db.session.commit()
                logger.info(f"Updated stats for server {guild.id}")
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
                db.session.rollback()

def start_bot():
    """Start the Discord bot with proper error handling"""
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("Discord bot token not found in environment variables")
        return

    try:
        logger.info("Starting Discord bot...")
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error("""
        Error: Privileged Intents are not enabled for this bot!
        Please follow these steps to enable them:
        1. Go to https://discord.com/developers/applications
        2. Select your bot application
        3. Go to the "Bot" section
        4. Enable the following Privileged Gateway Intents:
           - SERVER MEMBERS INTENT
           - MESSAGE CONTENT INTENT
        """)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")