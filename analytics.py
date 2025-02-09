from collections import Counter
from models import Message, ServerStats
from datetime import datetime, timedelta

import json
import nltk
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('wordnet')


def get_top_topics(messages, top_n=5):
    """Extract top topics from messages using simple word frequency"""
    words = ' '.join([msg.content for msg in messages]).lower().split()
    # Get NLTK stop words
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    # Filter out stop words, short words, and command words (starting with !)
    words = [
        w for w in words
        if w not in stop_words and len(w) > 3 and not w.startswith('!')
    ]

    # Lemmatize words
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]

    return Counter(words).most_common(top_n)


def get_top_topics_bigram(messages, top_n=5):
    """Extract top topics from messages using bigram frequency"""
    from bigram import retrieve_top_topics_bigram

    # Extract author_id and content
    formatted_messages = [(msg.content) for msg in messages]

    # Call your bigram analysis function
    return retrieve_top_topics_bigram(formatted_messages, top_n)


def get_active_members(messages, top_n=10):
    """Get most active members based on message count"""
    author_counts = Counter([msg.author_id for msg in messages])
    return author_counts.most_common(top_n)


def get_influential_members(messages, top_n=10):
    """Get most influential members based on message * (reaction cnt + 1)"""
    influence_score = Counter(
        [msg.author_id * (3 * msg.reaction_count + 1) for msg in messages])

    #for msg in messages:
    #    influence_score[msg.author_id] += (msg.reaction_count + 1)

    return influence_score.most_common(top_n)


def generate_weekly_report(server_id):
    """Generate weekly analytics report"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_period = datetime.utcnow() - timedelta(days=0)
    messages = Message.query.filter(Message.timestamp >= week_ago).all()

    top_topics = get_top_topics_bigram(messages)
    active_members = get_active_members(messages)

    return {
        'top_topics': json.dumps(dict(top_topics)),
        'active_members': json.dumps(dict(active_members)),
        'influential_members'
        'total_messages': len(messages)
    }
