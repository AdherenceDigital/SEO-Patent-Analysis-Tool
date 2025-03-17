#!/usr/bin/env python3
"""
Patent Search Module for SEO Patent Analysis Tool
Uses the Google Patents API to search for patents
"""

import os
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime

# Import libraries for text analysis
import nltk
from nltk.corpus import wordnet
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Base URL for Google Patents API
GOOGLE_PATENTS_API_URL = "https://patents.google.com/api/search"

def clean_html(text):
    """Clean HTML tags from text"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def expand_keywords(keywords):
    """Expand keywords with synonyms for better search results"""
    expanded = set(keywords.split())
    
    for word in keywords.split():
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                expanded.add(lemma.name().replace('_', ' '))
    
    # Limit to top 10 synonyms to avoid over-expansion
    return ' OR '.join(list(expanded)[:10])

def search_patents(query, num_results=10):
    """
    Search for patents using the Google Patents API
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return
        
    Returns:
        list: List of patent results
    """
    # Expand query with synonyms
    expanded_query = expand_keywords(query)
    
    # Format request parameters
    params = {
        'q': expanded_query,
        'num': num_results,
        'format': 'json',
        'sort': 'new'
    }
    
    url = f"{GOOGLE_PATENTS_API_URL}?{urllib.parse.urlencode(params)}"
    
    # For demonstration, we'll simulate the API response
    # In a real implementation, you would make the actual API request
    
    # Simulated API response
    results = []
    
    # Generate fake search results based on the query
    for i in range(min(num_results, 20)):
        # Create a fake Google patent ID
        patent_id = f"US{10000000 + i * 123456}B2"
        
        # Use query words in the title
        query_words = query.split()
        title_words = []
        for j in range(min(3, len(query_words))):
            title_words.append(query_words[j])
        
        title = f"Method and system for {' '.join(title_words)} in search engine optimization"
        
        # Generate a fake abstract
        abstract = f"A method and system for improving search engine optimization through {query}. " \
                  f"The invention relates to techniques for analyzing and optimizing website content " \
                  f"based on search engine algorithms and patent analysis."
        
        # Generate random dates
        filing_date = datetime(2010 + i % 10, 1 + i % 12, 1 + i % 28).strftime("%Y-%m-%d")
        issue_date = datetime(2015 + i % 10, 1 + i % 12, 1 + i % 28).strftime("%Y-%m-%d")
        
        # Assignee based on query (simulate major tech companies)
        assignees = ["Google LLC", "Microsoft Technology Licensing, LLC", "Amazon Technologies, Inc.", 
                    "Facebook, Inc.", "Apple Inc."]
        assignee = assignees[i % len(assignees)]
        
        # Inventors (fake names)
        first_names = ["John", "Jane", "Robert", "Mary", "David", "Jennifer", "Michael", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
        
        num_inventors = 1 + i % 3
        inventors = []
        for j in range(num_inventors):
            inventors.append(f"{first_names[(i+j) % len(first_names)]} {last_names[(i+j) % len(last_names)]}")
        
        # Create result object
        result = {
            "patent_id": patent_id,
            "title": title,
            "abstract": abstract,
            "filing_date": filing_date,
            "issue_date": issue_date,
            "assignee": assignee,
            "inventors": ", ".join(inventors),
            "category": "Search Ranking" if i % 2 == 0 else "Content Analysis",
            "relevance_score": 100 - (i * 5),
            "url": f"https://patents.google.com/patent/{patent_id}/en"
        }
        
        results.append(result)
    
    return results

def get_patent_details(patent_id):
    """
    Get detailed information for a specific patent
    
    Args:
        patent_id (str): Patent ID
        
    Returns:
        dict: Patent details
    """
    # In a real implementation, you would make an API request to Google Patents
    # For demonstration, we'll simulate the API response
    
    # Extract patent number from ID
    patent_number = re.search(r'US(\d+)', patent_id)
    if not patent_number:
        return None
    
    patent_number = int(patent_number.group(1))
    i = patent_number % 10
    
    # Generate fake patent details
    technologies = ["search engine", "website optimization", "content analysis", 
                   "backlink analysis", "semantic search", "mobile optimization"]
    
    title = f"Method and system for {technologies[i % len(technologies)]}"
    
    abstract = f"A method and system for improving search engine optimization through {technologies[i % len(technologies)]}. " \
              f"The invention relates to techniques for analyzing and optimizing website content " \
              f"based on search engine algorithms and patent analysis."
    
    # Generate random dates
    filing_date = datetime(2010 + i % 10, 1 + i % 12, 1 + i % 28).strftime("%Y-%m-%d")
    issue_date = datetime(2015 + i % 10, 1 + i % 12, 1 + i % 28).strftime("%Y-%m-%d")
    
    # Assignee based on patent number
    assignees = ["Google LLC", "Microsoft Technology Licensing, LLC", "Amazon Technologies, Inc.", 
                "Facebook, Inc.", "Apple Inc."]
    assignee = assignees[i % len(assignees)]
    
    # Inventors (fake names)
    first_names = ["John", "Jane", "Robert", "Mary", "David", "Jennifer", "Michael", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
    
    num_inventors = 1 + i % 3
    inventors = []
    for j in range(num_inventors):
        inventors.append(f"{first_names[(i+j) % len(first_names)]} {last_names[(i+j) % len(last_names)]}")
    
    # Generate a longer description for full text
    paragraphs = [
        f"The present invention relates to methods and systems for {technologies[i % len(technologies)]} in the field of search engine optimization.",
        f"With the increasing importance of search engine rankings for website visibility, there is a need for improved techniques for {technologies[(i+1) % len(technologies)]}.",
        f"Prior approaches have failed to adequately address the challenges of {technologies[(i+2) % len(technologies)]} in a way that accommodates the latest search engine algorithms.",
        f"This invention provides a novel approach to {technologies[i % len(technologies)]} by utilizing advanced machine learning and data analysis techniques.",
        f"One aspect of the invention involves analyzing user behavior patterns to determine optimal {technologies[(i+3) % len(technologies)]} strategies.",
        f"Another aspect involves implementing automated systems for {technologies[(i+4) % len(technologies)]} based on patent-derived insights.",
        f"The system can be integrated with existing website analytics platforms to provide comprehensive {technologies[i % len(technologies)]} solutions."
    ]
    
    full_text = "\n\n".join(paragraphs)
    
    # Create result object
    result = {
        "patent_id": patent_id,
        "title": title,
        "abstract": abstract,
        "filing_date": filing_date,
        "issue_date": issue_date,
        "assignee": assignee,
        "inventors": ", ".join(inventors),
        "category": "Search Ranking" if i % 2 == 0 else "Content Analysis",
        "full_text": full_text,
        "claims": generate_claims(technologies[i % len(technologies)]),
        "url": f"https://patents.google.com/patent/{patent_id}/en"
    }
    
    return result

def generate_claims(technology):
    """Generate fake patent claims for a given technology"""
    claims = [
        f"A method for improving search engine optimization, comprising: analyzing a website's content in relation to {technology}; and generating recommendations based on the analysis.",
        f"The method of claim 1, wherein analyzing the website's content comprises identifying key factors related to {technology} that impact search engine rankings.",
        f"The method of claim 1, further comprising implementing the recommendations to improve the website's performance in search engine results.",
        f"A system for {technology} analysis, comprising: a processor; and a memory storing instructions that, when executed by the processor, cause the system to perform the method of claim 1.",
        f"A non-transitory computer-readable medium storing instructions that, when executed by a processor, cause the processor to perform a method for {technology} optimization in search engines."
    ]
    
    return claims

def analyze_patent_seo_impact(patent_details):
    """
    Analyze the SEO impact of a patent
    
    Args:
        patent_details (dict): Patent details
        
    Returns:
        dict: Analysis results
    """
    # In a real implementation, you would perform actual analysis
    # For demonstration, we'll simulate the analysis
    
    # Extract key information from the patent
    title = patent_details.get('title', '')
    abstract = patent_details.get('abstract', '')
    full_text = patent_details.get('full_text', '')
    
    # Combine text for analysis
    combined_text = f"{title} {abstract} {full_text}"
    
    # Simple keyword extraction (in a real app, use better NLP)
    keywords = {}
    for word in combined_text.lower().split():
        # Clean the word
        word = re.sub(r'[^\w\s]', '', word)
        if word and len(word) > 3:
            keywords[word] = keywords.get(word, 0) + 1
    
    # Get top keywords
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Simulate analysis results
    analysis = {
        "seo_impact": "High" if "ranking" in combined_text.lower() else "Medium",
        "innovation_score": 75 + (len(abstract) % 20),
        "keywords": [k for k, v in top_keywords],
        "keyphrases": extract_keyphrases(combined_text),
        "recommendations": generate_recommendations(combined_text),
        "insight_summary": f"This patent focuses on {top_keywords[0][0]} and {top_keywords[1][0]}, suggesting these are important factors in search engine algorithms."
    }
    
    return analysis

def extract_keyphrases(text):
    """Extract key phrases from text"""
    # In a real app, use better NLP techniques
    # This is a simple simulation
    phrases = [
        "search quality",
        "page ranking",
        "site authority",
        "content relevance",
        "user experience",
        "mobile friendliness",
        "page speed",
        "backlink profile"
    ]
    
    # Choose a subset based on the text
    selected_phrases = []
    for phrase in phrases:
        if phrase.split()[0] in text.lower() or phrase.split()[-1] in text.lower():
            selected_phrases.append(phrase)
    
    # Return at least 3 phrases
    if len(selected_phrases) < 3:
        selected_phrases.extend(phrases[:3 - len(selected_phrases)])
    
    return selected_phrases[:5]

def generate_recommendations(text):
    """Generate SEO recommendations based on patent text"""
    recommendations = [
        "Focus on comprehensive content that demonstrates E-A-T",
        "Create content that fully addresses user intent",
        "Improve technical SEO aspects mentioned in the patent",
        "Optimize internal linking structure",
        "Focus on building high-quality backlinks",
        "Improve page loading speed",
        "Enhance mobile user experience",
        "Create more in-depth content around key topics"
    ]
    
    # Choose a subset based on the text
    selected_recommendations = []
    for rec in recommendations:
        words = rec.lower().split()
        if any(word in text.lower() for word in words if len(word) > 3):
            selected_recommendations.append(rec)
    
    # Return at least 3 recommendations
    if len(selected_recommendations) < 3:
        selected_recommendations.extend(recommendations[:3 - len(selected_recommendations)])
    
    return selected_recommendations[:5]

# For testing purposes
if __name__ == "__main__":
    # Test the patent search
    results = search_patents("site quality score", 5)
    print(json.dumps(results, indent=2))
    
    # Test getting patent details
    details = get_patent_details("US10699311B2")
    print(json.dumps(details, indent=2))
