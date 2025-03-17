# database/db_manager.py
import os
import sqlite3
import datetime
import json

def get_db():
    """Connect to the database and return a connection object"""
    # Get database path from environment, or use default
    db_path = os.environ.get('DATABASE_PATH', 'database/seo_tool.db')
    
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn

def init_db():
    """Initialize the database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Read schema file
    with open('database/schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute schema
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")

def create_project(name, description, url):
    """Create a new project"""
    conn = get_db()
    cursor = conn.cursor()
    
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        'INSERT INTO projects (name, description, url, created_at) VALUES (?, ?, ?, ?)',
        (name, description, url, created_at)
    )
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return project_id

def get_projects():
    """Get all projects"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
    projects = cursor.fetchall()
    
    conn.close()
    
    return projects

def get_project_by_name(name):
    """Get a project by name"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
    project = cursor.fetchone()
    
    conn.close()
    
    return project

def get_project_by_id(project_id):
    """Get a project by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    
    conn.close()
    
    return project

def save_upload(project_id, upload_type, filename, notes=None):
    """Save an upload record"""
    conn = get_db()
    cursor = conn.cursor()
    
    uploaded_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        'INSERT INTO uploads (project_id, upload_type, filename, notes, uploaded_at) VALUES (?, ?, ?, ?, ?)',
        (project_id, upload_type, filename, notes, uploaded_at)
    )
    
    upload_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return upload_id

def get_uploads_by_project(project_id, upload_type=None):
    """Get all uploads for a project, optionally filtered by type"""
    conn = get_db()
    cursor = conn.cursor()
    
    if upload_type:
        cursor.execute(
            'SELECT * FROM uploads WHERE project_id = ? AND upload_type = ? ORDER BY uploaded_at DESC',
            (project_id, upload_type)
        )
    else:
        cursor.execute(
            'SELECT * FROM uploads WHERE project_id = ? ORDER BY uploaded_at DESC',
            (project_id,)
        )
    
    uploads = cursor.fetchall()
    conn.close()
    
    return uploads

