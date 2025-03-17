# SEO Patent Analysis Tool

An advanced SEO analysis tool that analyzes websites from the perspective of Google patents, providing specific optimization recommendations based on patent insights.

## Features

- Patent retrieval and analysis from Google Patents API
- Import and analysis of data from:
  - Screaming Frog crawls
  - Ahrefs CSV files
  - Google Search Console
- Advanced SEO analysis based on Google patents
- Internal link optimization recommendations
- Historical analysis and comparison
- Visualization of site architecture and improvements

## Project Structure

The application follows a modular design with clear separation of concerns:

- `/dashboard` - Main project overview
- `/patents` - Patent listing and details
- `/[project-name]/dashboard` - Project-specific dashboard
- `/[project-name]/ahrefs` - Ahrefs data analysis
- `/[project-name]/search-console` - Search Console data
- `/[project-name]/Screaming Frog` - Screaming Frog data
- `/[project-name]/patent-analysis/[patent-id]` - Patent-specific analysis

## Technology Stack

- Backend: Python
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Deployment: Hetzner Server
- Version Control: GitHub

## Setup and Installation

1. Clone the repository
2. Install required dependencies: `pip install -r requirements.txt`
3. Initialize the database: `python init_db.py`
4. Run the application: `python app.py`

## Development Guidelines

- Each script/page should be under 500 lines
- Use templates for consistency across the application
- Document new functionality with README.md files
- Follow modular design principles for easy extension
