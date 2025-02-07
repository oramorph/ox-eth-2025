from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Text, DateTime, Date, Column

class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    discord_message_id = Column(String(32), unique=True)
    channel_id = Column(String(32))
    author_id = Column(String(32))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ServerStats(Base):
    __tablename__ = 'server_stats'

    id = Column(Integer, primary_key=True)
    server_id = Column(String(32))
    total_messages = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    date = Column(Date)

class WeeklyReport(Base):
    __tablename__ = 'weekly_reports'

    id = Column(Integer, primary_key=True)
    server_id = Column(String(32))
    week_start = Column(Date)
    top_topics = Column(Text)  # JSON string
    active_members = Column(Text)  # JSON string
    summary = Column(Text)