from flask import Flask, render_template, request, send_file, abort
from services.visualization_service import generate_top_authors_svg
from services.db_service import cached_get_reviews, get_total_reviews_count, get_review_by_id
import sqlite3

app = Flask(__name__)

# Add built-in functions to Jinja2 context
app.jinja_env.globals.update(
    max=max,
    min=min,
    len=len,
    range=range
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '')
    filter_option = request.args.get('filter_option', 'all')
    scoring_method = request.args.get('scoring_method', 'tfidf')  # Default to TF-IDF
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Get total count first
    total_reviews = get_total_reviews_count(keyword, filter_option)
    total_pages = (total_reviews + per_page - 1) // per_page

    # Ensure page is within bounds
    page = min(max(1, page), total_pages if total_pages > 0 else 1)

    # Get globally sorted and paginated reviews
    reviews = cached_get_reviews(
        page=page,
        per_page=per_page,
        keyword=keyword,
        filter_option=filter_option,
        scoring_method=scoring_method
    )

    scoring_methods = [
        {'id': 'tfidf', 'name': 'TF-IDF', 'description': 'Zaawansowane wyszukiwanie uwzględniające częstość słów'},
        {'id': 'jaccard', 'name': 'Jaccard', 'description': 'Proste porównanie na podstawie wspólnych słów'}
    ]

    return render_template(
        'search.html',
        reviews=reviews,
        page=page,
        total_pages=total_pages,
        filter_option=filter_option,
        keyword=keyword,
        total_results=total_reviews,
        scoring_methods=scoring_methods,
        scoring_method=scoring_method
    )

@app.route('/visualizations')
def visualizations():
    svg_chart = generate_top_authors_svg()
    return render_template('visualizations.html', svg_chart=svg_chart)

@app.route('/clear-cache')
def clear_cache():
    cached_get_reviews.cache_clear()
    return "Cache został wyczyszczony!"

@app.route('/review/<int:review_id>')
def review_detail(review_id):
    review = get_review_by_id(review_id)
    if review is None:
        abort(404)
    return render_template('review_detail.html', review=review)

@app.route('/games')
def show_games():
    # Connect to the database
    conn = sqlite3.connect('data/steamspy_data.db')
    cursor = conn.cursor()

    # Get filter values from request
    name_filter = request.args.get('name', '')
    owner_filter = request.args.get('owners', '')
    developer_filter = request.args.get('developer', '')
    publisher_filter = request.args.get('publisher', '')
    language_filter = request.args.get('languages', '')
    genre_filter = request.args.get('genre', '')

    # Base query
    query = "SELECT * FROM games WHERE 1=1"
    params = []

    # Add filters if they exist
    if name_filter:
        query += " AND name LIKE ?"
        params.append(f"%{name_filter}%")
    if owner_filter:
        query += " AND owners = ?"
        params.append(owner_filter)
    if developer_filter:
        query += " AND developer = ?"
        params.append(developer_filter)
    if publisher_filter:
        query += " AND publisher = ?"
        params.append(publisher_filter)
    if language_filter:
        query += " AND languages LIKE ?"
        params.append(f"%{language_filter}%")
    if genre_filter:
        query += " AND genre = ?"
        params.append(genre_filter)

    # Get filtered games
    cursor.execute(query, params)
    games = cursor.fetchall()

    # Get unique values for dropdowns
    cursor.execute("SELECT DISTINCT owners FROM games ORDER BY owners")
    owners = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT developer FROM games ORDER BY developer")
    developers = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT publisher FROM games ORDER BY publisher")
    publishers = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT languages FROM games ORDER BY languages")
    languages = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT genre FROM games ORDER BY genre")
    genres = [row[0] for row in cursor.fetchall()]

    # Close the connection
    conn.close()

    return render_template('games.html', 
                         games=games,
                         owners=owners,
                         developers=developers,
                         publishers=publishers,
                         languages=languages,
                         genres=genres,
                         filters={
                             'name': name_filter,
                             'owners': owner_filter,
                             'developer': developer_filter,
                             'publisher': publisher_filter,
                             'languages': language_filter,
                             'genre': genre_filter
                         })

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
