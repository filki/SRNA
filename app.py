from flask import Flask, render_template, request, send_file, abort
from services.visualization_service import generate_top_authors_svg
from services.db_service import cached_get_reviews, get_total_reviews_count, get_review_by_id

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
