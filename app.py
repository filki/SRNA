from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from textblob import TextBlob
app = Flask(__name__)

# SQLite Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///steam_reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from textblob import TextBlob

class SteamReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, nullable=False)  # Add this field
    author_steamid = db.Column(db.String(100), nullable=False)
    review = db.Column(db.Text, nullable=False)
    voted_up = db.Column(db.Boolean, nullable=False)
    playtime_forever = db.Column(db.Integer, nullable=True)
    review_score = db.Column(db.Integer, nullable=True)
    weighted_vote_score = db.Column(db.Float, nullable=True)
    timestamp_created = db.Column(db.Integer, nullable=True)
    timestamp_updated = db.Column(db.Integer, nullable=True)
    author_num_games_owned = db.Column(db.Integer, nullable=True)
    author_num_reviews = db.Column(db.Integer, nullable=True)
    author_playtime_last_two_weeks = db.Column(db.Integer, nullable=True)
    author_playtime_at_review = db.Column(db.Integer, nullable=True)
    comments_count = db.Column(db.Integer, nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<SteamReview {self.author_steamid} for Game {self.game_id}>"



@app.route('/')
def index():
    return render_template('index.html')
@app.route('/get_reviews', methods=['GET', 'POST'])
def get_reviews():
    if request.method == 'POST':
        app_id = request.form.get('app_id', 570, type=int)
        review_type = request.form.get('review_type', 'positive')
        total_reviews = min(request.form.get('total_reviews', 25000, type=int), 25000)

        # Fetch reviews from Steam
        reviews = fetch_reviews(app_id, review_type, total_reviews)

        # Save reviews to database with the app_id as game_id
        save_reviews_to_db(reviews, game_id=app_id)

        # Stay on index.html and show success message
        return render_template('index.html', success_message="Reviews have been successfully fetched and stored.")
    return render_template('index.html')


@app.route('/results')
def results():
    game_id = request.args.get('game_id', type=int)  # New filter
    voted_up = request.args.get('voted_up')
    min_playtime = request.args.get('min_playtime', type=int)
    max_playtime = request.args.get('max_playtime', type=int)
    min_sentiment = request.args.get('min_sentiment', type=float)
    max_sentiment = request.args.get('max_sentiment', type=float)

    query = SteamReview.query

    if game_id is not None:
        query = query.filter(SteamReview.game_id == game_id)

    if voted_up is not None:
        query = query.filter(SteamReview.voted_up == (voted_up.lower() == "true"))

    if min_playtime is not None:
        query = query.filter(SteamReview.playtime_forever >= min_playtime)

    if max_playtime is not None:
        query = query.filter(SteamReview.playtime_forever <= max_playtime)

    if min_sentiment is not None:
        query = query.filter(SteamReview.sentiment_score >= min_sentiment)

    if max_sentiment is not None:
        query = query.filter(SteamReview.sentiment_score <= max_sentiment)

    reviews = query.all()
    return render_template('results.html', reviews=reviews)




def fetch_reviews(app_id, review_type, total_reviews=200):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num={total_reviews}&filter={review_type}&language=english"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('success', 0):
                return data.get('reviews', [])
        return []
    except Exception as e:
        return [f"Error fetching reviews: {e}"]

def save_reviews_to_db(reviews, game_id):
    db.session.bulk_insert_mappings(SteamReview, [
        {
            'game_id': game_id,  # Add game_id to each review
            'author_steamid': review['author'].get('steamid', 'Unknown'),
            'review': review.get('review', ''),
            'voted_up': review.get('voted_up', False),
            'playtime_forever': review['author'].get('playtime_forever', 0),
            'review_score': review.get('review_score', None),
            'weighted_vote_score': review.get('weighted_vote_score', 0.0),
            'timestamp_created': review.get('timestamp_created', None),
            'timestamp_updated': review.get('timestamp_updated', None),
            'author_num_games_owned': review['author'].get('num_games_owned', 0),
            'author_num_reviews': review['author'].get('num_reviews', 0),
            'author_playtime_last_two_weeks': review['author'].get('playtime_last_two_weeks', 0),
            'author_playtime_at_review': review['author'].get('playtime_at_review', 0),
            'comments_count': review.get('comment_count', 0),
            'sentiment_score': TextBlob(review.get('review', '')).sentiment.polarity
        }
        for review in reviews
    ])
    db.session.commit()


@app.route('/search_game_title')
def search_game_title():
    title = request.args.get('title', '').strip()
    if not title:
        return []

    # Fetch games using the Steam API
    response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    data = response.json()

    # Filter games that match the title
    games = [
        {"name": game["name"], "app_id": game["appid"]}
        for game in data["applist"]["apps"]
        if title.lower() in game["name"].lower()
    ]

    return games[:10]  # Return top 10 results



@app.route('/delete_reviews', methods=['POST'])
def delete_reviews():
    db.session.query(SteamReview).delete()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/visualization')
def visualization():
    # Example: Bar chart for positive vs. negative reviews
    positive = SteamReview.query.filter_by(voted_up=True).count()
    negative = SteamReview.query.filter_by(voted_up=False).count()

    # Visualization 1: Positive vs Negative Reviews
    plt.figure(figsize=(8, 6))
    plt.bar(['Positive', 'Negative'], [positive, negative], color=['green', 'red'])
    plt.title('Positive vs Negative Reviews')
    plt.ylabel('Count')
    plt.xlabel('Sentiment')

    img1 = BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode()
    plt.close()

    # Visualization 2: Sentiment Score Distribution
    sentiment_scores = [review.sentiment_score for review in SteamReview.query.all() if review.sentiment_score is not None]
    plt.figure(figsize=(8, 6))
    plt.hist(sentiment_scores, bins=20, color='blue', edgecolor='black')
    plt.title('Sentiment Score Distribution')
    plt.xlabel('Sentiment Score')
    plt.ylabel('Count')

    img2 = BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()

    # Visualization 3: Average Sentiment Score per Game
    game_sentiment = db.session.query(
        SteamReview.game_id, db.func.avg(SteamReview.sentiment_score).label('avg_sentiment')
    ).group_by(SteamReview.game_id).all()

    game_ids, avg_sentiments = zip(*game_sentiment) if game_sentiment else ([], [])
    plt.figure(figsize=(10, 6))
    plt.bar([str(gid) for gid in game_ids], avg_sentiments, color='purple')
    plt.title('Average Sentiment Score per Game')
    plt.xlabel('Game ID')
    plt.ylabel('Average Sentiment Score')

    img3 = BytesIO()
    plt.savefig(img3, format='png')
    img3.seek(0)
    plot_url3 = base64.b64encode(img3.getvalue()).decode()
    plt.close()

    return render_template('visualization.html', plot_urls=[plot_url1, plot_url2, plot_url3])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)