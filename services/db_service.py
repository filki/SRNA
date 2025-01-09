from datetime import datetime
import sqlite3
from typing import List, Dict, Any
from .search_service import search_service
from .text_analysis_service import text_analysis_service
import traceback

DATABASE = 'data/steam_reviews_with_authors.db'

def format_timestamp(unix_timestamp):
    """Konwertuje znacznik czasu UNIX na czytelną datę."""
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def build_query_conditions(keyword: str = "", filter_option: str = "all", game_id: str = "", 
                         date_from: str = None, date_to: str = None, min_playtime: int = None,
                         min_funny: int = None, received_free: bool = None, 
                         early_access: bool = None) -> tuple[str, list]:
    """
    Builds query conditions and parameters for filtering reviews.
    Returns a tuple of (conditions_string, parameters_list)
    """
    conditions = []
    params = []
    
    # Base conditions
    if keyword:
        conditions.append("r.content LIKE ?")
        params.append(f"%{keyword}%")

    if filter_option == "positive":
        conditions.append("r.is_positive = 'Positive'")
    elif filter_option == "negative":
        conditions.append("r.is_positive = 'Negative'")

    if game_id:
        conditions.append("r.app_id = ?")
        params.append(int(game_id))

    # Date range conditions
    if date_from:
        conditions.append("r.timestamp_created >= strftime('%s', ?)")
        params.append(date_from)
    if date_to:
        conditions.append("r.timestamp_created <= strftime('%s', ?)")
        params.append(date_to)

    # Playtime condition
    if min_playtime is not None:
        conditions.append("a.playtime_at_review >= ?")
        params.append(min_playtime * 60)  # Convert hours to minutes

    # Funny votes condition
    if min_funny is not None:
        conditions.append("r.votes_funny >= ?")
        params.append(min_funny)

    # Boolean filters
    if received_free is not None:
        conditions.append("r.received_for_free = ?")
        params.append(str(received_free))
    if early_access is not None:
        conditions.append("r.written_during_early_access = ?")
        params.append(str(early_access))

    return " AND ".join(conditions) if conditions else "1=1", params

def cached_get_reviews(page: int = 1, per_page: int = 20, keyword: str = "", 
                      filter_option: str = "all", scoring_method: str = "tfidf",
                      game_id: str = "", date_from: str = None, date_to: str = None,
                      min_playtime: int = None, min_funny: int = None,
                      received_free: bool = None, early_access: bool = None) -> List[Dict[str, Any]]:
    """
    Pobiera recenzje z bazy danych z uwzględnieniem wszystkich filtrów jednocześnie.
    """
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Build query conditions
    conditions, params = build_query_conditions(
        keyword, filter_option, game_id, date_from, date_to,
        min_playtime, min_funny, received_free, early_access
    )

    # Base query with all necessary fields
    query = f"""
        SELECT r.*, 
               a.num_games_owned as games_owned,
               a.num_reviews as total_reviews,
               a.playtime_forever,
               a.playtime_at_review,
               g.name as game_name,
               g.developer as game_developer,
               g.publisher as game_publisher,
               g.genre as game_genre,
               g.tags as game_tags,
               g.languages as game_languages,
               g.owners as game_owners
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        LEFT JOIN games g ON r.app_id = g.app_id
        WHERE {conditions}
    """

    print(f"\nDebug: Query conditions: {conditions}")
    print(f"Debug: Query parameters: {params}")
    
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        # Execute query
        cur.execute(query, params)
        columns = [col[0] for col in cur.description]
        all_reviews = [dict(zip(columns, row)) for row in cur.fetchall()]

        # Format timestamps and initialize relevance scores
        for review in all_reviews:
            review['timestamp_created'] = format_timestamp(review['timestamp_created'])
            review['relevance'] = 0.0  # Default relevance score
            
            # Create author dictionary structure
            review['author'] = {
                'games_owned': review.get('games_owned', 0),
                'total_reviews': review.get('total_reviews', 0),
                'playtime_forever': review.get('playtime_forever', 0),
                'playtime_last_two_weeks': review.get('playtime_last_two_weeks', 0),
                'playtime_at_review': review.get('playtime_at_review', 0)
            }
            
            # Convert boolean fields
            def convert_text_to_bool(value):
                if value is None:
                    return False
                return str(value).lower() in ('true', '1', 't', 'y', 'yes')
                
            review['steam_purchase'] = convert_text_to_bool(review.get('steam_purchase'))
            review['received_for_free'] = convert_text_to_bool(review.get('received_for_free'))
            review['written_during_early_access'] = convert_text_to_bool(review.get('written_during_early_access'))

        # If keyword provided, calculate relevancy scores and sort ALL reviews
        if keyword and all_reviews:
            print(f"Debug: Calculating relevance scores using {scoring_method} for keyword: '{keyword}'")
            all_reviews = search_service.search_reviews(keyword, all_reviews, scoring_method)
            print(f"Debug: After global sorting, first review score: {all_reviews[0]['relevance'] if all_reviews else 0.0}")
        
        # Apply pagination to the globally sorted results
        paginated_reviews = all_reviews[start_idx:end_idx]
        print(f"Debug: Returning page {page} ({len(paginated_reviews)} reviews)")
        
        return paginated_reviews
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()
        return []
    finally:
        cur.close()
        con.close()

