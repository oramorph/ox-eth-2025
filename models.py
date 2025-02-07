from app import db
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Date

# Message Model
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(Integer, primary_key=True)
    discord_message_id = db.Column(String(32), unique=True)
    channel_id = db.Column(String(32))
    author_id = db.Column(String(32))
    content = db.Column(Text, nullable=True)
    timestamp = db.Column(DateTime, default=datetime.utcnow)

    def __init__(self, discord_message_id, channel_id, author_id, content, timestamp):
        self.discord_message_id = discord_message_id
        self.channel_id = channel_id
        self.author_id = author_id
        self.content = content
        self.timestamp = timestamp


# Server Stats Model
class ServerStats(db.Model):
    __tablename__ = "server_stats"

    id = db.Column(Integer, primary_key=True)
    server_id = db.Column(String(32))
    total_messages = db.Column(Integer, default=0)
    active_users = db.Column(Integer, default=0)
    date = db.Column(Date)

    def __init__(self, server_id, total_messages=0, active_users=0, date=None):
        self.server_id = server_id
        self.total_messages = total_messages
        self.active_users = active_users
        self.date = date or datetime.utcnow().date()

# Weekly Report Model
class WeeklyReport(db.Model):
    __tablename__ = "weekly_reports"

    id = db.Column(Integer, primary_key=True)
    server_id = db.Column(String(32))
    week_start = db.Column(Date)
    top_topics = db.Column(Text)  # JSON string
    active_members = db.Column(Text)  # JSON string
    summary = db.Column(Text)
