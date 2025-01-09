from flask import Flask, render_template, request, send_file
from services.visualization_service import generate_top_authors_svg
from services.db_service import cached_get_reviews, get_total_reviews_count
from services.analysis_service import generate_wordcloud

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '')
    filter_option = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)

    # Pobierz recenzje z uwzględnieniem limitu i offsetu
    offset = (page - 1) * 20
    reviews = cached_get_reviews(keyword=keyword, filter_option=filter_option, limit=20, offset=offset)

    # Oblicz liczbę stron
    total_reviews = get_total_reviews_count(keyword, filter_option)
    total_pages = (total_reviews + 19) // 20

    return render_template(
        'search.html',
        reviews=reviews,
        current_page=page,
        total_pages=total_pages,
        selected_filter=filter_option,
        keyword=keyword
    )

@app.route('/visualizations')
def visualizations():
    svg_chart = generate_top_authors_svg()
    return render_template('visualizations.html', svg_chart=svg_chart)

@app.route('/clear-cache')
def clear_cache():
    cached_get_reviews.cache_clear()
    return "Cache został wyczyszczony!"

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/analysis/wordcloud')
def wordcloud():
    # Wygeneruj chmurę słów
    img = generate_wordcloud()
    return send_file(img, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
