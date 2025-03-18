#!/usr/bin/env python3

import os
import re
import sys
import json
import base64
import urllib.parse
import mimetypes
import http.server
import logging
import time
import subprocess
from http import HTTPStatus
from urllib.parse import parse_qs

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't') else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('seo_patent_tool')

# Add database imports
from database.db_manager import get_patents, get_patent_by_id, ensure_patents_exist, get_projects, create_project

# Default port and host
PORT = int(os.environ.get('PORT', 8000))
HOST = os.environ.get('HOST', '0.0.0.0')

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.environ.get('STATIC_DIR', 'static')
INCLUDES_DIR = os.environ.get('INCLUDES_DIR', 'includes')
STATIC_ROOT = os.path.join(BASE_DIR, STATIC_DIR)
INCLUDES_DIR = os.path.join(STATIC_ROOT, INCLUDES_DIR)

class SEOPatentHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for SEO Patent Analysis Tool"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        logger.info(f"Handling request: {path} with params: {query_params}")
        
        # Handle API endpoints
        if path.startswith('/api/'):
            logger.info(f"Processing API request: {path}")
            self.handle_api(path, query_params)
            return
        
        # Handle special routes
        if path == '/':
            logger.info("Serving home page")
            path = '/index.html'
        elif path == '/patents':
            logger.info("Serving patents index page")
            path = '/patents/index.html'
        elif path.startswith('/patents/') and len(path.split('/')) == 3 and not path.endswith('.html') and not path.endswith('.css') and not path.endswith('.js'):
            # Handle /patents/[patent-id]
            patent_id = path.split('/')[2]
            logger.info(f"Serving patent detail page for ID: {patent_id}")
            # Store the patent ID for use in process_includes
            self.patent_id = patent_id
            path = '/patents/view/index.html'
        elif path == '/dashboard':
            logger.info("Serving dashboard page")
            path = '/dashboard.html'
        elif path == '/projects':
            logger.info("Serving projects page")
            path = '/projects/index.html'
        
        # Handle special case for favicon
        if path == '/favicon.ico':
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return
        
        # Convert path to file path
        if path.startswith('/'):
            path = path[1:]
        
        # Prepend static for HTML files
        if not path.startswith('static/'):
            file_path = os.path.join(STATIC_ROOT, path)
        else:
            file_path = os.path.join(BASE_DIR, path)
        
        print(f"Serving: {file_path}")
        
        # Determine content type
        _, ext = os.path.splitext(file_path)
        content_type = mimetypes.types_map.get(ext, 'application/octet-stream')
        
        try:
            # Open the file
            logger.info(f"Attempting to open file: {file_path}")
            with open(file_path, 'rb') as f:
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', content_type)
                self.send_header('X-Robots-Tag', 'noindex, nofollow')
                self.end_headers()
                
                # For HTML files, process includes
                if ext == '.html':
                    logger.info(f"Processing HTML file: {file_path}")
                    content = f.read().decode('utf-8')
                    content = self.process_includes(content)
                    self.wfile.write(content.encode('utf-8'))
                else:
                    # For non-HTML files, send as is
                    logger.info(f"Serving non-HTML file: {file_path}")
                    self.wfile.write(f.read())
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return
        except Exception as e:
            logger.error(f"Error serving file {file_path}: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
            return
    
    def do_POST(self):
        """Handle POST requests"""
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        logger.info(f"Handling POST request: {path}")
        
        # Handle API endpoints
        if path.startswith('/api/'):
            self.handle_api(path, {})
            return
    
    def handle_api(self, path, query_params):
        """Handle API requests"""
        if path == '/api/patents':
            self.handle_api_patents(query_params)
        elif path == '/api/patent':
            self.handle_api_patent(query_params)
        elif path == '/api/projects':
            self.handle_api_projects()
        elif path == '/api/projects/create' and self.command == 'POST':
            self.handle_api_projects_create()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'API endpoint not found')
            
    def handle_api_projects(self):
        """Handle /api/projects endpoint"""
        # Get projects from the database
        projects = get_projects()
        
        # Convert to JSON serializable format
        projects_json = []
        for project in projects:
            projects_json.append({
                'id': project['id'],
                'name': project['name'],
                'description': project['description'],
                'url': project.get('url', ''),
                'created_at': project['created_at']
            })
        
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(projects_json).encode('utf-8'))
        
    def handle_api_projects_create(self):
        """Handle creating a new project via POST to /api/projects/create"""
        # Get POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # Parse JSON data
            data = json.loads(post_data)
            
            # Extract project details
            name = data.get('name')
            description = data.get('description', '')
            url = data.get('url', '')
            
            if not name:
                raise ValueError("Project name is required")
            
            # Create the project
            project_id = create_project(name, description, url)
            
            # Return success response
            response = {
                'success': True,
                'message': 'Project created successfully',
                'project_id': project_id
            }
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            # Return error response
            response = {
                'success': False,
                'error': str(e)
            }
            
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def handle_api_patents(self, query_params):
        """Handle /api/patents endpoint"""
        category = query_params.get('category', [None])[0]
        page = int(query_params.get('page', ['1'])[0])
        per_page = int(query_params.get('per_page', ['10'])[0])
        
        result = get_patents(category, page, per_page)
        
        # Convert patents to JSON serializable format
        patents_json = {
            'patents': [],
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'total_pages': result['total_pages']
        }
        
        for patent in result['patents']:
            patents_json['patents'].append({
                'id': patent['patent_id'],
                'title': patent['title'],
                'abstract': patent['abstract'],
                'filing_date': patent['filing_date'],
                'issue_date': patent['issue_date'],
                'inventors': patent['inventors'],
                'assignee': patent['assignee'],
                'category': patent['category']
            })
        
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(patents_json).encode('utf-8'))
    
    def handle_api_patent(self, query_params):
        """Handle /api/patent endpoint"""
        patent_id = query_params.get('id', [None])[0]
        
        if not patent_id:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Missing patent ID')
            return
        
        patent = get_patent_by_id(patent_id)
        
        if not patent:
            self.send_error(HTTPStatus.NOT_FOUND, 'Patent not found')
            return
        
        # Convert patent to JSON serializable format
        patent_json = {
            'id': patent['patent_id'],
            'title': patent['title'],
            'abstract': patent['abstract'],
            'filing_date': patent['filing_date'],
            'issue_date': patent['issue_date'],
            'inventors': patent['inventors'],
            'assignee': patent['assignee'],
            'category': patent['category'],
            'full_text': patent['full_text']
        }
        
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(patent_json).encode('utf-8'))
    
    def process_includes(self, content):
        """Process includes in HTML content"""
        # Find all include placeholders
        include_pattern = r'<!-- INCLUDE:([a-zA-Z0-9_/.-]+) -->'
        matches = list(re.finditer(include_pattern, content))
        
        # Replace each include with its content
        for match in matches:
            include_path = match.group(1).strip()
            full_path = os.path.join(INCLUDES_DIR, include_path)
            
            try:
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        include_content = f.read()
                        content = content.replace(match.group(0), include_content)
                else:
                    print(f"Warning: Include file not found: {full_path}")
                    content = content.replace(match.group(0), f"<!-- Include not found: {include_path} -->")
            except Exception as e:
                print(f"Error processing include {include_path}: {str(e)}")
                content = content.replace(match.group(0), f"<!-- Error processing include: {include_path} -->")
        
        # Replace any patent ID placeholder if applicable
        if hasattr(self, 'patent_id'):
            content = content.replace('__PATENT_ID__', self.patent_id)
            
            # Add a script to set the patent ID in JavaScript
            patent_id_script = f"""
            <script>
                // Set patent ID from server
                window.patentId = "{self.patent_id}";
            </script>
            """
            
            # Insert the script at the end of the head section
            content = content.replace('</head>', f"{patent_id_script}</head>")
        
        return content


