from datetime import datetime
import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATABASE = 'data/steam_reviews_with_authors.db'

def format_timestamp(unix_timestamp):
    """Konwertuje znacznik czasu UNIX na czytelną datę."""
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def cached_get_reviews(page=1, per_page=10, keyword=None, filter_option='all'):
    """
    Pobiera stronicowaną listę recenzji z bazy danych.
    """
    offset = (page - 1) * per_page
    
    # Buduj zapytanie bazowe
    query = """
        SELECT r.*, a.num_games_owned as games_owned, a.num_reviews as total_reviews
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        WHERE 1=1
    """
    params = []
    
    # Dodaj warunki wyszukiwania
    if keyword:
        query += " AND r.content LIKE ?"
        params.append(f"%{keyword}%")
    
    if filter_option == 'positive':
        query += " AND r.is_positive = 'Positive'"
    elif filter_option == 'negative':
        query += " AND r.is_positive = 'Negative'"
    
    # Dodaj sortowanie i limit
    query += " ORDER BY r.timestamp_created DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute(query, params)
        reviews = [dict(row) for row in cur.fetchall()]
        
        # Formatuj daty i dodaj informacje o autorze
        for review in reviews:
            review['timestamp_created'] = format_timestamp(review['timestamp_created'])
            review['author'] = {
                'games_owned': review.get('games_owned', 0),
                'total_reviews': review.get('total_reviews', 0)
            }
            
            # Oblicz relewancję jeśli jest słowo kluczowe
            if keyword:
                relevance = calculate_relevance(keyword, [review])[0]
                review['relevance'] = relevance if relevance is not None else 'NULL'
            else:
                review['relevance'] = 'NULL'
        
        return reviews
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        cur.close()
        con.close()

def get_total_reviews_count(keyword=None, filter_option='all'):
    """
    Zwraca całkowitą liczbę recenzji w bazie danych.
    """
    query = "SELECT COUNT(*) FROM reviews WHERE 1=1"
    params = []
    
    if keyword:
        query += " AND content LIKE ?"
        params.append(f"%{keyword}%")
        
    if filter_option == 'positive':
        query += " AND is_positive = 'Positive'"
    elif filter_option == 'negative':
        query += " AND is_positive = 'Negative'"
    
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    try:
        cur.execute(query, params)
        return cur.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    finally:
        cur.close()
        con.close()

def get_review_by_id(review_id):
    """
    Pobiera szczegółowe informacje o recenzji na podstawie jej ID.
    """
    query = """
        SELECT r.*, 
               a.num_games_owned as games_owned,
               a.num_reviews as total_reviews,
               a.playtime_forever,
               a.playtime_last_two_weeks,
               a.playtime_at_review
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        WHERE r.id = ?
    """
    
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        cur.execute(query, [review_id])
        result = cur.fetchone()
        
        if result is None:
            return None
            
        review = dict(result)
        review['timestamp_created'] = format_timestamp(review['timestamp_created'])
        
        # Konwertuj pola boolean (zapisane jako tekst 'true'/'false' lub '1'/'0')
        def convert_text_to_bool(value):
            if value is None:
                return False
            return str(value).lower() in ('true', '1', 't', 'y', 'yes')
            
        review['steam_purchase'] = convert_text_to_bool(review.get('steam_purchase'))
        review['received_for_free'] = convert_text_to_bool(review.get('received_for_free'))
        review['written_during_early_access'] = convert_text_to_bool(review.get('written_during_early_access'))
        
        review['author'] = {
            'games_owned': review.get('games_owned', 0),
            'total_reviews': review.get('total_reviews', 0),
            'playtime_forever': review.get('playtime_forever', 0),
            'playtime_last_two_weeks': review.get('playtime_last_two_weeks', 0),
            'playtime_at_review': review.get('playtime_at_review', 0)
        }
        
        return review
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        cur.close()
        con.close()

def calculate_relevance(query_text, reviews, vectorizer=None):
    """
    Oblicza relevance score dla każdej recenzji względem zapytania.
    """
    if not reviews or not query_text:
        return np.zeros(len(reviews) if reviews else 0)
        
    # Przygotuj teksty do porównania
    review_texts = [review['content'] for review in reviews]
    
    # Użyj istniejącego vectorizera lub stwórz nowy
    if vectorizer is None:
        vectorizer = TfidfVectorizer(stop_words='english')
        
    try:
        # Przekształć teksty na wektory TF-IDF
        tfidf_matrix = vectorizer.fit_transform(review_texts + [query_text])
        
        # Oblicz podobieństwo cosinusowe między zapytaniem a każdą recenzją
        query_vector = tfidf_matrix[-1]
        review_vectors = tfidf_matrix[:-1]
        
        similarities = cosine_similarity(review_vectors, query_vector)
        return similarities.flatten()
        
    except Exception as e:
        print(f"Error calculating relevance: {e}")
        return np.zeros(len(reviews))
