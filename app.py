from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/visualizations')
def visualizations():
    return render_template('visualizations.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

if __name__ == "__main__":
    app.run(debug=True)
