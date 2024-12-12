from functools import lru_cache
import sqlite3
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATABASE = 'data/steam_reviews_with_timestamp.db'

def format_timestamp(unix_timestamp):
    """Konwertuje znacznik czasu UNIX na czytelną datę."""
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def calculate_relevance(query, documents):
    """Oblicza miary relewancji TF-IDF dla zapytania i dokumentów."""
    if not query:
        return [None] * len(documents)

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform([query] + documents)
    query_vector = tfidf_matrix[0]
    document_vectors = tfidf_matrix[1:]
    relevance_scores = cosine_similarity(query_vector, document_vectors).flatten()
    return relevance_scores

@lru_cache(maxsize=32)
def cached_get_reviews(keyword=None, filter_option='all', limit=20, offset=0):
    """
    Funkcja cache'ująca wyniki wyszukiwania w pamięci.
    """
    query = """
        SELECT author_id, content, is_positive, timestamp_created
        FROM reviews
        WHERE content LIKE ?
    """
    args = [f"%{keyword}%"]

    if filter_option == 'positive':
        query += " AND is_positive = 'Positive'"
    elif filter_option == 'negative':
        query += " AND is_positive = 'Negative'"

    query += " LIMIT ? OFFSET ?"
    args.extend([limit, offset])

    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(query, args)
    results = cur.fetchall()
    cur.close()
    con.close()

    # Przetwórz wyniki
    documents = [row['content'] for row in results]
    relevance_scores = calculate_relevance(keyword, documents)

    reviews = []
    for idx, row in enumerate(results):
        review = dict(row)
        review['timestamp_created'] = format_timestamp(review['timestamp_created'])
        review['relevance'] = relevance_scores[idx] if relevance_scores[idx] is not None else 'NULL'
        reviews.append(review)

    return tuple(reviews)  # Cache wymaga hashowalnych danych

def get_total_reviews_count(keyword=None, filter_option='all'):
    """
    Zwraca całkowitą liczbę recenzji pasujących do słowa kluczowego i filtra.
    """
    query = "SELECT COUNT(*) FROM reviews WHERE content LIKE ?"
    args = [f"%{keyword}%"]

    if filter_option == 'positive':
        query += " AND is_positive = 'Positive'"
    elif filter_option == 'negative':
        query += " AND is_positive = 'Negative'"

    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(query, args)
    total_count = cur.fetchone()[0]
    cur.close()
    con.close()
    return total_count
