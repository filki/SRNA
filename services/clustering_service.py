from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter
import numpy as np
from typing import List, Dict, Any
import sqlite3
from .search_service import search_service

class ClusteringService:
    def __init__(self, n_clusters: int = 5):
        """Initialize clustering service with specified number of clusters"""
        self.n_clusters = n_clusters
        self.vectorizer = search_service.tfidf_vectorizer  # Reuse vectorizer from search service
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.vectors = None
        self.cluster_assignments = None
        self.reviews_data = None
        
    def get_reviews_from_db(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch reviews from database"""
        conn = sqlite3.connect('data/steam_reviews_with_authors.db')
        cursor = conn.cursor()
        
        # First, let's check the table structure
        cursor.execute("PRAGMA table_info(games)")
        columns = cursor.fetchall()
        print("Games table columns:", columns)
        
        query = """
            SELECT r.content, r.id as review_id, g.name as game_title, g.genre
            FROM reviews r
            JOIN games g ON r.app_id = g.app_id
            WHERE r.content IS NOT NULL
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'content': row[0],
                'review_id': row[1],
                'game_title': row[2],
                'genre': row[3]
            }
            for row in rows
        ]

    def perform_clustering(self, limit: int = 1000):
        """Perform clustering on reviews"""
        # Get reviews
        self.reviews_data = self.get_reviews_from_db(limit)
        texts = [review['content'] for review in self.reviews_data]
        
        # Vectorize texts
        self.vectors = self.vectorizer.fit_transform(texts)
        
        # Perform clustering
        self.cluster_assignments = self.kmeans.fit_predict(self.vectors)
        
        # Add cluster assignments to reviews data
        for i, review in enumerate(self.reviews_data):
            review['cluster'] = int(self.cluster_assignments[i])

    def get_cluster_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for each cluster"""
        if self.vectors is None or self.cluster_assignments is None:
            return []

        stats = []
        feature_names = self.vectorizer.get_feature_names_out()
        
        for i in range(self.n_clusters):
            # Get cluster center
            cluster_center = self.kmeans.cluster_centers_[i]
            
            # Get top terms
            top_term_indices = cluster_center.argsort()[-10:][::-1]
            top_terms = [feature_names[idx] for idx in top_term_indices]
            
            # Get sample reviews
            cluster_reviews = [r for r in self.reviews_data if r['cluster'] == i]
            sample_reviews = cluster_reviews[:3]  # Get 3 sample reviews
            
            # Get genres distribution
            genre_counter = Counter(r['genre'] for r in cluster_reviews)
            top_genres = dict(genre_counter.most_common(3))
            
            stats.append({
                'cluster_id': i,
                'size': len(cluster_reviews),
                'top_terms': top_terms,
                'sample_reviews': sample_reviews,
                'top_genres': top_genres
            })
        
        return stats

clustering_service = ClusteringService()
