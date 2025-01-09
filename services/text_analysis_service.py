import re
from typing import Dict, Any

class TextAnalysisService:
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        """Perform basic text analysis without external NLP libraries."""
        if not text:
            return {
                'word_count': 0,
                'avg_word_length': 0,
                'sentence_count': 0,
                'avg_sentence_length': 0,
                'unique_words': 0,
                'special_chars_percent': 0,
                'caps_words_count': 0
            }

        # Clean text and get words
        words = re.findall(r'\b\w+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count special characters
        total_chars = len(text)
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text))
        
        # Count words in ALL CAPS (excluding single letters)
        caps_words = len(re.findall(r'\b[A-Z]{2,}+\b', text))
        
        # Calculate metrics
        word_count = len(words)
        unique_words = len(set(words))
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        special_chars_percent = (special_chars / total_chars * 100) if total_chars > 0 else 0

        return {
            'word_count': word_count,
            'avg_word_length': round(avg_word_length, 1),
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'unique_words': unique_words,
            'special_chars_percent': round(special_chars_percent, 1),
            'caps_words_count': caps_words
        }

text_analysis_service = TextAnalysisService()
