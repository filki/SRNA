import re
import spacy
from typing import Dict, Any
from textblob import TextBlob

class TextAnalysisService:
    def __init__(self):
        """Initialize spaCy model"""
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            print("Warning: English language model not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            subprocess.run(["pip", "install", "textblob"])
            self.nlp = spacy.load('en_core_web_sm')

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using TextBlob."""
        if not text:
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'assessment': 'neutral',
                'polarity_percentage': 50,
                'subjectivity_percentage': 0,
                'intensity': {
                    'value': 0.0,
                    'label': 'neutral'
                }
            }

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Calculate intensity based on word modifiers and punctuation
        intensity_value = 0.0
        exclamation_count = text.count('!')
        caps_words = len(re.findall(r'\b[A-Z]{2,}+\b', text))
        intensity_modifiers = ['very', 'really', 'extremely', 'absolutely', 'completely']
        
        # Add intensity for exclamations (max 0.3)
        intensity_value += min(exclamation_count * 0.1, 0.3)
        
        # Add intensity for caps words (max 0.3)
        intensity_value += min(caps_words * 0.1, 0.3)
        
        # Add intensity for modifier words (max 0.4)
        modifier_count = sum(1 for word in intensity_modifiers if word.lower() in text.lower())
        intensity_value += min(modifier_count * 0.1, 0.4)

        # Determine intensity label
        if intensity_value < 0.3:
            intensity_label = 'mild'
        elif intensity_value < 0.6:
            intensity_label = 'moderate'
        else:
            intensity_label = 'strong'

        # Determine sentiment assessment
        if polarity > 0.1:
            assessment = 'positive'
        elif polarity < -0.1:
            assessment = 'negative'
        else:
            assessment = 'neutral'

        # Convert scores to percentages for easier visualization
        polarity_percentage = ((polarity + 1) / 2) * 100  # Convert -1 to 1 to 0-100%
        subjectivity_percentage = subjectivity * 100

        return {
            'polarity': round(polarity, 2),
            'subjectivity': round(subjectivity, 2),
            'assessment': assessment,
            'polarity_percentage': round(polarity_percentage, 1),
            'subjectivity_percentage': round(subjectivity_percentage, 1),
            'intensity': {
                'value': round(intensity_value, 2),
                'label': intensity_label,
                'percentage': round(intensity_value * 100, 1)
            }
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Perform text analysis including morphological analysis using spaCy."""
        if not text:
            return {
                'word_count': 0,
                'avg_word_length': 0,
                'sentence_count': 0,
                'avg_sentence_length': 0,
                'unique_words': 0,
                'special_chars_percent': 0,
                'caps_words_count': 0,
                'morphological_analysis': [],
                'summary_stats': {
                    'pos_counts': {},
                    'dep_counts': {},
                    'total_tokens': 0
                },
                'sentiment': {
                    'polarity': 0,
                    'subjectivity': 0,
                    'assessment': 'neutral'
                }
            }

        # Basic text analysis
        words = re.findall(r'\b\w+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count special characters
        total_chars = len(text)
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text))
        
        # Count words in ALL CAPS (excluding single letters)
        caps_words = len(re.findall(r'\b[A-Z]{2,}+\b', text))
        
        # Calculate basic metrics
        word_count = len(words)
        unique_words = len(set(words))
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        special_chars_percent = (special_chars / total_chars * 100) if total_chars > 0 else 0

        # Perform sentiment analysis
        sentiment = self.analyze_sentiment(text)

        # Perform morphological analysis using spaCy
        morphological_analysis = []
        pos_counts = {}
        dep_counts = {}
        total_tokens = 0

        try:
            doc = self.nlp(text[:5000])  # Limit text length to avoid memory issues
            for token in doc:
                if not token.is_punct and not token.is_space:
                    total_tokens += 1
                    pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
                    dep_counts[token.dep_] = dep_counts.get(token.dep_, 0) + 1
                    
                    morphological_analysis.append({
                        'text': token.text,
                        'lemma': token.lemma_,
                        'pos': self._get_pos_description(token.pos_),
                        'tag': token.tag_,
                        'dep': self._get_dep_description(token.dep_)
                    })
        except Exception as e:
            print(f"Warning: Error during morphological analysis: {e}")
            morphological_analysis = []
            pos_counts = {}
            dep_counts = {}
            total_tokens = 0

        return {
            'word_count': word_count,
            'avg_word_length': round(avg_word_length, 1),
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'unique_words': unique_words,
            'special_chars_percent': round(special_chars_percent, 1),
            'caps_words_count': caps_words,
            'morphological_analysis': morphological_analysis[:50],  # Limit to first 50 tokens
            'summary_stats': {
                'pos_counts': pos_counts,
                'dep_counts': dep_counts,
                'total_tokens': total_tokens
            },
            'sentiment': sentiment
        }

    def _get_pos_description(self, pos: str) -> str:
        """Get user-friendly description of part of speech tags."""
        pos_map = {
            'ADJ': 'Adjective',
            'ADP': 'Preposition',
            'ADV': 'Adverb',
            'AUX': 'Auxiliary',
            'CONJ': 'Conjunction',
            'CCONJ': 'Coordinating Conjunction',
            'DET': 'Determiner',
            'INTJ': 'Interjection',
            'NOUN': 'Noun',
            'NUM': 'Number',
            'PART': 'Particle',
            'PRON': 'Pronoun',
            'PROPN': 'Proper Noun',
            'PUNCT': 'Punctuation',
            'SCONJ': 'Subordinating Conjunction',
            'SYM': 'Symbol',
            'VERB': 'Verb',
            'X': 'Other'
        }
        return pos_map.get(pos, pos)

    def _get_dep_description(self, dep: str) -> str:
        """Get user-friendly description of dependency relations."""
        dep_map = {
            'nsubj': 'Subject',
            'obj': 'Object',
            'dobj': 'Direct Object',
            'iobj': 'Indirect Object',
            'det': 'Determiner',
            'prep': 'Preposition',
            'pobj': 'Object of Preposition',
            'amod': 'Adjective Modifier',
            'advmod': 'Adverb Modifier',
            'aux': 'Auxiliary',
            'ROOT': 'Root',
            'compound': 'Compound',
            'conj': 'Conjunction',
            'cc': 'Coordinating Conjunction',
            'nmod': 'Noun Modifier',
            'poss': 'Possession Modifier',
            'mark': 'Marker',
            'case': 'Case Marking',
            'punct': 'Punctuation'
        }
        return dep_map.get(dep, dep)

text_analysis_service = TextAnalysisService()
