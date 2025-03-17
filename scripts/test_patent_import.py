#!/usr/bin/env python3
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_patents, get_patent_by_id
from scripts.import_patents import extract_patent_id, fetch_patent_data, process_patents

def test_extract_patent_id():
    """Test the patent ID extraction function"""
    test_cases = [
        ("US6285999B1: \"Method for node ranking in a linked database\"", "US6285999B1"),
        ("US9165040B1: \"Producing a ranking for pages using distances in a web-link graph\"", "US9165040B1"),
        ("US8682892B1: \"Biasing search results for site links\"", "US8682892B1"),
        ("US7716225B1: \"Ranking documents based on user behavior and/or feature data\"", "US7716225B1"),
        ("US20130232132A1: \"Managing search-engine-optimization content in web pages\"", "US20130232132A1"),
    ]
    
    print("Testing patent ID extraction:")
    for test_case, expected in test_cases:
        result = extract_patent_id(test_case)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{test_case}', Expected: '{expected}', Got: '{result}'")
    
    print()

def test_fetch_patent_data():
    """Test fetching patent data from Google Patents"""
    patent_id = "US6285999B1"  # PageRank patent
    
    print(f"Testing patent data fetching for {patent_id}:")
    data = fetch_patent_data(patent_id)
    
    if data:
        print("✓ Successfully fetched patent data:")
        for key, value in data.items():
            if key == 'full_text':
                print(f"  - {key}: {len(value)} characters")
            else:
                print(f"  - {key}: {value}")
    else:
        print("✗ Failed to fetch patent data")
    
    print()

def test_process_patents():
    """Test processing a small list of patents"""
    sample_patents = """
1. Core Ranking Algorithm Patents
PageRank and Link Analysis

US6285999B1: "Method for node ranking in a linked database" (Original PageRank patent)
US9165040B1: "Producing a ranking for pages using distances in a web-link graph"
    """
    
    print("Testing patent processing:")
    process_patents(sample_patents)
    
    # Verify the patents were saved
    patents = get_patents()
    print(f"Found {len(patents)} patents in the database")
    
    for patent in patents:
        print(f"  - {patent['patent_id']}: {patent['title']}")
    
    print()

def main():
    """Main test function"""
    print("== Patent Import Functions Test ==")
    print()
    
    test_extract_patent_id()
    test_fetch_patent_data()
    test_process_patents()
    
    print("Tests completed.")

if __name__ == "__main__":
    main()
