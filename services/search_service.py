from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Any, Set
from gensim.models import Word2Vec
from gensim.utils import simple_preprocess

class SearchService:
    def __init__(self):
        """Initialize the search service with TF-IDF vectorizer and Word2Vec model"""
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=10000,
            sublinear_tf=True
        )
        self.word2vec_model = None
        self.review_vectors = {}
        
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
        Returns value in [0,1] range
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
            
        return float(intersection / union)  # Already in [0,1] range

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
        
        # Similarities are already in [0,1] range from cosine_similarity
        similarities = cosine_similarities.flatten()
        
        # Update review scores
        for review, score in zip(reviews, similarities):
            review['relevance'] = float(score)
            
        return reviews

    def calculate_cosine_similarity(self, query: str, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate pure cosine similarity using TF-IDF"""
        if not reviews:
            return []

        # Prepare texts
        review_texts = [self.preprocess_text(review['content']) for review in reviews]
        query_text = self.preprocess_text(query)
        
        # Add query to the end of texts for vectorization
        all_texts = review_texts + [query_text]
        
        # Calculate TF-IDF
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(tfidf_matrix[:-1], tfidf_matrix[-1:])
        
        # Similarities are already in [0,1] range from cosine_similarity
        similarities = cosine_similarities.flatten()
        
        # Update review scores
        for review, score in zip(reviews, similarities):
            review['relevance'] = float(score)
            
        return reviews

    def train_word2vec(self, reviews: List[Dict[str, Any]]):
        """Train Word2Vec model on review texts"""
        # Preprocess and tokenize reviews
        tokenized_reviews = [simple_preprocess(review['content']) for review in reviews if review['content']]
        
        # Train Word2Vec model
        self.word2vec_model = Word2Vec(
            sentences=tokenized_reviews,
            vector_size=100,
            window=5,
            min_count=1,
            workers=4
        )
        
        # Create review vectors
        for review in reviews:
            if review['content']:
                tokens = simple_preprocess(review['content'])
                if tokens:
                    vector = np.mean([self.word2vec_model.wv[word] 
                                    for word in tokens 
                                    if word in self.word2vec_model.wv], axis=0)
                    self.review_vectors[review['id']] = vector

    def calculate_word2vec_similarity(self, query: str, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate similarity using Word2Vec embeddings"""
        if not self.word2vec_model:
            self.train_word2vec(reviews)
            
        query_tokens = simple_preprocess(query)
        if not query_tokens:
            return reviews
            
        # Calculate query vector
        query_vector = np.mean([self.word2vec_model.wv[word] 
                              for word in query_tokens 
                              if word in self.word2vec_model.wv], axis=0)
        
        # Calculate similarities
        for review in reviews:
            if review['id'] in self.review_vectors:
                review_vector = self.review_vectors[review['id']]
                # cosine_similarity returns value in [-1,1], normalize to [0,1]
                similarity = cosine_similarity([query_vector], [review_vector])[0][0]
                review['relevance'] = float((similarity + 1) / 2)  # normalize to [0,1]
            else:
                review['relevance'] = 0.0
                
        return reviews

    def search_reviews(self, query: str, reviews: List[Dict[str, Any]], scoring_method: str = 'tfidf') -> List[Dict[str, Any]]:
        """
        Search and rank reviews based on selected scoring method.
        scoring_method: 'tfidf', 'jaccard', 'cosine', or 'word2vec'
        """
        if not reviews or not query:
            return reviews

        if scoring_method == 'jaccard':
            for review in reviews:
                score = self.calculate_jaccard_similarity(query, review['content'])
                review['relevance'] = score
                review['scoring_method'] = 'jaccard'
        elif scoring_method == 'cosine':
            reviews = self.calculate_cosine_similarity(query, reviews)
            for review in reviews:
                review['scoring_method'] = 'cosine'
        elif scoring_method == 'word2vec':
            reviews = self.calculate_word2vec_similarity(query, reviews)
            for review in reviews:
                review['scoring_method'] = 'word2vec'
        else:  # default to tfidf
            reviews = self.calculate_tfidf_similarity(query, reviews)
            for review in reviews:
                review['scoring_method'] = 'tfidf'

        # Sort by relevance score in descending order
        return sorted(reviews, key=lambda x: x['relevance'], reverse=True)

search_service = SearchService()
