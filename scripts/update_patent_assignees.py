#!/usr/bin/env python3
import os
import sys
import time
import random
import requests
from bs4 import BeautifulSoup
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_patents

# Configure database path
if os.path.exists('/var/db/seo-patent-tool/seo_tool.db'):
    # Server path
    DATABASE_PATH = '/var/db/seo-patent-tool/seo_tool.db'
else:
    # Local path
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'seo_tool.db')

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
        
        return assignee
        
    except Exception as e:
        print(f"Error fetching assignee for patent {patent_id}: {e}")
        return None

def update_assignees():
    """Update assignee information for all patents in the database."""
    # Get all patents
    all_patents = get_patents(page=1, per_page=1000)
    patents_to_update = []
    
    # Identify patents with missing assignees
    for patent in all_patents['patents']:
        if not patent.get('assignee'):
            patents_to_update.append(patent)
    
    print(f"Found {len(patents_to_update)} patents with missing assignee information.")
    
    # Connect to the database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Update each patent
    updated_count = 0
    for patent in patents_to_update:
        patent_id = patent['patent_id']
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
