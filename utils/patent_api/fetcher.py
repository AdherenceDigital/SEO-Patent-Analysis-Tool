#!/usr/bin/env python3
"""
Patent Data Fetcher
------------------
Module for fetching patent data from external sources like Google Patents.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
import urllib.parse

class PatentFetcher:
    """Class for fetching patent data from various sources."""
    
    def __init__(self, cache_enabled=True):
        """Initialize the patent fetcher.
        
        Args:
            cache_enabled (bool): Whether to cache results to avoid repeated requests
        """
        self.cache_enabled = cache_enabled
        self.cache = {}
    
    def fetch_from_google_patents(self, patent_id):
        """Fetch patent data from Google Patents.
        
        Args:
            patent_id (str): The patent ID (e.g., 'US10885017B2')
            
        Returns:
            dict: Patent data including title, abstract, claims, etc.
        """
        # Check cache first if enabled
        if self.cache_enabled and patent_id in self.cache:
            return self.cache[patent_id]
            
        # Clean and normalize the patent ID
        clean_id = self._normalize_patent_id(patent_id)
        
        # Construct Google Patents URL
        url = f"https://patents.google.com/patent/{clean_id}/en"
        
        try:
            # Make request to Google Patents
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            if response.status_code != 200:
                return {
                    'error': f"Failed to fetch patent data. Status code: {response.status_code}",
                    'patent_id': patent_id
                }
                
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract patent information
            patent_data = self._extract_patent_data(soup, patent_id)
            
            # Cache the result if enabled
            if self.cache_enabled:
                self.cache[patent_id] = patent_data
                
            return patent_data
            
        except Exception as e:
            return {
                'error': f"Error fetching patent data: {str(e)}",
                'patent_id': patent_id
            }
    
    def _normalize_patent_id(self, patent_id):
        """Normalize a patent ID to the format expected by Google Patents.
        
        Args:
            patent_id (str): The patent ID to normalize
            
        Returns:
            str: Normalized patent ID
        """
        # Remove any whitespace
        patent_id = patent_id.strip()
        
        # Add US prefix if missing and looks like a US patent
        if not patent_id.startswith(('US', 'EP', 'WO', 'CN', 'JP')):
            if re.match(r'^\d+[A-Z]?\d*$', patent_id):
                patent_id = 'US' + patent_id
        
        return patent_id
    
    def _extract_patent_data(self, soup, patent_id):
        """Extract patent data from the BeautifulSoup object.
        
        Args:
            soup (BeautifulSoup): The parsed HTML
            patent_id (str): The patent ID
            
        Returns:
            dict: Structured patent data
        """
        try:
            # Extract title
            title_elem = soup.find('span', itemprop='title')
            title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Extract abstract
            abstract_elem = soup.find('div', itemprop='abstract')
            abstract = abstract_elem.text.strip() if abstract_elem else ""
            
            # Extract filing date and issue date
            dates = soup.find_all('time', itemprop=['applicationDate', 'publicationDate'])
            filing_date = ""
            issue_date = ""
            
            for date_elem in dates:
                if date_elem.get('itemprop') == 'applicationDate':
                    filing_date = date_elem.text.strip()
                elif date_elem.get('itemprop') == 'publicationDate':
                    issue_date = date_elem.text.strip()
            
            # Extract inventors
            inventor_elems = soup.find_all('dd', itemprop='inventor')
            inventors = [elem.text.strip() for elem in inventor_elems] if inventor_elems else []
            
            # Extract assignee
            assignee_elem = soup.find('dd', itemprop='assignee')
            assignee = assignee_elem.text.strip() if assignee_elem else ""
            
            # Extract claims
            claims_section = soup.find('section', attrs={'itemprop': 'claims'})
            claims = claims_section.text.strip() if claims_section else ""
            
            # Extract description
            description_section = soup.find('section', attrs={'itemprop': 'description'})
            description = description_section.text.strip() if description_section else ""
            
            # Extract classification
            classification_elem = soup.find('dd', itemprop='classifications')
            classification = classification_elem.text.strip() if classification_elem else ""
            
            # Build the full patent data object
            patent_data = {
                'patent_id': patent_id,
                'title': title,
                'abstract': abstract,
                'filing_date': filing_date,
                'issue_date': issue_date,
                'inventors': inventors,
                'assignee': assignee,
                'classification': classification,
                'claims': claims,
                'description': description,
                'url': f"https://patents.google.com/patent/{self._normalize_patent_id(patent_id)}/en"
            }
            
            return patent_data
            
        except Exception as e:
            return {
                'error': f"Error extracting patent data: {str(e)}",
                'patent_id': patent_id
            }
    
    def fetch_batch(self, patent_ids):
        """Fetch data for multiple patents.
        
        Args:
            patent_ids (list): List of patent IDs to fetch
            
        Returns:
            dict: Dictionary mapping patent IDs to their data
        """
        results = {}
        for patent_id in patent_ids:
            results[patent_id] = self.fetch_from_google_patents(patent_id)
        return results