def delete_upload(upload_id):
    """Delete an upload and its associated data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get upload details to determine what associated data to delete
    cursor.execute('SELECT upload_type FROM uploads WHERE id = ?', (upload_id,))
    upload = cursor.fetchone()
    
    if not upload:
        conn.close()
        return False
    
    # Delete associated data based on upload_type
    if upload['upload_type'] == 'ahrefs_backlinks':
        cursor.execute('DELETE FROM ahrefs_backlinks WHERE upload_id = ?', (upload_id,))
    elif upload['upload_type'] == 'ahrefs_internal_links':
        cursor.execute('DELETE FROM ahrefs_internal_links WHERE upload_id = ?', (upload_id,))
    elif upload['upload_type'] == 'screaming_frog':
        cursor.execute('DELETE FROM screaming_frog_data WHERE upload_id = ?', (upload_id,))
    elif upload['upload_type'] == 'search_console':
        cursor.execute('DELETE FROM search_console_data WHERE upload_id = ?', (upload_id,))
    
    # Delete the upload record
    cursor.execute('DELETE FROM uploads WHERE id = ?', (upload_id,))
    
    conn.commit()
    conn.close()
    
    return True

def save_patent(patent_id, title, abstract, filing_date, issue_date, inventors, assignee, category, full_text=None):
    """Save a patent to the database"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if patent already exists
    cursor.execute('SELECT id FROM patents WHERE patent_id = ?', (patent_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing patent
        cursor.execute(
            '''UPDATE patents SET 
               title = ?, abstract = ?, filing_date = ?, issue_date = ?, 
               inventors = ?, assignee = ?, category = ?, full_text = ?
               WHERE patent_id = ?''',
            (title, abstract, filing_date, issue_date, inventors, assignee, category, full_text, patent_id)
        )
    else:
        # Insert new patent
        cursor.execute(
            '''INSERT INTO patents 
               (patent_id, title, abstract, filing_date, issue_date, inventors, assignee, category, full_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (patent_id, title, abstract, filing_date, issue_date, inventors, assignee, category, full_text)
        )
    
    conn.commit()
    conn.close()

def get_patents(category=None, page=1, per_page=10):
    """Get patents with pagination, optionally filtered by category"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get the total count first
    if category:
        cursor.execute('SELECT COUNT(*) FROM patents WHERE category LIKE ?', (f'%{category}%',))
    else:
        cursor.execute('SELECT COUNT(*) FROM patents')
    
    total_count = cursor.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get the paginated results
    if category:
        cursor.execute(
            'SELECT * FROM patents WHERE category LIKE ? ORDER BY issue_date DESC LIMIT ? OFFSET ?', 
            (f'%{category}%', per_page, offset)
        )
    else:
        cursor.execute(
            'SELECT * FROM patents ORDER BY issue_date DESC LIMIT ? OFFSET ?', 
            (per_page, offset)
        )
    
    patents = cursor.fetchall()
    conn.close()
    
    return {
        'patents': patents,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page  # Ceiling division
    }

def get_patent_by_id(patent_id):
    """Get a patent by its ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM patents WHERE patent_id = ?', (patent_id,))
    patent = cursor.fetchone()
    
    conn.close()
    
    return patent

def save_analysis(project_id, patent_id, upload_id, analysis_data, recommendations):
    """Save a patent analysis for a project"""
    conn = get_db()
    cursor = conn.cursor()
    
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert dictionaries to JSON if necessary
    if isinstance(analysis_data, dict):
        analysis_data = json.dumps(analysis_data)
    
    if isinstance(recommendations, dict):
        recommendations = json.dumps(recommendations)
    
    cursor.execute(
        '''INSERT INTO analyses 
           (project_id, patent_id, upload_id, analysis_data, recommendations, created_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (project_id, patent_id, upload_id, analysis_data, recommendations, created_at)
    )
    
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return analysis_id

def get_analyses_by_project(project_id, patent_id=None):
    """Get all analyses for a project, optionally filtered by patent"""
    conn = get_db()
    cursor = conn.cursor()
    
    if patent_id:
        cursor.execute(
            '''SELECT a.*, p.title as patent_title, u.upload_type, u.filename
               FROM analyses a
               JOIN patents p ON a.patent_id = p.patent_id
               JOIN uploads u ON a.upload_id = u.id
               WHERE a.project_id = ? AND a.patent_id = ?
               ORDER BY a.created_at DESC''',
            (project_id, patent_id)
        )
    else:
        cursor.execute(
            '''SELECT a.*, p.title as patent_title, u.upload_type, u.filename
               FROM analyses a
               JOIN patents p ON a.patent_id = p.patent_id
               JOIN uploads u ON a.upload_id = u.id
               WHERE a.project_id = ?
               ORDER BY a.created_at DESC''',
            (project_id,)
        )
    
    analyses = cursor.fetchall()
    conn.close()
    
    return analyses

def ensure_patents_exist():
    """Make sure the demo patents exist in the database"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Patent data
    demo_patents = [
        {
            'patent_id': 'US10719547B2',
            'title': 'Entity Recognition in Search Algorithms',
            'abstract': 'Methods, systems, and apparatus for entity recognition within search queries. One method includes detecting that a search query includes one or more entity terms and modifying the query to improve search results based on entity recognition.',
            'filing_date': '2019-01-15',
            'issue_date': '2020-07-21',
            'inventors': 'John Smith, Jane Doe',
            'assignee': 'Google LLC',
            'category': 'Search Algorithms',
            'full_text': 'Detailed description of entity recognition systems used in search algorithms including techniques for identifying entities in queries and adjusting ranking accordingly.',
        },
        {
            'patent_id': 'US10885017B2',
            'title': 'Ranking Search Results Using Interaction Metrics',
            'abstract': 'A system for ranking search results based on user interaction data. The system tracks user interactions with search results and uses this data to improve future search rankings.',
            'filing_date': '2019-04-10',
            'issue_date': '2021-01-05',
            'inventors': 'Sarah Johnson, Michael Brown',
            'assignee': 'Google LLC',
            'category': 'Search Algorithms',
            'full_text': 'This patent describes methods for tracking and analyzing user interactions with search results, and using these metrics to improve the quality and relevance of future search results.',
        },
        {
            'patent_id': 'US10909122B1',
            'title': 'Mobile-First Indexing Method',
            'abstract': 'A system and method for prioritizing mobile content when indexing web pages for search. The method includes analyzing mobile versions of pages first to determine content and relevance.',
            'filing_date': '2020-02-14',
            'issue_date': '2021-02-02',
            'inventors': 'David Wilson, Lisa Chen',
            'assignee': 'Google LLC',
            'category': 'Indexing',
            'full_text': 'This patent covers Google\'s mobile-first indexing approach which prioritizes the mobile version of a website for indexing and ranking. It includes methods for comparing mobile and desktop versions of sites, and algorithms for handling content disparities.',
        }
    ]
    
    # Check if each patent exists, and insert if it doesn't
    for patent in demo_patents:
        cursor.execute('SELECT COUNT(*) FROM patents WHERE patent_id = ?', (patent['patent_id'],))
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute('''
                INSERT INTO patents (
                    patent_id, title, abstract, filing_date, issue_date, 
                    inventors, assignee, category, full_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patent['patent_id'], patent['title'], patent['abstract'],
                patent['filing_date'], patent['issue_date'], patent['inventors'],
                patent['assignee'], patent['category'], patent['full_text']
            ))
    
    conn.commit()
    conn.close()
    return True

# Function to initialize the database if needed
if __name__ == "__main__":
    init_db()
    ensure_patents_exist()
