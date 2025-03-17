import re
import json
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from collections import Counter
import string
import math
import random

# Download necessary NLTK resources on first import
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class PatentAnalyzer:
    """
    A utility class for analyzing patents and extracting SEO-relevant information.
    """
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # SEO-specific keywords to look for
        self.seo_keywords = {
            "search engine": 10,
            "algorithm": 9,
            "ranking": 9,
            "relevance": 8,
            "indexing": 8,
            "crawling": 8,
            "link": 7,
            "keyword": 7,
            "query": 7,
            "content": 6,
            "optimization": 8,
            "semantic": 8,
            "natural language": 9,
            "machine learning": 9,
            "artificial intelligence": 9,
            "user experience": 7,
            "relevance score": 8,
            "search result": 7,
            "web page": 6,
            "document": 6,
            "information retrieval": 9,
            "metadata": 7,
            "classification": 7,
            "personalization": 8,
            "recommendation": 7,
            "user behavior": 8,
            "click through": 8,
            "bounce rate": 7
        }
    
    def preprocess_text(self, text):
        """
        Preprocess text for analysis:
        - Remove punctuation
        - Convert to lowercase
        - Remove stopwords
        - Lemmatize words
        
        Args:
            text (str): The text to preprocess
            
        Returns:
            list: A list of preprocessed tokens
        """
        if not text:
            return []
        
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove punctuation and stopwords, then lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in string.punctuation and token not in self.stop_words and len(token) > 2
        ]
        
        return tokens
    
    def extract_keywords(self, text, top_n=50):
        """
        Extract the most important keywords from text.
        
        Args:
            text (str): The text to analyze
            top_n (int): Number of top keywords to return
            
        Returns:
            list: A list of (keyword, count) tuples
        """
        if not text:
            return []
        
        # Preprocess
        tokens = self.preprocess_text(text)
        
        # Count frequency
        keyword_counts = Counter(tokens)
        
        # Return top N keywords
        return keyword_counts.most_common(top_n)
    
    def extract_keyphrases(self, text, top_n=30, ngram_range=(2, 3)):
        """
        Extract the most important keyphrases from text.
        
        Args:
            text (str): The text to analyze
            top_n (int): Number of top keyphrases to return
            ngram_range (tuple): Range of n-gram sizes to consider
            
        Returns:
            list: A list of (keyphrase, count) tuples
        """
        if not text:
            return []
        
        # Tokenize without removing stopwords
        tokens = word_tokenize(text.lower())
        
        # Remove punctuation only
        tokens = [
            token for token in tokens 
            if token not in string.punctuation and len(token) > 2
        ]
        
        # Generate n-grams
        all_ngrams = []
        for n in range(ngram_range[0], ngram_range[1] + 1):
            all_ngrams.extend([' '.join(gram) for gram in ngrams(tokens, n)])
        
        # Count frequency
        phrase_counts = Counter(all_ngrams)
        
        # Return top N keyphrases
        return phrase_counts.most_common(top_n)
    
    def extract_entities(self, text, top_n=15):
        """
        Extract entities from text using simple pattern matching.
        This is a simplified approach - in a production environment,
        you might want to use a Named Entity Recognition model.
        
        Args:
            text (str): The text to analyze
            top_n (int): Number of top entities per category to return
            
        Returns:
            dict: A dictionary of entity categories and their counts
        """
        if not text:
            return {
                'organizations': [],
                'technologies': [],
                'applications': []
            }
        
        # Simple regex patterns for different entity types
        org_pattern = r'(?:[A-Z][a-z]+ )+(?:Inc|LLC|Corporation|Corp|Company|Co|Ltd)'
        tech_pattern = r'(?:algorithm|system|method|engine|model|framework|platform|technology|database|network|interface|API)'
        app_pattern = r'(?:search engine|recommender system|information retrieval|content analysis|user tracking|web crawler|indexing system)'
        
        # Find matches
        orgs = re.findall(org_pattern, text)
        techs = re.findall(tech_pattern, text, re.IGNORECASE)
        apps = re.findall(app_pattern, text, re.IGNORECASE)
        
        # Count frequencies
        org_counts = Counter(orgs)
        tech_counts = Counter([tech.lower() for tech in techs])
        app_counts = Counter([app.lower() for app in apps])
        
        return {
            'organizations': org_counts.most_common(top_n),
            'technologies': tech_counts.most_common(top_n),
            'applications': app_counts.most_common(top_n)
        }
    
    def calculate_seo_relevance(self, text):
        """
        Calculate the SEO relevance of a patent.
        
        Args:
            text (str): The patent text
            
        Returns:
            dict: SEO relevance metrics
        """
        if not text:
            return {
                'overall_relevance_score': 0,
                'seo_keywords': [],
                'relevance_by_category': {}
            }
        
        # Preprocess
        tokens = self.preprocess_text(text)
        text_lower = text.lower()
        
        # Count SEO keywords
        seo_keyword_counts = {}
        total_relevance_score = 0
        
        for keyword, weight in self.seo_keywords.items():
            count = text_lower.count(keyword)
            if count > 0:
                seo_keyword_counts[keyword] = count
                total_relevance_score += count * weight
        
        # Calculate overall relevance score (0-100)
        max_possible_score = sum(weight * 10 for weight in self.seo_keywords.values())
        overall_score = min(100, int((total_relevance_score / max_possible_score) * 100))
        
        # Categorize relevance
        categories = {
            'search_algorithms': ['algorithm', 'ranking', 'relevance', 'search engine'],
            'content_analysis': ['content', 'semantic', 'natural language', 'text'],
            'user_behavior': ['user experience', 'click through', 'bounce rate', 'behavior'],
            'technical_seo': ['crawling', 'indexing', 'metadata', 'link'],
            'ml_ai': ['machine learning', 'artificial intelligence', 'neural network', 'model']
        }
        
        relevance_by_category = {}
        
        for category, terms in categories.items():
            category_score = 0
            for term in terms:
                if term in seo_keyword_counts:
                    category_score += seo_keyword_counts[term] * self.seo_keywords.get(term, 5)
            
            # Normalize to 0-100
            max_category_score = sum(self.seo_keywords.get(term, 5) * 10 for term in terms)
            normalized_score = min(100, int((category_score / max_category_score) * 100)) if max_category_score > 0 else 0
            
            relevance_by_category[category] = normalized_score
        
        # Sort seo_keyword_counts by count
        sorted_seo_keywords = sorted(
            seo_keyword_counts.items(), 
            key=lambda x: (x[1], self.seo_keywords.get(x[0], 0)), 
            reverse=True
        )
        
        return {
            'overall_relevance_score': overall_score,
            'seo_keywords': sorted_seo_keywords,
            'relevance_by_category': relevance_by_category
        }
    
    def calculate_innovation_score(self, patent_data):
        """
        Calculate an innovation score for the patent.
        
        Args:
            patent_data (dict): Patent data
            
        Returns:
            int: Innovation score (0-100)
        """
        # This is a simplified scoring model
        # In a real application, this would be more sophisticated
        
        # Initialize with a baseline score
        score = 50
        
        # Factor 1: Length and detail of the patent
        full_text = patent_data.get('full_text', '')
        if full_text:
            text_length = len(full_text)
            # Longer patents might indicate more detailed innovation
            if text_length > 20000:
                score += 10
            elif text_length > 10000:
                score += 5
            elif text_length < 5000:
                score -= 5
        
        # Factor 2: Technical complexity (basic approximation)
        technical_terms = ['algorithm', 'system', 'method', 'apparatus', 'process', 
                          'technique', 'device', 'mechanism', 'framework', 'architecture']
        technical_count = sum(full_text.lower().count(term) for term in technical_terms)
        
        if technical_count > 100:
            score += 15
        elif technical_count > 50:
            score += 10
        elif technical_count > 25:
            score += 5
        
        # Factor 3: Presence of claims
        if 'CLAIMS:' in full_text:
            claims_section = full_text.split('CLAIMS:')[1]
            num_claims = claims_section.count('\n\n')
            
            if num_claims > 15:
                score += 10
            elif num_claims > 8:
                score += 5
        
        # Factor 4: Age of patent (newer may be more innovative)
        filing_date = patent_data.get('filing_date', '')
        if filing_date and 'filed' in filing_date.lower():
            try:
                year = int(re.search(r'\d{4}', filing_date).group())
                current_year = 2025  # Using a fixed reference point
                age = current_year - year
                
                if age < 3:
                    score += 15
                elif age < 5:
                    score += 10
                elif age < 10:
                    score += 5
                elif age > 20:
                    score -= 10
            except:
                # If year extraction fails, don't adjust the score
                pass
        
        # Ensure score is in range 0-100
        return max(0, min(100, score))
    
    def analyze_patent(self, patent_data):
        """
        Perform a comprehensive analysis of a patent.
        
        Args:
            patent_data (dict): Patent data including at least title, abstract, and full_text
            
        Returns:
            dict: Analysis results
        """
        # Get text to analyze
        title = patent_data.get('title', '')
        abstract = patent_data.get('abstract', '')
        full_text = patent_data.get('full_text', '')
        
        # Combine text for analysis
        combined_text = f"{title}\n\n{abstract}\n\n{full_text}"
        
        # Extract keywords
        keywords = self.extract_keywords(combined_text)
        
        # Extract keyphrases
        keyphrases = self.extract_keyphrases(combined_text)
        
        # Extract entities
        entities = self.extract_entities(combined_text)
        
        # Calculate SEO relevance
        seo_relevance = self.calculate_seo_relevance(combined_text)
        
        # Calculate innovation score
        innovation_score = self.calculate_innovation_score(patent_data)
        
        # Return analysis
        return {
            'keywords': keywords,
            'keyphrases': keyphrases,
            'entities': entities,
            'seo_relevance': seo_relevance,
            'innovation_score': innovation_score
        }
    
    def generate_recommendations(self, analysis):
        """
        Generate SEO recommendations based on patent analysis.
        
        Args:
            analysis (dict): Patent analysis results
            
        Returns:
            dict: SEO recommendations
        """
        seo_relevance = analysis.get('seo_relevance', {})
        overall_score = seo_relevance.get('overall_relevance_score', 0)
        category_scores = seo_relevance.get('relevance_by_category', {})
        seo_keywords = seo_relevance.get('seo_keywords', [])
        innovation_score = analysis.get('innovation_score', 0)
        
        # Initialize recommendations
        recommendations = {
            'priority_score': min(100, (overall_score + innovation_score) // 2),
            'content_strategy': [],
            'technical_seo': [],
            'competitive_analysis': []
        }
        
        # Generate content strategy recommendations
        if seo_keywords:
            top_keywords = [k for k, _ in seo_keywords[:10]]
            
            recommendations['content_strategy'].append({
                'title': 'Focus Content Around Key SEO Concepts',
                'description': 'Prioritize these patent-derived keywords in your content strategy.',
                'items': [
                    f"Create in-depth content around '{kw}'" for kw in top_keywords[:5]
                ]
            })
            
            # Technical terms for content
            technical_keywords = [k for k, _ in filter(
                lambda x: x[0] in ['algorithm', 'system', 'method', 'technique', 'framework', 'model'], 
                seo_keywords
            )]
            
            if technical_keywords:
                recommendations['content_strategy'].append({
                    'title': 'Technical Explainer Content',
                    'description': 'Create technical content explaining these concepts to establish authority.',
                    'items': [
                        f"Develop a technical guide about '{kw}'" for kw in technical_keywords[:3]
                    ]
                })
        
        # Generate technical SEO recommendations
        if 'search_algorithms' in category_scores and category_scores['search_algorithms'] > 50:
            recommendations['technical_seo'].append({
                'title': 'Schema Markup Implementation',
                'description': 'Implement structured data to help search engines understand your content.',
                'items': [
                    "Add Article schema markup to content discussing search algorithms",
                    "Use TechArticle schema for technical content",
                    "Implement HowTo schema for implementation guides"
                ]
            })
        
        if 'technical_seo' in category_scores and category_scores['technical_seo'] > 40:
            recommendations['technical_seo'].append({
                'title': 'Technical SEO Optimization',
                'description': 'Optimize technical aspects based on patent insights.',
                'items': [
                    "Ensure proper crawlability and indexing of technical content",
                    "Optimize internal linking structure to emphasize expertise in patent-related topics",
                    "Implement breadcrumb navigation for complex technical content"
                ]
            })
        
        # Generate competitive analysis recommendations
        if innovation_score > 70:
            recommendations['competitive_analysis'].append({
                'title': 'Competitive Innovation Analysis',
                'description': 'Leverage insights from this highly innovative patent.',
                'items': [
                    "Research companies implementing similar technologies",
                    "Analyze content gaps between your site and competitors using this technology",
                    "Create comparison content highlighting different approaches to this technology"
                ]
            })
        elif innovation_score > 40:
            recommendations['competitive_analysis'].append({
                'title': 'Market Differentiation Strategy',
                'description': 'Use these patent insights to differentiate your content.',
                'items': [
                    "Focus on unique aspects of this patent approach compared to competitors",
                    "Create content addressing specific problems solved by this patent",
                    "Develop case studies showcasing successful implementations of similar technologies"
                ]
            })
        
        # Return recommendations
        return recommendations
