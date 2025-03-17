#!/usr/bin/env python3
import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
import time
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import save_patent

# Patent categories
CATEGORIES = {
    'Core Ranking Algorithm Patents': [
        'PageRank and Link Analysis',
        'Machine Learning for Ranking',
        'Content Relevance and Quality'
    ],
    'Site Architecture Optimization': [
        'Website Structure',
        'Crawling and Indexing'
    ],
    'Mobile Optimization': [
        'Responsive Design',
        'Mobile User Experience'
    ],
    'Entity Recognition & Semantic Search': [
        'Knowledge Graph Implementation',
        'Natural Language Processing'
    ],
    'User Experience & Intent Matching': [
        'User Behavior Analysis',
        'Intent Recognition'
    ],
    'Technical SEO Factors': [
        'Performance Optimization',
        'Core Web Vitals'
    ],
    'Local & Voice Search': [
        'Local Search Optimization',
        'Voice Search'
    ],
    'Social Signals & Author Authority': [
        'Social Influence',
        'Author Authority'
    ]
}

def extract_patent_id(patent_string):
    """Extract patent ID from a patent string."""
    # For patterns like US6285999B1
    match = re.search(r'(US\d+[A-Z]\d+)', patent_string)
    if match:
        return match.group(1)
    
    # For patterns like US9165040
    match = re.search(r'(US\d+)', patent_string)
    if match:
        return match.group(1)
    
    # If no ID found, return None
    return None

def extract_patent_title(patent_string):
    """Extract patent title from a patent string."""
    # Look for title in quotes
    match = re.search(r'"([^"]+)"', patent_string)
    if match:
        return match.group(1)
    
    # If no title found, return empty string
    return ""

def fetch_patent_data(patent_id):
    """Fetch detailed patent data from Google Patents."""
    print(f"Fetching data for patent {patent_id}...")
    
    # Add a delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    url = f"https://patents.google.com/patent/{patent_id}/en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch patent {patent_id}. Status code: {response.status_code}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract patent information
        title_elem = soup.select_one('h1.heading')
        title = title_elem.text.strip() if title_elem else ""
        
        # Extract abstract
        abstract_elem = soup.select_one('div.abstract')
        abstract = abstract_elem.text.strip() if abstract_elem else ""
        
        # Extract filing and issue dates
        filing_date = ""
        issue_date = ""
        date_elements = soup.select('time')
        for elem in date_elements:
            if 'itemprop' in elem.attrs:
                if elem['itemprop'] == 'publicationDate':
                    issue_date = elem.text.strip()
                elif elem['itemprop'] == 'filingDate':
                    filing_date = elem.text.strip()
        
        # Extract inventors
        inventors_elems = soup.select('dd[itemprop="inventor"] span[itemprop="name"]')
        inventors = ", ".join([inv.text.strip() for inv in inventors_elems]) if inventors_elems else ""
        
        # Extract assignee - improved to better target "Current Assignee" information
        assignee = ""
        # Try first with the specific itemprop
        assignee_elem = soup.select_one('dd[itemprop="assigneeSearch"] span')
        if assignee_elem:
            assignee = assignee_elem.text.strip()
        else:
            # Backup method: look for text labels
            assignee_labels = soup.find_all('dt', string=lambda x: x and 'Current Assignee' in x)
            if assignee_labels and len(assignee_labels) > 0:
                # Get the next dd element after the "Current Assignee" label
                assignee_elem = assignee_labels[0].find_next('dd')
                if assignee_elem:
                    assignee = assignee_elem.text.strip()
        
        # Extract full text (claims and description)
        claims_elem = soup.select_one('section[itemprop="claims"]')
        claims = claims_elem.text.strip() if claims_elem else ""
        
        description_elem = soup.select_one('section[itemprop="description"]')
        description = description_elem.text.strip() if description_elem else ""
        
        full_text = f"CLAIMS:\n{claims}\n\nDESCRIPTION:\n{description}" if claims or description else ""
        
        return {
            'patent_id': patent_id,
            'title': title,
            'abstract': abstract,
            'filing_date': filing_date,
            'issue_date': issue_date,
            'inventors': inventors,
            'assignee': assignee,
            'full_text': full_text
        }
    
    except Exception as e:
        print(f"Error fetching patent {patent_id}: {str(e)}")
        return None

