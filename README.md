# Steam Review Analysis System

A comprehensive web application for analyzing Steam game reviews, built with Flask and modern data analysis tools.

## Features

- **Advanced Search Functionality**
  - Full-text search with TF-IDF and Jaccard similarity
  - Multiple filter options (date range, playtime, sentiment, etc.)
  - Persistent filter states
  - Game-specific filtering

- **Data Analysis**
  - Sentiment analysis of reviews
  - Text clustering using K-means
  - Word cloud generation
  - Various statistical visualizations

- **Visualizations**
  - Interactive charts using Plotly
  - Word clouds
  - Top authors, genres, publishers, and developers charts

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd steam-review-analysis
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download required NLTK data and spaCy model:
```bash
python -m spacy download en_core_web_sm
```

5. Initialize the database:
```bash
python init_db.py  # If provided
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open a web browser and navigate to:
```
http://localhost:5000
```

## Database Schema

The application uses SQLite with the following main tables:

- **reviews**: Stores review data including content, ratings, and metadata
- **authors**: Contains information about review authors
- **games**: Stores game-related information

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
