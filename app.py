# app.py
import os
import json
import mimetypes
import sqlite3
import traceback
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from database.db_manager import get_db, init_db
from utils.helpers import render_template, get_project_path, get_project_name_from_path
from config import HOST, PORT, DEBUG

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Ensure database exists
if not os.path.exists('database/seo_tool.db'):
    init_db()

# Simple router
def application(environ, start_response):
    """WSGI application entry point"""
    path = environ.get('PATH_INFO', '').lstrip('/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Parse query parameters
    query_string = environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    
    # Parse form data if it's a POST request
    form_data = {}
    if method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0
        
        request_body = environ['wsgi.input'].read(request_body_size)
        if request_body:
            try:
                # Try to parse as JSON
                if environ.get('CONTENT_TYPE', '').startswith('application/json'):
                    form_data = json.loads(request_body)
                # Otherwise parse as form data
                else:
                    form_data = parse_qs(request_body.decode('utf-8'))
                    # Convert single item lists to values
                    for key, value in form_data.items():
                        if isinstance(value, list) and len(value) == 1:
                            form_data[key] = value[0]
            except:
                pass
    
    # Set default response
    status = '200 OK'
    response_body = ''
    content_type = 'text/html'
    
    try:
        # Handle static files
        if path.startswith('static/'):
            try:
                file_path = path[7:]  # Remove 'static/' prefix
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                
                with open(os.path.join('static', file_path), 'rb') as f:
                    response_body = f.read()
                
                content_type = mime_type
            except FileNotFoundError:
                status = '404 Not Found'
                response_body = 'File not found'
                content_type = 'text/plain'
        
        # Handle main routes
        elif not path or path == 'dashboard':
            # Main dashboard - list all projects
            from routes.dashboard import handle_dashboard
            response_body = handle_dashboard(method, query_params, form_data)
        
        elif path.startswith('patents'):
            # Patent routes
            from routes.patents import handle_patents
            parts = path.split('/')
            response_body = handle_patents(method, parts, query_params, form_data)
        
        # Project-specific routes - assumed if first part is not a known route
        elif len(path.split('/')) >= 1 and not path.split('/')[0] in ['static', 'dashboard', 'patents']:
            from routes.project import handle_project
            parts = path.split('/')
            response_body = handle_project(method, parts, query_params, form_data)
        
        # 404 for any other routes
        else:
            status = '404 Not Found'
            response_body = render_template('404.html', 
                                           title='Page Not Found', 
                                           message='The page you requested does not exist.')
    
    except Exception as e:
        # Handle exceptions
        if DEBUG:
            status = '500 Internal Server Error'
            error_details = traceback.format_exc()
            response_body = f"<h1>Internal Server Error</h1><pre>{error_details}</pre>"
        else:
            status = '500 Internal Server Error'
            response_body = render_template('500.html', 
                                           title='Server Error', 
                                           message='An internal server error occurred.')
    
    # Set headers
    headers = [('Content-Type', content_type)]
    
    # Send response
    start_response(status, headers)
    
    # Convert response to bytes if it's a string
    if isinstance(response_body, str):
        response_body = response_body.encode('utf-8')
    
    return [response_body]

# Main entry point to run the server
if __name__ == '__main__':
    print(f"Starting server on {HOST}:{PORT}...")
    httpd = make_server(HOST, PORT, application)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
