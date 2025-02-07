import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from app import db, app
from models import Message, ServerStats, WeeklyReport
import json
import os

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
    update_stats.start()

@bot.command(name='weekly')
async def weekly_summary(ctx):
    """Get server activity summary for the past week"""
    with app.app_context():
        week_ago = datetime.utcnow() - timedelta(days=7)
        messages = Message.query.filter(Message.timestamp >= week_ago).all()
        
        total_messages = len(messages)
        unique_users = len(set(msg.author_id for msg in messages))
        top_topics = get_top_topics(messages)
        active_members = get_active_members(messages)
        
        summary = f"**Weekly Summary**\n"
        summary += f"Total Messages: {total_messages}\n"
        summary += f"Active Users: {unique_users}\n\n"
        
        summary += "**Top Topics:**\n"
        for topic, count in top_topics:
            summary += f"• {topic}: {count} mentions\n"
        
        summary += "\n**Most Active Members:**\n"
        for member_id, count in active_members[:5]:
            summary += f"• <@{member_id}>: {count} messages\n"
            
        await ctx.send(summary)

@bot.command(name='monthly')
async def monthly_summary(ctx):
    """Get server activity summary for the past month"""
    with app.app_context():
        month_ago = datetime.utcnow() - timedelta(days=30)
        messages = Message.query.filter(Message.timestamp >= month_ago).all()
        
        total_messages = len(messages)
        unique_users = len(set(msg.author_id for msg in messages))
        top_topics = get_top_topics(messages)
        active_members = get_active_members(messages)
        
        summary = f"**Monthly Summary**\n"
        summary += f"Total Messages: {total_messages}\n"
        summary += f"Active Users: {unique_users}\n\n"
        
        summary += "**Top Topics:**\n"
        for topic, count in top_topics:
            summary += f"• {topic}: {count} mentions\n"
        
        summary += "\n**Most Active Members:**\n"
        for member_id, count in active_members[:5]:
            summary += f"• <@{member_id}>: {count} messages\n"
            
        await ctx.send(summary)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)
    
    # Store non-command messages in database
    if not message.content.startswith(bot.command_prefix):
        with app.app_context():
            try:
                existing_message = Message.query.filter_by(discord_message_id=str(message.id)).first()
                if not existing_message:
                    new_message = Message(
                        discord_message_id=str(message.id),
                        channel_id=str(message.channel.id),
                        author_id=str(message.author.id),
                        content=message.content,
                        timestamp=message.created_at
                    )
                    db.session.add(new_message)
                    db.session.commit()
                    logger.info(f"Stored message {message.id} from {message.author}")
            except Exception as e:
                logger.error(f"Error storing message: {e}")
                db.session.rollback()

@tasks.loop(hours=24)
async def update_stats():
    """Update daily server statistics"""
    with app.app_context():
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