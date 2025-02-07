from app import db
from datetime import datetime

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_message_id = db.Column(db.String(32), unique=True)
    channel_id = db.Column(db.String(32))
    author_id = db.Column(db.String(32))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ServerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(32))
    total_messages = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    date = db.Column(db.Date)

class WeeklyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(32))
    week_start = db.Column(db.Date)
    top_topics = db.Column(db.Text)  # JSON string
    active_members = db.Column(db.Text)  # JSON string
    summary = db.Column(db.Text)
