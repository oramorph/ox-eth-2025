from collections import Counter
from models import Message, ServerStats
from datetime import datetime, timedelta
import json


def get_top_topics(messages, top_n=5):
    """Extract top topics from messages using simple word frequency"""
    words = ' '.join([msg.content for msg in messages]).lower().split()
    # Filter common words
    stop_words = set(
        ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have'])
    words = [w for w in words if w not in stop_words and len(w) > 3]
    return Counter(words).most_common(top_n)


def get_active_members(messages, top_n=10):
    """Get most active members based on message count"""
    author_counts = Counter([msg.author_id for msg in messages])
    return author_counts.most_common(top_n)


def generate_weekly_report(server_id):
    """Generate weekly analytics report"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    messages = Message.query.filter(Message.timestamp >= week_ago).all()

    top_topics = get_top_topics(messages)
    active_members = get_active_members(messages)

    return {
        'top_topics': json.dumps(dict(top_topics)),
        'active_members': json.dumps(dict(active_members)),
        'total_messages': len(messages)
    }
