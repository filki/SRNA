from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['user_input']
    # Możesz dodać dowolne operacje na danych tutaj
    return render_template('results.html', data=user_input)

if __name__ == '__main__':
    app.run(debug=True)
