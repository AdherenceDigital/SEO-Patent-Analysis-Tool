# config.py
import os

# Application configuration
APP_NAME = 'SEO Patent Analysis Tool'
VERSION = '1.0.0'
DEBUG = True

# Database configuration
DATABASE_PATH = 'database/seo_tool.db'

# File uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {
    'csv': ['text/csv', 'application/vnd.ms-excel'],
    'xml': ['text/xml', 'application/xml'],
    'zip': ['application/zip', 'application/x-zip-compressed'],
}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# Google API
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
GOOGLE_CUSTOM_SEARCH_ENGINE_ID = os.environ.get('GOOGLE_CUSTOM_SEARCH_ENGINE_ID', '')

# Google Search Console API
GOOGLE_CREDENTIALS_FILE = 'google_credentials.json'

# Patent API
PATENT_API_ENDPOINT = 'https://patents.google.com/api/search'

# GitHub settings
GITHUB_REPO = 'SEO-Patent-Analysis-Tool'
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'AdherenceDigital')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Server settings
PORT = 8000
HOST = '0.0.0.0'

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
