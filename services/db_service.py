from functools import lru_cache
import sqlite3
from datetime import datetime

DATABASE = 'data/steam_reviews_with_timestamp.db'

def format_timestamp(unix_timestamp):
    """Konwertuje znacznik czasu UNIX na czytelną datę."""
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

@lru_cache(maxsize=32)
def cached_get_reviews(keyword=None, limit=20, offset=0):
    """
    Funkcja cache'ująca wyniki wyszukiwania w pamięci.
    """
    query = """
        SELECT author_id, content, is_positive, timestamp_created
        FROM reviews
        WHERE content LIKE ?
        LIMIT ? OFFSET ?
    """
    args = (f"%{keyword}%", limit, offset)

    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(query, args)
    results = cur.fetchall()
    cur.close()
    con.close()

    # Konwertuj timestamp na czytelne daty
    reviews = []
    for row in results:
        review = dict(row)
        review['timestamp_created'] = format_timestamp(review['timestamp_created'])
        reviews.append(review)

    return tuple(reviews)  # Cache wymaga hashowalnych danych

def get_total_reviews_count(keyword=None):
    """
    Zwraca całkowitą liczbę recenzji pasujących do słowa kluczowego.
    """
    query = "SELECT COUNT(*) FROM reviews WHERE content LIKE ?"
    args = (f"%{keyword}%",)

    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(query, args)
    total_count = cur.fetchone()[0]
    cur.close()
    con.close()
    return total_count
