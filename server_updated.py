#!/usr/bin/env python3
"""
SEO Patent Analysis Tool - Simple HTTP Server
"""

import os
import sys
import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

# Import the authentication module
import auth

# Configuration
PORT = 8080
DATABASE = 'database/seo_tool.db'
SERVER_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(SERVER_ROOT, 'static')
INCLUDES_DIR = os.path.join(STATIC_ROOT, 'includes')

# Import the patent search module
sys.path.append(SERVER_ROOT)
from patent_search import search_patents, get_patent_details

class SEOPatentHandler(BaseHTTPRequestHandler):
    """Custom handler for SEO Patent Analysis Tool"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL and query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Get cookies
        cookies = self.headers.get('Cookie', '')
        
        # Special case for logout
        if path == '/logout':
            self.handle_logout()
            return
        
        # Verify authorization
        if path != '/login' and not path.startswith('/static/'):
            authorized, session = auth.verify_authorization(self.headers, cookies)
            if not authorized:
                self.send_response(HTTPStatus.FOUND)
                self.send_header('Location', '/login')
                self.end_headers()
                return
        
        # Handle API requests
        if path.startswith('/api/'):
            self.handle_api_request(path, query_params)
            return
            
        # Serve static files for other paths
        if path == '/':
            self.path = '/static/index.html'
        elif path == '/login':
            self.path = '/static/login.html'
        elif os.path.exists(os.path.join(SERVER_ROOT, path[1:])):
            # Path exists, serve it as is
            pass
        else:
            # Try to find an HTML file with the same name in static
            if not path.endswith('/'):
                html_path = f'/static{path}.html'
                if os.path.exists(os.path.join(SERVER_ROOT, html_path[1:])):
                    self.path = html_path
                else:
                    # Serve 404 page
                    self.path = '/static/404.html'
            else:
                # Serve index.html for directory requests
                self.path = f'/static{path}index.html'
        
        # Serve the file
        try:
            f = open(os.path.join(SERVER_ROOT, self.path[1:]), 'rb')
            self.send_response(HTTPStatus.OK)
            
            # Set content type based on file extension
            if self.path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif self.path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif self.path.endswith('.js'):
                self.send_header('Content-type', 'application/javascript')
            elif self.path.endswith('.json'):
                self.send_header('Content-type', 'application/json')
            elif self.path.endswith('.png'):
                self.send_header('Content-type', 'image/png')
            elif self.path.endswith('.jpg') or self.path.endswith('.jpeg'):
                self.send_header('Content-type', 'image/jpeg')
            elif self.path.endswith('.svg'):
                self.send_header('Content-type', 'image/svg+xml')
            else:
                self.send_header('Content-type', 'application/octet-stream')
                
            # Add no-index header for all responses
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
                
            self.end_headers()
            
            # For HTML files, we need to process includes
            if self.path.endswith('.html'):
                content = f.read().decode('utf-8')
                content = self.process_includes(content)
                self.wfile.write(content.encode('utf-8'))
            else:
                # For non-HTML files, send as is
                self.wfile.write(f.read())
            f.close()
            return
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return
    
    def do_POST(self):
        """Handle POST requests"""
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Get content length to read the POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Handle different content types
        content_type = self.headers.get('Content-Type', '')
        
        if content_type.startswith('application/json'):
            post_params = json.loads(post_data)
        else:
            post_params = urllib.parse.parse_qs(post_data)
            # Convert lists to single values for convenience
            for key in post_params:
                if isinstance(post_params[key], list) and len(post_params[key]) == 1:
                    post_params[key] = post_params[key][0]
        
        # Handle login
        if path == '/login':
            self.handle_login(post_params)
            return
            
        # For other routes, verify authentication
        cookies = self.headers.get('Cookie', '')
        authorized, session = auth.verify_authorization(self.headers, cookies)
        if not authorized:
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', '/login')
            self.end_headers()
            return
            
        # Handle patent search
        if path == '/patents/search':
            self.handle_patent_search(post_params)
            return
            
        # Handle patent save
        elif path == '/patents/save':
            self.handle_patent_save(post_params)
            return
            
        # Handle patent analysis
        elif path == '/patents/analyze':
            self.handle_patent_analysis(post_params)
            return
        
        # If no specific handler, return 404
        self.send_error(HTTPStatus.NOT_FOUND)
    
    def handle_api_request(self, path, query_params):
        """Handle API requests"""
        cookies = self.headers.get('Cookie', '')
        authorized, session = auth.verify_authorization(self.headers, cookies)
        if not authorized:
            self.send_json({'error': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED)
            return
            
        if path == '/api/projects':
            self.send_json(self.get_projects())
        elif path == '/api/patents':
            self.send_json(self.get_patents())
        elif path.startswith('/api/patent/'):
            patent_id = path.split('/')[-1]
            self.send_json(self.get_patent(patent_id))
        elif path == '/api/search':
            query = query_params.get('q', [''])[0]
            num_results = int(query_params.get('n', ['10'])[0])
            results = search_patents(query, num_results)
            self.send_json(results)
        else:
            self.send_json({'error': 'Not found'}, HTTPStatus.NOT_FOUND)
    
    def send_json(self, data, status=HTTPStatus.OK):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_db_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(os.path.join(SERVER_ROOT, DATABASE))
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_projects(self):
        """Get all projects from the database"""
        conn = self.get_db_connection()
        projects = conn.execute('SELECT * FROM projects').fetchall()
        conn.close()
        return [dict(project) for project in projects]
    
    def get_patents(self):
        """Get all patents from the database"""
        conn = self.get_db_connection()
        patents = conn.execute('SELECT * FROM patents').fetchall()
        conn.close()
        return [dict(patent) for patent in patents]
    
    def get_patent(self, patent_id):
        """Get a specific patent from the database"""
        conn = self.get_db_connection()
        patent = conn.execute('SELECT * FROM patents WHERE id = ?', (patent_id,)).fetchone()
        
        if patent:
            patent_dict = dict(patent)
            
            # Get analyses for this patent
            analyses = conn.execute(
                'SELECT * FROM patent_analyses WHERE patent_id = ?', 
                (patent_id,)
            ).fetchall()
            
            if analyses:
                patent_dict['analyses'] = [dict(analysis) for analysis in analyses]
            
            conn.close()
            return patent_dict
        
        conn.close()
        return None
    
    def handle_login(self, post_params):
        """Handle login requests"""
        if isinstance(post_params, dict):
            username = post_params.get('username', '')
            password = post_params.get('password', '')
        else:
            username = post_params.get('username', [''])[0]
            password = post_params.get('password', [''])[0]
        
        # Authenticate user
        if auth.verify_credentials(username, password):
            # Set a cookie for session
            cookie = auth.get_auth_cookie(username)
            
            # Redirect to dashboard
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Set-Cookie', cookie)
            self.send_header('Location', '/dashboard')
            self.end_headers()
        else:
            # Redirect back to login with error
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', '/login?error=1')
            self.end_headers()
    
    def handle_logout(self):
        """Handle logout requests"""
        # Get the session cookie
        cookies = self.headers.get('Cookie', '')
        cookie = SimpleCookie(cookies)
        
        # Clear the session cookie by setting an expired date
        self.send_response(HTTPStatus.FOUND)
        self.send_header('Set-Cookie', 'session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly')
        self.send_header('Location', '/login')
        self.end_headers()
    
    def handle_patent_search(self, post_params):
        """Handle patent search requests"""
        if isinstance(post_params, dict):
            query = post_params.get('query', '')
            num_results = int(post_params.get('num_results', 10))
        else:
            query = post_params.get('query', [''])[0]
            num_results = int(post_params.get('num_results', ['10'])[0])
        
        # Search for patents
        results = search_patents(query, num_results)
        
        # Redirect to search results page
        self.send_response(HTTPStatus.FOUND)
        self.send_header('Location', f'/search_results?q={urllib.parse.quote(query)}&n={num_results}')
        self.end_headers()
    
    def handle_patent_save(self, post_params):
        """Handle patent save requests"""
        if isinstance(post_params, dict):
            patent_id = post_params.get('patent_id', '')
            project_id = post_params.get('project_id', '')
        else:
            patent_id = post_params.get('patent_id', [''])[0]
            project_id = post_params.get('project_id', [''])[0]
        
        # Get patent details from API
        patent_details = get_patent_details(patent_id)
        
        if patent_details:
            conn = self.get_db_connection()
            
            # Insert patent into database
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patents (
                    patent_id, title, abstract, filing_date, issue_date, 
                    assignee, inventors, category, full_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patent_details['patent_id'],
                patent_details['title'],
                patent_details['abstract'],
                patent_details['filing_date'],
                patent_details['issue_date'],
                patent_details['assignee'],
                patent_details['inventors'],
                patent_details['category'],
                patent_details['full_text']
            ))
            
            # Get the inserted patent ID
            patent_db_id = cursor.lastrowid
            
            # If project ID is provided, link patent to project
            if project_id:
                cursor.execute('''
                    INSERT INTO project_patents (project_id, patent_id)
                    VALUES (?, ?)
                ''', (project_id, patent_db_id))
            
            conn.commit()
            conn.close()
            
            # Redirect to patent details page
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', f'/patents/view/{patent_db_id}')
            self.end_headers()
        else:
            # If patent not found, redirect back with error
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', '/patents/search?error=1')
            self.end_headers()
    
    def handle_patent_analysis(self, post_params):
        """Handle patent analysis requests"""
        if isinstance(post_params, dict):
            patent_id = post_params.get('patent_id', '')
        else:
            patent_id = post_params.get('patent_id', [''])[0]
        
        # Get patent from database
        conn = self.get_db_connection()
        patent = conn.execute('SELECT * FROM patents WHERE id = ?', (patent_id,)).fetchone()
        
        if patent:
            # Perform analysis (placeholder)
            analysis = {
                'patent_id': patent_id,
                'seo_impact': 'High',
                'innovation_score': 85,
                'keywords': json.dumps(['ranking', 'algorithm', 'quality', 'relevance']),
                'keyphrases': json.dumps(['search quality', 'page ranking', 'site authority']),
                'recommendations': json.dumps([
                    'Focus on comprehensive content that demonstrates E-A-T',
                    'Create content that fully addresses user intent',
                    'Improve technical SEO aspects mentioned in the patent'
                ]),
                'insight_summary': 'This patent suggests Google places high importance on content quality and relevance signals.'
            }
            
            # Save analysis to database
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patent_analyses (
                    patent_id, seo_impact, innovation_score, keywords,
                    keyphrases, recommendations, insight_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patent_id,
                analysis['seo_impact'],
                analysis['innovation_score'],
                analysis['keywords'],
                analysis['keyphrases'],
                analysis['recommendations'],
                analysis['insight_summary']
            ))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Redirect to analysis page
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', f'/patents/analysis/{analysis_id}')
            self.end_headers()
        else:
            conn.close()
            # If patent not found, redirect back with error
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', '/patents?error=1')
            self.end_headers()
    
    def process_includes(self, content):
        """Process includes in HTML content"""
        # Find all include placeholders
        include_pattern = r'<!-- INCLUDE:([a-zA-Z0-9_/.-]+) -->'
        matches = re.finditer(include_pattern, content)
        
        # Replace each include with its content
        for match in matches:
            include_path = match.group(1).strip()
            full_path = os.path.join(INCLUDES_DIR, include_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    include_content = f.read()
                content = content.replace(match.group(0), include_content)
            else:
                print(f"Include file not found: {full_path}")
        
        return content

def init_db():
    """Initialize the database if it doesn't exist"""
    db_path = os.path.join(SERVER_ROOT, DATABASE)
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patent_id TEXT NOT NULL,
        title TEXT NOT NULL,
        abstract TEXT,
        filing_date TEXT,
        issue_date TEXT,
        assignee TEXT,
        inventors TEXT,
        category TEXT,
        full_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patent_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patent_id INTEGER,
        seo_impact TEXT,
        innovation_score INTEGER,
        keywords TEXT,
        keyphrases TEXT,
        recommendations TEXT,
        insight_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patent_id) REFERENCES patents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_patents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        patent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id),
        FOREIGN KEY (patent_id) REFERENCES patents (id)
    )
    ''')
    
    # Insert demo data if tables are empty
    if not cursor.execute('SELECT COUNT(*) FROM projects').fetchone()[0]:
        cursor.execute('''
        INSERT INTO projects (name, description)
        VALUES 
            ('SEO Strategy 2025', 'Research for upcoming algorithm changes'),
            ('Competitor Analysis', 'Patent analysis of major competitors')
        ''')
    
    if not cursor.execute('SELECT COUNT(*) FROM patents').fetchone()[0]:
        cursor.execute('''
        INSERT INTO patents (patent_id, title, abstract, filing_date, issue_date, assignee, inventors, category, full_text)
        VALUES 
            ('US10699311B2', 'Site Quality Score', 'Methods, systems, and apparatus for providing a site quality score for a site.', '2018-06-15', '2020-06-30', 'Google LLC', 'John Smith, Jane Doe', 'Search Ranking', 'Example full text of the patent...'),
            ('US9002867B1', 'Modifying Ranking Data Based on Document Changes', 'A system and method for modifying ranking data based on detection of changes to documents.', '2010-12-30', '2015-04-07', 'Google Inc.', 'Robert Johnson, Mary Williams', 'Search Ranking', 'Example full text of the patent...')
        ''')
    
    if not cursor.execute('SELECT COUNT(*) FROM patent_analyses').fetchone()[0]:
        cursor.execute('''
        INSERT INTO patent_analyses (patent_id, seo_impact, innovation_score, keywords, keyphrases, recommendations, insight_summary)
        VALUES 
            (1, 'High', 85, '["quality", "score", "ranking", "algorithm"]', '["site quality", "ranking algorithm", "scoring system"]', '["Focus on site quality signals", "Improve E-A-T factors"]', 'This patent indicates Google uses a site quality score as a ranking factor.'),
            (2, 'Medium', 72, '["ranking", "document", "changes", "freshness"]', '["content freshness", "document changes", "ranking signal"]', '["Regular content updates", "Monitor document changes"]', 'This patent shows Google values content freshness and may adjust rankings based on document changes.')
        ''')
    
    conn.commit()
    conn.close()

def run_server():
    """Run the HTTP server"""
    init_db()
    
    # Change to the server root directory
    os.chdir(SERVER_ROOT)
    
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, SEOPatentHandler)
    
    print(f"Server running at http://localhost:{PORT}/")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
