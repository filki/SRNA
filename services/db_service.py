import sqlite3

DATABASE = 'data/steam_reviews_with_timestamp.db'

def query_database(query, args=(), one=False):
    """Funkcja pomocnicza do wykonywania zapytań SQL."""
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    con.close()
    return (rv[0] if rv else None) if one else rv

def get_reviews(limit=20, keyword=None):
    """Pobiera recenzje z bazy danych."""
    query = "SELECT author_id, content, is_positive, timestamp_created FROM steam_reviews LIMIT ?"
    args = (limit,)
    if keyword:
        query = """
            SELECT author_id, content, is_positive, timestamp_created 
            FROM steam_reviews 
            WHERE content LIKE ? 
            LIMIT ?
        """
        args = (f"%{keyword}%", limit)
    return query_database(query, args)
