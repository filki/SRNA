from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Any
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class SearchService:
    def __init__(self):
        # Configure vectorizer to better handle specific terms like "cs2"
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            stop_words='english',
            token_pattern=r'(?u)\b\w+\b',  
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 3),  
            max_features=10000,
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=True  
        )
        self.review_vectors = None
        self.review_texts = None

    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better matching."""
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Normalize spaces and remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def calculate_relevance_scores(self, query: str, reviews: List[Dict[str, Any]]) -> List[float]:
        """Calculate relevance scores for reviews based on the query."""
        if not query.strip() or not reviews:
            return [0.0] * len(reviews)

        try:
            # Preprocess texts
            review_texts = [self.preprocess_text(review.get('content', '')) for review in reviews]
            processed_query = self.preprocess_text(query)

            # Create document corpus with query at the end
            all_texts = review_texts + [processed_query]

            # Fit and transform all texts including query
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Get query vector (last document) and review vectors
            query_vector = tfidf_matrix[-1]
            review_vectors = tfidf_matrix[:-1]

            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, review_vectors).flatten()

            # Calculate context bonus based on term frequency
            term_freq_bonus = np.zeros(len(reviews))
            query_terms = set(processed_query.split())
            
            for idx, text in enumerate(review_texts):
                text_terms = set(text.split())
                # Calculate term overlap ratio
                overlap = len(query_terms & text_terms) / len(query_terms)
                term_freq_bonus[idx] = overlap * 0.3  # 30% bonus for term frequency

            # Combine base similarity with term frequency bonus
            combined_scores = similarities + term_freq_bonus

            # Normalize to 0-100 scale
            max_score = combined_scores.max()
            if max_score > 0:
                scores = (combined_scores / max_score) * 100
            else:
                scores = combined_scores * 0

            # Apply logarithmic scaling to make differences more pronounced
            scores = np.log1p(scores) * 20  # Scale factor to keep scores in reasonable range
            
            # Clip scores to 0-100 range and round
            scores = np.clip(scores, 0, 100)
            scores = [round(float(score), 2) for score in scores]

            return scores

        except Exception as e:
            print(f"Error in calculate_relevance_scores: {str(e)}")
            import traceback
            traceback.print_exc()
            return [0.0] * len(reviews)

    def search_reviews(self, query: str, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search reviews and return them with relevance scores."""
        if not query.strip():
            return reviews

        try:
            # Calculate relevance scores
            scores = self.calculate_relevance_scores(query, reviews)

            # Add scores to reviews
            for review, score in zip(reviews, scores):
                review['relevance'] = score

            # Sort by relevancy score (highest first)
            sorted_reviews = sorted(reviews, key=lambda x: x.get('relevance', 0.0), reverse=True)

            return sorted_reviews

        except Exception as e:
            print(f"Error in search_reviews: {str(e)}")
            import traceback
            traceback.print_exc()
            return reviews

# Create a singleton instance
search_service = SearchService()
