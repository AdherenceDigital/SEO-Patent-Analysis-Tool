# database/db_manager.py
import os
import sqlite3
import datetime
import json

def get_db():
    """Connect to the database and return a connection object"""
    # Ensure the database directory exists
    os.makedirs(os.path.dirname('database/seo_tool.db'), exist_ok=True)
    
    conn = sqlite3.connect('database/seo_tool.db')
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

def get_patents(category=None):
    """Get all patents, optionally filtered by category"""
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute('SELECT * FROM patents WHERE category = ? ORDER BY issue_date DESC', (category,))
    else:
        cursor.execute('SELECT * FROM patents ORDER BY issue_date DESC')
    
    patents = cursor.fetchall()
    conn.close()
    
    return patents

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

# Function to initialize the database if needed
if __name__ == "__main__":
    init_db()
