import re
import spacy
from typing import Dict, Any
from textblob import TextBlob
from collections import Counter

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

    def extract_named_entities(self, text: str) -> Dict[str, list]:
        """
        Extract named entities from text using spaCy.
        Returns a dictionary with entity types as keys and lists of entities as values.
        """
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            # Convert spaCy labels to more readable names
            label = {
                'PERSON': 'Osoby',
                'ORG': 'Organizacje',
                'GPE': 'Lokalizacje',
                'PRODUCT': 'Produkty',
                'DATE': 'Daty',
                'MONEY': 'Kwoty',
                'GAME': 'Gry',
                'DEVELOPER': 'Deweloperzy'
            }.get(ent.label_, ent.label_)
            
            if label not in entities:
                entities[label] = []
            
            # Add entity text and its position
            entities[label].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'sentence': ent.sent.text.strip()
            })
        
        # Add gaming-specific entity extraction
        game_patterns = [
            r'(?i)\b(steam|valve|epic games|gog|origin)\b',  # Gaming platforms
            r'(?i)\b(dlc|expansion|patch|update)\b',         # Gaming terms
            r'(?i)\b(fps|rpg|mmo|rts|moba)\b',              # Game genres
            r'\$\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\$',         # Price patterns
            r'v\d+\.\d+(?:\.\d+)?'                          # Version numbers
        ]
        
        # Add custom gaming entities
        for pattern in game_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                label = 'GAMING_TERM'
                if label not in entities:
                    entities[label] = []
                entities[label].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'sentence': text[max(0, match.start()-50):min(len(text), match.end()+50)].strip()
                })
        
        return entities

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive text analysis including NER"""
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
                'named_entities': {},
                'sentiment': {
                    'polarity': 0,
                    'subjectivity': 0,
                    'assessment': 'neutral'
                }
            }

        doc = self.nlp(text)
        
        # Basic statistics
        words = [token.text for token in doc if not token.is_punct and not token.is_space]
        sentences = list(doc.sents)
        
        analysis = {
            'word_count': len(words),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words)),
            'special_chars_percent': len([c for c in text if not c.isalnum() and not c.isspace()]) / len(text) * 100 if text else 0,
            'caps_words_count': len([w for w in words if w.isupper()]),
            'morphological_analysis': [
                {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'dep': token.dep_
                }
                for token in doc
            ],
            'summary_stats': {
                'pos_counts': dict(Counter(token.pos_ for token in doc)),
                'dep_counts': dict(Counter(token.dep_ for token in doc)),
                'total_tokens': len(doc)
            }
        }
        
        # Add NER analysis
        analysis['named_entities'] = self.extract_named_entities(text)
        
        # Add sentiment analysis
        analysis['sentiment'] = self.analyze_sentiment(text)
        
        return analysis

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
