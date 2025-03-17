#!/usr/bin/env python3
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random

# Check for both possible database paths
DATABASE_PATHS = [
    '/var/db/seo-patent-tool/seo_tool.db',
    '/var/www/seo-patent-tool/database/seo_tool.db',
    'database/seo_tool.db'
]

DATABASE_PATH = None
for path in DATABASE_PATHS:
    if os.path.exists(path):
        DATABASE_PATH = path
        print(f"Found database at: {DATABASE_PATH}")
        break

if not DATABASE_PATH:
    print("Error: Could not find the database file in any of the expected locations.")
    exit(1)

def fetch_assignee(patent_id):
    """Fetch the assignee information for a specific patent."""
    print(f"Fetching assignee for patent {patent_id}...")
    
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
        
        # Extract assignee - try multiple methods
        assignee = None
        
        # Method 1: Look for the specific itemprop
        assignee_elem = soup.select_one('dd[itemprop="assigneeSearch"] span')
        if assignee_elem:
            assignee = assignee_elem.text.strip()
            print(f"Found assignee using method 1: {assignee}")
            return assignee
        
        # Method 2: Look for text labels
        assignee_labels = soup.find_all('dt', string=lambda x: x and 'Current Assignee' in x)
        if assignee_labels and len(assignee_labels) > 0:
            # Get the next dd element after the "Current Assignee" label
            assignee_elem = assignee_labels[0].find_next('dd')
            if assignee_elem:
                assignee = assignee_elem.text.strip()
                print(f"Found assignee using method 2: {assignee}")
                return assignee
        
        # Method 3: Try a more general approach
        aside = soup.select_one('aside')
        if aside:
            assignee_section = aside.find(string=lambda x: x and 'Current Assignee' in x)
            if assignee_section:
                parent = assignee_section.parent
                next_elem = parent.find_next_sibling()
                if next_elem:
                    assignee = next_elem.text.strip()
                    print(f"Found assignee using method 3: {assignee}")
                    return assignee
        
        print(f"Could not find assignee for patent {patent_id}")
        return None
        
    except Exception as e:
        print(f"Error fetching assignee for patent {patent_id}: {e}")
        return None

def update_assignees():
    """Update assignee information for all patents in the database."""
    # Connect to the database directly
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all patents, including those with specific values
    cursor.execute("""
        SELECT patent_id FROM patents 
        WHERE assignee IS NULL 
        OR assignee = '' 
        OR assignee = 'not specified'
        OR assignee = 'Unknown Assignee'
        OR assignee = 'Unknown'
    """)
    
    patents_to_update = [row['patent_id'] for row in cursor.fetchall()]
    
    # If no results, check all patents to see what's available
    if not patents_to_update:
        print("No patents with missing assignee information found. Checking total patents...")
        cursor.execute("SELECT COUNT(*) FROM patents")
        total_count = cursor.fetchone()[0]
        print(f"Total patents in database: {total_count}")
        
        if total_count > 0:
            cursor.execute("SELECT patent_id, assignee FROM patents LIMIT 5")
            sample_patents = cursor.fetchall()
            print("Sample patents:")
            for p in sample_patents:
                print(f"ID: {p['patent_id']}, Assignee: {p['assignee']}")
            
            # Update all patents
            cursor.execute("SELECT patent_id FROM patents")
            patents_to_update = [row['patent_id'] for row in cursor.fetchall()]
    
    print(f"Found {len(patents_to_update)} patents to update assignee information.")
    
    # Update each patent
    updated_count = 0
    for patent_id in patents_to_update:
        assignee = fetch_assignee(patent_id)
        
        if assignee:
            # Update the database
            cursor.execute("UPDATE patents SET assignee = ? WHERE patent_id = ?", (assignee, patent_id))
            conn.commit()
            print(f"Updated assignee for patent {patent_id} to: {assignee}")
            updated_count += 1
    
    print(f"Updated assignee information for {updated_count} patents.")
    conn.close()

if __name__ == "__main__":
    update_assignees()
