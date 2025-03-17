import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from urllib.parse import quote_plus

class GooglePatentsAPI:
    """
    A utility class for interacting with Google Patents.
    Since Google doesn't provide an official API, this class uses web scraping to gather data.
    """
    
    SEARCH_URL = "https://patents.google.com/search"
    PATENT_URL = "https://patents.google.com/patent/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_patents(self, query, num_results=10, language="en", sort="relevance"):
        """
        Search for patents based on a query string.
        
        Args:
            query (str): The search query
            num_results (int): Number of results to return (max 100)
            language (str): Language code for results (default: en)
            sort (str): Sort method (relevance, new, old)
            
        Returns:
            list: A list of patent metadata dictionaries
        """
        # Limit number of results
        num_results = min(num_results, 100)
        
        # Format query for URL
        formatted_query = quote_plus(query)
        
        # Set up parameters
        params = {
            'q': query,
            'num': num_results,
            'lan': language,
            'sort': sort
        }
        
        try:
            # Make the request
            response = self.session.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            search_results = soup.select('.result-item')
            
            for result in search_results:
                try:
                    # Get patent ID
                    patent_id_elem = result.select_one('.patent-number')
                    patent_id = patent_id_elem.text.strip() if patent_id_elem else None
                    
                    # Skip if no patent ID
                    if not patent_id:
                        continue
                    
                    # Get title
                    title_elem = result.select_one('.patent-title')
                    title = title_elem.text.strip() if title_elem else "Unknown Title"
                    
                    # Get applicant/assignee
                    applicant_elem = result.select_one('.patent-assignee')
                    applicant = applicant_elem.text.strip() if applicant_elem else None
                    
                    # Get filing date
                    filing_date_elem = result.select_one('.filing-date')
                    filing_date = filing_date_elem.text.strip() if filing_date_elem else None
                    
                    # Get URL
                    url = f"{self.PATENT_URL}{patent_id}"
                    
                    # Add to results
                    results.append({
                        'patent_id': patent_id,
                        'title': title,
                        'applicant': applicant,
                        'filing_date': filing_date,
                        'url': url
                    })
                    
                    # Stop if we have enough results
                    if len(results) >= num_results:
                        break
                        
                except Exception as e:
                    print(f"Error parsing search result: {str(e)}")
                    continue
            
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            return results
            
        except Exception as e:
            print(f"Error searching for patents: {str(e)}")
            return []
    
    def get_patent_details(self, patent_id):
        """
        Get detailed information about a specific patent.
        
        Args:
            patent_id (str): The patent ID
            
        Returns:
            dict: A dictionary containing patent details
        """
        url = f"{self.PATENT_URL}{patent_id}"
        
        try:
            # Make the request
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            # Title
            title_elem = soup.select_one('h1.title')
            title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Abstract
            abstract_elem = soup.select_one('.abstract')
            abstract = abstract_elem.text.strip() if abstract_elem else None
            
            # Assignee
            assignee_elem = soup.select_one('.patent-assignee')
            assignee = assignee_elem.text.strip() if assignee_elem else None
            
            # Filing date
            filing_date_elem = soup.select_one('.filing-date')
            filing_date = filing_date_elem.text.strip() if filing_date_elem else None
            
            # Issue date
            issue_date_elem = soup.select_one('.grant-date')
            issue_date = issue_date_elem.text.strip() if issue_date_elem else None
            
            # Inventors
            inventors = []
            inventor_elems = soup.select('.inventor')
            for inventor_elem in inventor_elems:
                inventors.append(inventor_elem.text.strip())
            
            # Full text
            description_elem = soup.select_one('.description')
            full_text = description_elem.text.strip() if description_elem else None
            
            # Claims
            claims_elem = soup.select_one('.claims')
            claims = claims_elem.text.strip() if claims_elem else None
            
            # If we have claims, append to full text
            if claims and full_text:
                full_text += "\n\nCLAIMS:\n" + claims
            elif claims:
                full_text = "CLAIMS:\n" + claims
            
            # Categories/classification
            category = None
            classification_elem = soup.select_one('.classification-tree')
            if classification_elem:
                category = classification_elem.text.strip()
            
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            # Return the patent details
            return {
                'patent_id': patent_id,
                'title': title,
                'abstract': abstract,
                'assignee': assignee,
                'filing_date': filing_date,
                'issue_date': issue_date,
                'inventors': inventors,
                'full_text': full_text,
                'category': category,
                'url': url
            }
            
        except Exception as e:
            print(f"Error getting patent details for {patent_id}: {str(e)}")
            return None
    
    def get_patent_citations(self, patent_id, direction="forward", max_results=50):
        """
        Get citations for a patent.
        
        Args:
            patent_id (str): The patent ID
            direction (str): 'forward' for patents citing this one, 'backward' for patents cited by this one
            max_results (int): Maximum number of citations to return
            
        Returns:
            list: A list of citation dictionaries
        """
        url = f"{self.PATENT_URL}{patent_id}"
        tab = "citedby" if direction == "forward" else "citations"
        
        try:
            # Make the request to the citations tab
            response = self.session.get(f"{url}/{tab}")
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract citations
            citations = []
            citation_elems = soup.select('.search-result')
            
            for citation_elem in citation_elems[:max_results]:
                try:
                    # Get patent ID
                    patent_id_elem = citation_elem.select_one('.patent-number')
                    cit_patent_id = patent_id_elem.text.strip() if patent_id_elem else None
                    
                    # Skip if no patent ID
                    if not cit_patent_id:
                        continue
                    
                    # Get title
                    title_elem = citation_elem.select_one('.patent-title')
                    title = title_elem.text.strip() if title_elem else "Unknown Title"
                    
                    # Get applicant/assignee
                    applicant_elem = citation_elem.select_one('.patent-assignee')
                    applicant = applicant_elem.text.strip() if applicant_elem else None
                    
                    # Get filing date
                    filing_date_elem = citation_elem.select_one('.filing-date')
                    filing_date = filing_date_elem.text.strip() if filing_date_elem else None
                    
                    # Add to citations
                    citations.append({
                        'patent_id': cit_patent_id,
                        'title': title,
                        'applicant': applicant,
                        'filing_date': filing_date,
                        'relationship': 'cited by' if direction == "forward" else 'cites'
                    })
                    
                except Exception as e:
                    print(f"Error parsing citation: {str(e)}")
                    continue
            
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            return citations
            
        except Exception as e:
            print(f"Error getting patent citations for {patent_id}: {str(e)}")
            return []
