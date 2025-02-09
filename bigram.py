import nltk
from nltk import word_tokenize
from nltk.util import ngrams
from collections import Counter
import string
from nltk.corpus import stopwords

# Ensure necessary resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

def retrieve_top_topics_bigram(messages, n=5):
    """Find the most common single words and bigrams in a list of messages, merging related mentions."""
    stop_words = set(stopwords.words('english'))
    all_tokens = []
    all_bigrams = []

    for msg in messages:
        tokens = word_tokenize(msg.lower())  # Convert to lowercase for consistency
        tokens = [word for word in tokens if word.isalnum() and word not in stop_words]  # Remove punctuation and stopwords
        all_tokens.extend(tokens)
        all_bigrams.extend(list(ngrams(tokens, 2)))

    # Count single word and bigram frequencies
    word_counts = Counter(all_tokens)
    bigram_counts = Counter(all_bigrams)

    # Merge frequencies: if a bigram is dominant, it absorbs its individual word counts
    topic_counts = Counter(word_counts)
    for bigram, bigram_freq in bigram_counts.items():
        topic_counts[bigram] = bigram_freq
        if bigram[0] in topic_counts:
            topic_counts[bigram[0]] -= bigram_freq
        if bigram[1] in topic_counts:
            topic_counts[bigram[1]] -= bigram_freq

    # Remove negative counts due to over-subtraction
    topic_counts = {k: v for k, v in topic_counts.items() if v > 0}

    sorted_topics = Counter(topic_counts).most_common(n)

    # Format output
    formatted_topics = [(" ".join(topic) if isinstance(topic, tuple) else topic, freq) for topic, freq in sorted_topics]

    return formatted_topics