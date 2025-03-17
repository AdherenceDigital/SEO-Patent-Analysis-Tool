#!/usr/bin/env python3

import os
import re
import sys
import json
import base64
import urllib.parse
import mimetypes
import http.server
from http import HTTPStatus
from urllib.parse import parse_qs

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
INCLUDES_DIR = os.path.join(STATIC_ROOT, 'includes')

# Default port
PORT = 8000

class SEOPatentHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for SEO Patent Analysis Tool"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Handle special routes
        if path == '/':
            path = '/index.html'
        elif path == '/patents':
            path = '/patents/index.html'
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
                    print(f"Include file not found: {full_path}")
                    content = content.replace(match.group(0), f"<!-- Include not found: {include_path} -->")
            except Exception as e:
                print(f"Error processing include {include_path}: {e}")
                content = content.replace(match.group(0), f"<!-- Error processing include: {include_path} -->")
        
        return content


def run_server(port=PORT):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, SEOPatentHandler)
    print(f"Starting server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")


if __name__ == "__main__":
    run_server()
