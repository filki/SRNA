from datetime import datetime
import sqlite3
from typing import List, Dict, Any
from .search_service import search_service

DATABASE = 'data/steam_reviews_with_authors.db'

def format_timestamp(unix_timestamp):
    """Konwertuje znacznik czasu UNIX na czytelną datę."""
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def cached_get_reviews(page: int = 1, per_page: int = 20, keyword: str = "", filter_option: str = "all") -> List[Dict[str, Any]]:
    """
    Pobiera recenzje z bazy danych z uwzględnieniem filtrów i wyszukiwania.
    """
    offset = (page - 1) * per_page
    
    print(f"\nDebug: Starting review fetch with keyword: '{keyword}', filter: {filter_option}")
    
    # Base query with all necessary fields
    query = """
        SELECT r.*, 
               a.num_games_owned as games_owned,
               a.num_reviews as total_reviews,
               a.playtime_forever,
               a.playtime_last_two_weeks,
               a.playtime_at_review
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        WHERE 1=1
    """
    params = []

    # Add filter conditions
    if filter_option == "positive":
        query += " AND r.is_positive = 'Positive'"
    elif filter_option == "negative":
        query += " AND r.is_positive != 'Positive'"

    # If keyword provided, use LIKE for initial filtering
    if keyword:
        query += " AND r.content LIKE ?"
        params.append(f"%{keyword}%")

    # Add limit and offset
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page * 3, offset])  # Fetch more reviews for better relevance calculation
    
    print(f"Debug: SQL Query: {query}")
    print(f"Debug: SQL Params: {params}")
    
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        # Execute query
        cur.execute(query, params)
        reviews = [dict(row) for row in cur.fetchall()]
        print(f"Debug: Fetched {len(reviews)} reviews from database")
        
        # Format timestamps
        for review in reviews:
            review['timestamp_created'] = format_timestamp(review['timestamp_created'])
            review['relevance'] = 0.0  # Default relevance score
            
        print(f"Debug: Sample review content: '{reviews[0]['content'][:100]}...' if reviews else 'No reviews'")

        # If keyword provided, calculate relevancy scores and sort
        if keyword and reviews:
            print(f"Debug: Calculating relevance scores for keyword: '{keyword}'")
            reviews = search_service.search_reviews(keyword, reviews)
            # Take only top per_page reviews after sorting by relevance
            reviews = reviews[:per_page]
            print(f"Debug: After relevance calculation, first review score: {reviews[0]['relevance'] if reviews else 0.0}")
        
        return reviews
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        cur.close()
        con.close()

def get_total_reviews_count(keyword: str = "", filter_option: str = "all") -> int:
    """
    Zwraca całkowitą liczbę recenzji w bazie danych.
    """
    query = "SELECT COUNT(*) FROM reviews WHERE 1=1"
    params = []
    
    if keyword:
        query += " AND content LIKE ?"
        params.append(f"%{keyword}%")
        
    if filter_option == "positive":
        query += " AND is_positive = 'Positive'"
    elif filter_option == "negative":
        query += " AND is_positive != 'Positive'"
    
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

def get_review_by_id(review_id: int) -> Dict[str, Any]:
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

def calculate_relevance(query_text: str, reviews: List[Dict[str, Any]]) -> List[float]:
    """
    Oblicza relevance score dla każdej recenzji względem zapytania.
    """
    if not reviews or not query_text:
        return [0.0] * len(reviews)
        
    # Przygotuj teksty do porównania
    review_texts = [review['content'] for review in reviews]
    
    # Użyj istniejącego vectorizera lub stwórz nowy
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
        
    try:
        # Przekształć teksty na wektory TF-IDF
        tfidf_matrix = vectorizer.fit_transform(review_texts + [query_text])
        
        # Oblicz podobieństwo cosinusowe między zapytaniem a każdą recenzją
        from sklearn.metrics.pairwise import cosine_similarity
        query_vector = tfidf_matrix[-1]
        review_vectors = tfidf_matrix[:-1]
        
        similarities = cosine_similarity(review_vectors, query_vector)
        return similarities.flatten()
        
    except Exception as e:
        print(f"Error calculating relevance: {e}")
        return [0.0] * len(reviews)