def get_total_reviews_count(keyword: str = "", filter_option: str = "all", 
                          game_id: str = "", date_from: str = None, 
                          date_to: str = None, min_playtime: int = None,
                          min_funny: int = None, received_free: bool = None,
                          early_access: bool = None) -> int:
    """
    Zwraca całkowitą liczbę recenzji spełniających wszystkie warunki filtrowania.
    """
    # Build query conditions
    conditions, params = build_query_conditions(
        keyword, filter_option, game_id, date_from, date_to,
        min_playtime, min_funny, received_free, early_access
    )

    query = f"""
        SELECT COUNT(*)
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        LEFT JOIN games g ON r.app_id = g.app_id
        WHERE {conditions}
    """
    
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    try:
        cur.execute(query, params)
        return cur.fetchone()[0]
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
               a.playtime_at_review,
               g.name as game_name,
               g.developer as game_developer,
               g.publisher as game_publisher,
               g.genre as game_genre,
               g.tags as game_tags,
               g.languages as game_languages,
               g.owners as game_owners
        FROM reviews r
        LEFT JOIN authors a ON r.author_id = a.author_id
        LEFT JOIN games g ON r.app_id = g.app_id
        WHERE r.id = ?
    """
    
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        print(f"Executing query: {query}")
        cur.execute(query, [review_id])
        result = cur.fetchone()
        print(f"Query returned {result} results")
        if result is None:
            return None
            
        review = dict(result)
        review['timestamp_created'] = format_timestamp(review['timestamp_created'])
        
        # Add text analysis
        review['text_stats'] = text_analysis_service.analyze_text(review['content'])
        
        # Convert boolean fields
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
        traceback.print_exc()
        return None
    finally:
        cur.close()
        con.close()

def get_games_list():
    """
    Returns a list of all games with their app_ids and names.
    """
    query = """
        SELECT DISTINCT app_id, name
        FROM games
        WHERE name IS NOT NULL
        ORDER BY name
    """
    
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    try:
        print(f"Executing query: {query}")
        cur.execute(query)
        results = [{'app_id': row[0], 'name': row[1]} for row in cur.fetchall()]
        print(f"Query returned {len(results)} results")
        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()
        return []
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
        traceback.print_exc()
        return [0.0] * len(reviews)


# FUNKCJE DLA LLM'a w celu weryfikacji działania aplikacji
def execute_query(query: str) -> List[Dict[str, Any]]:
    print(f"Connecting to database at: {DATABASE}")
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    try:
        print(f"Executing query: {query}")
        cur.execute(query)
        results = [dict(row) for row in cur.fetchall()]
        print(f"Query returned {len(results)} results")
        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()
        return []
    finally:
        cur.close()
        con.close()

def get_table_info():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        print("Getting table schema...")
        cur.execute("SELECT * FROM reviews LIMIT 1")
        columns = [description[0] for description in cur.description]
        print("Table columns:", columns)
        return columns
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()
        return []
    finally:
        cur.close()
        con.close()

def get_top_genres():
    query = """
    SELECT g.genre as name, COUNT(*) as review_count
    FROM reviews r
    JOIN games g ON r.app_id = g.app_id
    WHERE g.genre IS NOT NULL AND g.genre != ''
    GROUP BY g.genre
    ORDER BY review_count DESC
    LIMIT 10
    """
    result = execute_query(query)
    print("Top Genres Data:", result)
    return result

def get_top_publishers():
    query = """
    SELECT g.publisher as name, COUNT(*) as review_count
    FROM reviews r
    JOIN games g ON r.app_id = g.app_id
    WHERE g.publisher IS NOT NULL AND g.publisher != ''
    GROUP BY g.publisher
    ORDER BY review_count DESC
    LIMIT 10
    """
    result = execute_query(query)
    print("Top Publishers Data:", result)
    return result

def get_top_developers():
    query = """
    SELECT g.developer as name, COUNT(*) as review_count
    FROM reviews r
    JOIN games g ON r.app_id = g.app_id
    WHERE g.developer IS NOT NULL AND g.developer != ''
    GROUP BY g.developer
    ORDER BY review_count DESC
    LIMIT 10
    """
    result = execute_query(query)
    print("Top Developers Data:", result)
    return result

def get_unique_genres():
    """Get list of unique genres from the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT genre FROM games WHERE genre IS NOT NULL ORDER BY genre")
    genres = [row[0] for row in cursor.fetchall()]
    conn.close()
    return genres

def test_query():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    try:
        print("\nTesting simple query...")
        cur.execute("SELECT COUNT(*) FROM reviews")
        count = cur.fetchone()[0]
        print(f"Total reviews in database: {count}")
        
        print("\nSample review data:")
        cur.execute("SELECT * FROM reviews LIMIT 1")
        sample = dict(zip([col[0] for col in cur.description], cur.fetchone()))
        print(sample)
        return count
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()
        return 0
    finally:
        cur.close()
        con.close()

# Call test query
test_query()

get_table_info()
