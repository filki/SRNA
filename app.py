from flask import Flask, render_template, request, send_file
from services.visualization_service import generate_top_authors_svg
from services.db_service import cached_get_reviews
from services.analysis_service import generate_wordcloud

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    keyword = request.form.get('keyword') if request.method == 'POST' else None
    reviews = cached_get_reviews(keyword=keyword)
    return render_template('search.html', reviews=reviews)

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
