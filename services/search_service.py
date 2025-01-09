from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Any, Set

class SearchService:
    def __init__(self):
        """Initialize the search service with TF-IDF vectorizer"""
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=10000,
            sublinear_tf=True
        )

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for similarity calculation"""
        if not text:
            return ""
        # Convert to lowercase and normalize spaces
        return " ".join(text.lower().split())

    def calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.
        Jaccard = (A ∩ B) / (A ∪ B) where A and B are sets of words
        """
        # Preprocess texts
        text1 = self.preprocess_text(text1)
        text2 = self.preprocess_text(text2)
        
        # Convert to word sets
        set1: Set[str] = set(text1.split())
        set2: Set[str] = set(text2.split())
        
        # Calculate intersection and union
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        # Avoid division by zero
        if union == 0:
            return 0.0
            
        return (intersection / union) * 100  # Convert to percentage

    def calculate_tfidf_similarity(self, query: str, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate TF-IDF based similarity scores"""
        if not reviews:
            return []

        # Prepare texts
        review_texts = [self.preprocess_text(review['content']) for review in reviews]
        query_text = self.preprocess_text(query)
        
        # Add query to the end of texts for vectorization
        all_texts = review_texts + [query_text]
        
        # Calculate TF-IDF and cosine similarity
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
        cosine_similarities = cosine_similarity(tfidf_matrix[:-1], tfidf_matrix[-1:])
        
        # Convert similarities to percentages
        similarities = (cosine_similarities * 100).flatten()
        
        # Update review scores
        for review, score in zip(reviews, similarities):
            review['relevance'] = float(score)
            
        return reviews

    def search_reviews(self, query: str, reviews: List[Dict[str, Any]], scoring_method: str = 'tfidf') -> List[Dict[str, Any]]:
        """
        Search and rank reviews based on selected scoring method.
        scoring_method: 'tfidf' or 'jaccard'
        """
        if not reviews or not query:
            return reviews

        if scoring_method == 'jaccard':
            # Calculate Jaccard similarity for each review
            for review in reviews:
                score = self.calculate_jaccard_similarity(query, review['content'])
                review['relevance'] = score
                review['scoring_method'] = 'jaccard'
        else:  # default to tfidf
            reviews = self.calculate_tfidf_similarity(query, reviews)
            for review in reviews:
                review['scoring_method'] = 'tfidf'

        # Sort by relevance score in descending order
        return sorted(reviews, key=lambda x: x['relevance'], reverse=True)

search_service = SearchService()
