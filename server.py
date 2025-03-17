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
from database.db_manager import get_patents, get_patent_by_id

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
INCLUDES_DIR = os.path.join(STATIC_ROOT, 'includes')

# Default port
PORT = int(os.environ.get('PORT', 8000))

class SEOPatentHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for SEO Patent Analysis Tool"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # Handle API endpoints
        if path.startswith('/api/'):
            self.handle_api(path, query_params)
            return
        
        # Handle special routes
        if path == '/':
            path = '/index.html'
        elif path == '/patents':
            path = '/patents/index.html'
        elif path.startswith('/patents/') and len(path.split('/')) == 3 and not path.startswith('/patents/view/'):
            # Handle /patents/[patent-id]
            patent_id = path.split('/')[2]
            # Pass the patent ID as a query parameter
            self.patent_id = patent_id  # Store for use in process_includes
            path = '/patents/view/index.html'
        elif path == '/dashboard':
            path = '/dashboard.html'
        
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
            with open(file_path, 'rb') as f:
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', content_type)
                self.send_header('X-Robots-Tag', 'noindex, nofollow')
                self.end_headers()
                
                # For HTML files, process includes
                if ext == '.html':
                    content = f.read().decode('utf-8')
                    content = self.process_includes(content)
                    self.wfile.write(content.encode('utf-8'))
                else:
                    # For non-HTML files, send as is
                    self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return
    
    def handle_api(self, path, query_params):
        """Handle API requests"""
        if path == '/api/patents':
            self.handle_api_patents(query_params)
        elif path == '/api/patent':
            self.handle_api_patent(query_params)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'API endpoint not found')
    
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


def run_server(port=PORT):
    """Run the HTTP server"""
    try:
        server_address = ('', port)
        httpd = http.server.HTTPServer(server_address, SEOPatentHandler)
        logger.info(f"Starting server on port {port}...")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    run_server()
