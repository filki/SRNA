import io
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Użyj backendu AGG
import matplotlib.pyplot as plt
from flask import Response
from typing import Dict, List
import plotly.express as px
import plotly.graph_objects as go
from services.db_service import get_top_genres, get_top_publishers, get_top_developers

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

def create_top_genres_chart():
    data = get_top_genres()
    print("Creating genres chart with data:", data)
    fig = go.Figure(data=[
        go.Bar(
            x=[d['name'] for d in data],
            y=[d['review_count'] for d in data],
            marker_color='#66c0f4',
            hovertemplate='<b>%{x}</b><br>Liczba recenzji: %{y}<extra></extra>'
        )
    ])
    fig.update_layout(
        title={
            'text': 'Top 10 Gatunków Gier',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis_title='Gatunek',
        yaxis_title='Liczba Recenzji',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=50, r=20, t=70, b=50),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=12),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        showlegend=False
    )
    return fig.to_html(full_html=False, config={'displayModeBar': False})

def create_top_publishers_chart():
    data = get_top_publishers()
    print("Creating publishers chart with data:", data)
    fig = go.Figure(data=[
        go.Bar(
            x=[d['name'] for d in data],
            y=[d['review_count'] for d in data],
            marker_color='#1a9fff',
            hovertemplate='<b>%{x}</b><br>Liczba recenzji: %{y}<extra></extra>'
        )
    ])
    fig.update_layout(
        title={
            'text': 'Top 10 Wydawców',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis_title='Wydawca',
        yaxis_title='Liczba Recenzji',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=50, r=20, t=70, b=50),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=12),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        showlegend=False
    )
    return fig.to_html(full_html=False, config={'displayModeBar': False})

def create_top_developers_chart():
    data = get_top_developers()
    print("Creating developers chart with data:", data)
    fig = go.Figure(data=[
        go.Bar(
            x=[d['name'] for d in data],
            y=[d['review_count'] for d in data],
            marker_color='#47bfff',
            hovertemplate='<b>%{x}</b><br>Liczba recenzji: %{y}<extra></extra>'
        )
    ])
    fig.update_layout(
        title={
            'text': 'Top 10 Deweloperów',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis_title='Deweloper',
        yaxis_title='Liczba Recenzji',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=50, r=20, t=70, b=50),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=12),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True
        ),
        showlegend=False
    )
    return fig.to_html(full_html=False, config={'displayModeBar': False})