def process_patents(patents_list):
    """Process a list of patents and save to database."""
    # Extract all patent IDs from the list
    all_patents = []
    current_category = ""
    current_subcategory = ""
    
    lines = patents_list.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a category header (numbered)
        category_match = re.match(r'^\d+\.\s+(.*?)$', line)
        if category_match:
            current_category = category_match.group(1).strip()
            continue
        
        # Check if this is a subcategory
        if current_category and not line.startswith('US'):
            current_subcategory = line.strip()
            continue
        
        # Extract patent ID and title
        patent_id = extract_patent_id(line)
        if patent_id:
            title = extract_patent_title(line)
            combined_category = f"{current_category}/{current_subcategory}" if current_category and current_subcategory else ""
            
            all_patents.append({
                'id': patent_id,
                'title': title,
                'category': combined_category
            })
    
    # Process each patent
    for patent in all_patents:
        patent_id = patent['id']
        
        # Fetch detailed patent data
        data = fetch_patent_data(patent_id)
        
        # If we couldn't fetch the data, create a minimal record
        if not data:
            save_patent(
                patent_id=patent_id,
                title=patent['title'],
                abstract="",
                filing_date="",
                issue_date="",
                inventors="",
                assignee="",
                category=patent['category'],
                full_text=""
            )
            print(f"Saved minimal record for patent {patent_id}")
        else:
            # Save the patent to the database
            save_patent(
                patent_id=data['patent_id'],
                title=data['title'] or patent['title'],
                abstract=data['abstract'],
                filing_date=data['filing_date'],
                issue_date=data['issue_date'],
                inventors=data['inventors'],
                assignee=data['assignee'],
                category=patent['category'],
                full_text=data['full_text']
            )
            print(f"Saved patent {patent_id} to database")
        
        # Add a delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))

