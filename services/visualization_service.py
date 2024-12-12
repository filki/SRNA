import io
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Użyj backendu AGG
import matplotlib.pyplot as plt
from flask import Response

DATABASE = 'data/steam_reviews_with_timestamp.db'

def get_top_authors(limit=10):
    """Pobiera Top 10 autorów według liczby recenzji."""
    query = """
        SELECT author_id, COUNT(*) as review_count
        FROM reviews
        GROUP BY author_id
        ORDER BY review_count DESC
        LIMIT ?
    """
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(query, (limit,))
    results = cur.fetchall()
    con.close()
    return results

def generate_top_authors_svg():
    """Generuje wykres słupkowy w formacie SVG."""
    # Pobierz dane
    data = get_top_authors()
    authors = [str(row[0]) for row in data]
    review_counts = [row[1] for row in data]

    # Wygeneruj wykres
    plt.figure(figsize=(10, 6))
    plt.bar(authors, review_counts, color='skyblue')
    plt.title('Top 10 Autorów według liczby recenzji', fontsize=16)
    plt.xlabel('ID Autora', fontsize=12)
    plt.ylabel('Liczba recenzji', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.tight_layout()

    # Zapisz wykres jako SVG
    output = io.StringIO()
    plt.savefig(output, format='svg')
    plt.close()
    svg_data = output.getvalue()
    output.close()

    return svg_data
