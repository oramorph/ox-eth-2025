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
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY") or "discord_analytics_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///discord_analytics.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Import models after db initialization
from models import Message, ServerStats, WeeklyReport
from analytics import get_top_topics_bigram, get_influential_members, get_active_members


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/dashboard-data')
def dashboard_data():
    try:
        # Get the last 7 days of data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Get daily message counts
        daily_messages = db.session.query(
            func.date(Message.timestamp).label('date'),
            func.count(Message.id).label('count')).filter(
                Message.timestamp >= start_date).group_by(
                    func.date(Message.timestamp)).order_by(
                        func.date(Message.timestamp)).all()

        # Get daily active users
        daily_users = db.session.query(
            func.date(Message.timestamp).label('date'),
            func.count(func.distinct(
                Message.author_id)).label('count')).filter(
                    Message.timestamp >= start_date).group_by(
                        func.date(Message.timestamp)).order_by(
                            func.date(Message.timestamp)).all()

        # Format data for charts
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d')
                 for x in range(8)]
        message_data = {date: 0 for date in dates}
        user_data = {date: 0 for date in dates}

        for date, count in daily_messages:
            message_data[date.strftime('%Y-%m-%d')] = count

        for date, count in daily_users:
            user_data[date.strftime('%Y-%m-%d')] = count

        return jsonify({
            'dates': list(message_data.keys()),
            'message_counts': list(message_data.values()),
            'user_counts': list(user_data.values())
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({
            'dates': [],
            'message_counts': [],
            'user_counts': []
        }), 500


@app.route('/reports')
def reports():
    return render_template('reports.html')


@app.route('/api/reports-data')
def reports_data():
    try:
        # Get messages from the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        messages = Message.query.filter(Message.timestamp >= week_ago).all()

        # Get analytics data
        top_topics = get_top_topics_bigram(messages)
        active_members = get_active_members(messages)

        return jsonify({
            'top_topics': {
                topic: count
                for topic, count in top_topics
            },
            'active_members': {
                member: count
                for member, count in active_members
            }
        })
    except Exception as e:
        logger.error(f"Error fetching reports data: {e}")
        return jsonify({'top_topics': {}, 'active_members': {}}), 500


def init_db():
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# Database initialization will be done from main.py
