# Patent SEO Tool Development Guidelines

## Run Commands
- Run server: `python app.py`
- Run server with custom port: `HOST=127.0.0.1 PORT=8080 python app.py`
- Run test: `python scripts/test_patent_import.py`
- Import patents: `python scripts/import_patents.py [input_file]`
- Update assignees: `python scripts/update_patent_assignees.py`

## Style Guidelines
- Imports: standard library → third-party → local modules
- Naming: snake_case for functions/variables, PascalCase for classes
- Constants: UPPERCASE
- Private methods: prefix with underscore (_method_name)
- Documentation: Google-style docstrings
- Error handling: Use specific try/except with detailed error messages
- Return error dictionaries with descriptive messages for API endpoints
- Database operations: Use parameterized queries for safety
- Use the existing database connection pattern: get → use → close

## Project Organization
- Routes in routes/ directory
- Database operations in database/db_manager.py
- Patent API utilities in utils/patent_api/
- HTML templates in static/ directory
- Use render_template from utils.helpers for HTML rendering