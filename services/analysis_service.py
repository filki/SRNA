from wordcloud import WordCloud
import sqlite3
import matplotlib.pyplot as plt
import io

DATABASE = 'data/steam_reviews_with_timestamp.db'

def get_review_texts():
    """Pobiera teksty recenzji z bazy danych."""
    query = "SELECT content FROM reviews"
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(query)
    results = cur.fetchall()
    con.close()
    return [row[0] for row in results if row[0]]  # Usuń puste recenzje

def generate_wordcloud():
    """Generuje chmurę słów z treści recenzji."""
    # Pobierz teksty recenzji
    texts = get_review_texts()
    combined_text = " ".join(texts)

    # Wygeneruj chmurę słów
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        colormap='Blues',
        max_words=100
    ).generate(combined_text)

    # Zapisz chmurę słów jako obraz w pamięci
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    return img