def run_server(port=PORT, host=HOST):
    """Run the HTTP server"""
    try:
        server_address = (host, port)
        httpd = http.server.HTTPServer(server_address, SEOPatentHandler)
        logger.info(f"Starting server on {host}:{port}...")
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {port} is already in use, attempting to stop the existing process")
            import subprocess
            try:
                # Try to kill the process using this port
                subprocess.run(f"fuser -k {port}/tcp", shell=True)
                logger.info("Killed existing process, retrying to start server...")
                time.sleep(2)  # Give some time for the port to be released
                # Retry starting the server
                server_address = (host, port)
                httpd = http.server.HTTPServer(server_address, SEOPatentHandler)
                logger.info(f"Starting server on {host}:{port}...")
                httpd.serve_forever()
            except Exception as retry_error:
                logger.error(f"Could not restart server: {str(retry_error)}")
                logger.error("Please stop the existing server process manually")
                sys.exit(1)
        else:
            logger.error(f"Error starting server: {str(e)}")
            logger.error(f"Exception details: {type(e).__name__}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Make sure demo patents exist in the database
        logger.info("Checking for demo patents in the database...")
        ensure_patents_exist()
        logger.info("Demo patents have been added to the database.")
        
        # Start the server
        run_server()
    except Exception as e:
        logger.error(f"Error starting the application: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)