def main():
    """Main function."""
    # Patent list from the provided prompt
    patents_list = """
1. Core Ranking Algorithm Patents
PageRank and Link Analysis

US6285999B1: "Method for node ranking in a linked database" (Original PageRank patent)
US9165040B1: "Producing a ranking for pages using distances in a web-link graph"
US8682892B1: "Biasing search results for site links"
US7716225B1: "Ranking documents based on user behavior and/or feature data"
US8244722B1: "Ranking documents"
US8661029B1: "Modifying search result ranking based on implicit user feedback"

Machine Learning for Ranking

US9697248B2: "Semantic search system" (Related to RankBrain)
US10152552B2: "Targeted synonym generation for content retrieval"
US9514748B2: "Natural language speech recognition utilizing word vector" (BERT-related)
US9501570B2: "Generating and processing search engine analytics data"
US8762373B1: "Personalized search result ranking"
US8180782B2: "Systems and methods for ranking documents"

Content Relevance and Quality

US9031929B1: "Site quality score"
US8195650B2: "Method and system for determining similar documents"
US9002867B1: "Modifying ranking of search results based on facial expressions"
US9659097B1: "Propagating query classifications"
US8352465B1: "Grouping of related search queries"
US9928304B2: "Automated content detection of a webpage based on metadata"

2. Site Architecture Optimization
Website Structure

US20130232132A1: "Managing search-engine-optimization content in web pages"
US20120284252A1: "System and method for search engine optimization"
US9116994B2: "Search engine optimization for category specific search results"
US20170116200A1: "Determining relevance scores for locations"
US8577893B1: "Ranking based on reference contexts"
US8386495B1: "Augmented resource graph for scoring resources"

Crawling and Indexing

US8458163B2: "System and method for enabling website owner to manage crawl rate"
US8521746B1: "Preloading of web page content"
US8086953B1: "Identifying transient portions of web pages"
US8042112B1: "Scheduler for search engine crawler"
US8386459B1: "Scheduling a recrawl"
US9063982B2: "Dynamically associating different query execution strategies with selective portions of a database table"

3. Mobile Optimization
Responsive Design

US11823647B1: "Responsive layout system and server"
US9218435B2: "Dynamically modifying media content for mobile devices"
US8745161B2: "Determining and displaying a count of unread items in content feeds"
US9361651B2: "Presenting display characteristics of hierarchical data structures"
US9043425B2: "Dynamically modifying a header of a message"
US9811601B2: "Content adaptation for mobile device"

Mobile User Experience

US11875086B2: "Integration of content and automated assistant"
US9424354B2: "Providing search results based on execution of applications"
US8214764B2: "System and process for presenting search results in a histogram/cluster format"
US9418170B2: "Creating actions based on a user's data"
US9256676B2: "Presenting search result information"
US9298841B2: "Touch input detection in contextual search interfaces"

4. Entity Recognition & Semantic Search
Knowledge Graph Implementation

US20120158633A1: "Knowledge graph based search system"
US9798829B1: "Data reconciliation and knowledge graph building"
US10140515B1: "Personalized knowledge graph"
US9092504B2: "Predictive query completion and search results"
US9904960B2: "Systems, methods, and apparatuses for implementing a related command with a predictive query interface"
US9495345B2: "Methods and systems for characterizing entities"

Natural Language Processing

US10146776B1: "Contextual information for entities"
US9542438B2: "Term completions for entity-centric search"
US9196245B2: "Semantic parsing for entity recognition"
US9342622B2: "Query intent for question answering"
US10025773B2: "Understanding user queries with multiple contextual entities"
US10346477B2: "Semantic interpretation of input using natural language processing"

5. User Experience & Intent Matching
User Behavior Analysis

US8661029B1: "Modifying search result ranking based on implicit user feedback"
US8065296B1: "Systems and methods for determining a quality of provided items"
US9760641B1: "Site scoring for web search"
US9256683B2: "Dynamic client interaction for search"
US9436747B1: "Query generation using structural similarity between documents"
US8762363B1: "Adding result types for search type-ahead"

Intent Recognition

US10423685B2: "Query rewriting with entity detection"
US20160188608A1: "Generating search results containing state links"
US9582549B2: "Computer application data in search results"
US10083157B2: "Generating search result presentations"
US9576050B1: "Generating a response to a search request"
US10242094B2: "Personalizing search results based on user information"

6. Technical SEO Factors
Performance Optimization

US9083583B1: "Latency reduction via adaptive speculative preconnection"
US9769277B2: "Content delivery over multiple layers"
US9729654B1: "Reduction of perceived web page load time"
US10402446B2: "Passive monitoring of user activity in distributed systems"
US10084870B2: "Systems and methods for faster web site loading"
US9235843B2: "Insertion of flexible advertisements"

Core Web Vitals

US10089329B2: "Detecting anomalous application usage"
US10585732B2: "User experience monitoring system"
US10726095B2: "Layout shift identification in web resources"
US10970366B2: "Systems and methods for measuring page loading time"
US10992722B2: "Adaptive content delivery network selection"
US11513088B2: "Rendering content on electronic devices"

7. Local & Voice Search
Local Search Optimization

US8290942B2: "Entity display priority in a distributed geographic information system"
US9275154B2: "Context-sensitive point of interest retrieval"
US9323767B2: "Performance and site awareness of meta-search results"
US8676790B1: "Methods and systems for improving search rankings using advertising data"
US8433703B1: "Location-based, personalized activities for users"
US8515898B2: "Column relevancy for web search"

Voice Search

US9031839B2: "Content generation based on entity data from previous interactions"
US9449275B2: "Actionable voice commands"
US10621421B2: "Entity extraction based on classification of context"
US9437189B2: "Query language dialects and task completion"
US9123341B2: "System and method for analyzing audio information"
US10269345B2: "Automated assistant for controlled voice-based dialog"

8. Social Signals & Author Authority
Social Influence

US8606792B1: "Scoring authors of posts"
US8812586B1: "Correlating social networks with document quality"
US8825649B2: "Smart augmentation of search results"
US8589231B2: "Methods and systems for perceiving a website"
US9177057B2: "Document link reweighting based on user interaction"
US9330174B1: "Social-based updating of search results"

Author Authority

US8606792B1: "Scoring authors of posts"
US9361363B2: "Modifying search result ranking based on populations"
US8818995B1: "Search result ranking based on trust"
US9037581B1: "Personalized search result ranking"
US9449080B1: "System and method for determining quality of cited objects in search results"
US8843477B1: "Method and system for filtering electronic messages"
    """
    
    # Process the patents
    process_patents(patents_list)

if __name__ == "__main__":
    main()
