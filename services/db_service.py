from functools import lru_cache
import sqlite3

DATABASE = 'data/steam_reviews_with_timestamp.db'

@lru_cache(maxsize=32)
def cached_get_reviews(keyword=None, limit=20):
    """
    Funkcja cache'ująca wyniki wyszukiwania w pamięci.
    """
    query = "SELECT author_id, content, is_positive, timestamp_created FROM reviews LIMIT ?"
    args = (limit,)
    if keyword:
        query = """
            SELECT author_id, content, is_positive, timestamp_created 
            FROM reviews 
            WHERE content LIKE ? 
            LIMIT ?
        """
        args = (f"%{keyword}%", limit)

    # Wykonaj zapytanie do bazy danych
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(query, args)
    results = cur.fetchall()
    cur.close()
    con.close()
    return [dict(row) for row in results]
