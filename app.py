from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///steam_reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class SteamReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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

    def __repr__(self):
        return f"<SteamReview {self.author_steamid}>"

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

        # Save reviews to database
        save_reviews_to_db(reviews)

        # Stay on index.html and show success message
        return render_template('index.html', success_message="Reviews have been successfully fetched and stored.")
    return render_template('index.html')

@app.route('/results')
def results():
    voted_up = request.args.get('voted_up')  # e.g., "True" or "False"
    min_playtime = request.args.get('min_playtime', type=int)
    max_playtime = request.args.get('max_playtime', type=int)

    query = SteamReview.query
    if voted_up:
        query = query.filter_by(voted_up=(voted_up == "True"))
    if min_playtime and max_playtime:
        query = query.filter(SteamReview.playtime_forever.between(min_playtime, max_playtime))

    reviews = query.all()
    return render_template('results.html', reviews=reviews)



def fetch_reviews(app_id, review_type, total_reviews=50):
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

def save_reviews_to_db(reviews):
    db.session.bulk_insert_mappings(SteamReview, [
        {
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
            'comments_count': review.get('comment_count', 0)
        }
        for review in reviews
    ])
    db.session.commit()

@app.route('/delete_reviews', methods=['POST'])
def delete_reviews():
    db.session.query(SteamReview).delete()
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)