import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timedelta
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "discord_analytics_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///discord_analytics.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Import models after db initialization to avoid circular imports
from models import Message, ServerStats, WeeklyReport

@app.route('/')
def dashboard():
    # Get the last 7 days of data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    try:
        # Get daily message counts
        daily_messages = db.session.query(
            func.date(Message.timestamp).label('date'),
            func.count(Message.id).label('count')
        ).filter(
            Message.timestamp >= start_date
        ).group_by(
            func.date(Message.timestamp)
        ).order_by(
            func.date(Message.timestamp)
        ).all()

        # Get daily active users
        daily_users = db.session.query(
            func.date(Message.timestamp).label('date'),
            func.count(func.distinct(Message.author_id)).label('count')
        ).filter(
            Message.timestamp >= start_date
        ).group_by(
            func.date(Message.timestamp)
        ).order_by(
            func.date(Message.timestamp)
        ).all()

        # Format data for charts
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(8)]
        message_data = {date: 0 for date in dates}
        user_data = {date: 0 for date in dates}

        for date, count in daily_messages:
            message_data[date.strftime('%Y-%m-%d')] = count

        for date, count in daily_users:
            user_data[date.strftime('%Y-%m-%d')] = count

        return render_template('dashboard.html',
                             dates=list(message_data.keys()),
                             message_counts=list(message_data.values()),
                             user_counts=list(user_data.values()))
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return render_template('dashboard.html',
                             dates=[],
                             message_counts=[],
                             user_counts=[])

@app.route('/reports')
def reports():
    return render_template('reports.html')

def init_db():
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Initialize database tables
init_db()