# utils/helpers.py
import os
import re
import json
import datetime
from urllib.parse import urlparse

def get_project_path(project_name):
    """Convert project name to URL-safe path"""
    # Replace spaces and special characters with hyphens
    path = re.sub(r'[^a-zA-Z0-9]', '-', project_name.lower())
    # Remove multiple consecutive hyphens
    path = re.sub(r'-+', '-', path)
    # Remove leading/trailing hyphens
    path = path.strip('-')
    return path

def get_project_name_from_path(path):
    """Attempt to convert URL path back to project name"""
    from database.db_manager import get_projects
    
    # Get all projects
    projects = get_projects()
    
    # Try to find a matching path
    for project in projects:
        if get_project_path(project['name']) == path:
            return project['name']
    
    # If no match found, return the path as is
    return path

def format_date(date_string, input_format='%Y-%m-%d', output_format='%b %d, %Y'):
    """Format a date string"""
    if not date_string:
        return ""
    
    try:
        date_obj = datetime.datetime.strptime(date_string, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_string

def validate_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def clean_filename(filename):
    """Make a filename safe"""
    return re.sub(r'[^\w\.-]', '_', filename)

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def parse_csv(file_path, delimiter=','):
    """Simple CSV parser"""
    import csv
    
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error parsing CSV file: {e}")
        return []
    
    return data

def read_file(file_path):
    """Read a file as text"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""

def save_file(file_path, content):
    """Save content to a file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def json_serialize(obj):
    """Serialize object to JSON string"""
    return json.dumps(obj, ensure_ascii=False)

def json_deserialize(json_str):
    """Deserialize JSON string to object"""
    if not json_str:
        return {}
    return json.loads(json_str)

def render_template(template_name, **context):
    """Simple template renderer"""
    # Read the template file
    try:
        template_path = os.path.join('templates', template_name)
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        return f"Template not found: {template_name}"
    
    # Render base template if this extends one
    base_pattern = r'{%\s*extends\s+[\'"](.+?)[\'"]\s*%}'
    base_match = re.search(base_pattern, template_content)
    
    if base_match:
        base_template = base_match.group(1)
        try:
            base_path = os.path.join('templates', base_template)
            with open(base_path, 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            # Extract blocks from the current template
            blocks = {}
            block_pattern = r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}'
            for match in re.finditer(block_pattern, template_content, re.DOTALL):
                block_name, block_content = match.groups()
                blocks[block_name] = block_content
            
            # Replace block placeholders in the base template
            for block_name, block_content in blocks.items():
                base_block_pattern = r'{%\s*block\s+' + block_name + r'\s*%}.*?{%\s*endblock\s*%}'
                base_content = re.sub(base_block_pattern, block_content, base_content, flags=re.DOTALL)
            
            template_content = base_content
        except FileNotFoundError:
            return f"Base template not found: {base_template}"
    
    # Replace variables
    var_pattern = r'{{\s*(.+?)\s*}}'
    for match in re.finditer(var_pattern, template_content):
        var_name = match.group(1)
        
        # Handle nested attributes
        if '.' in var_name:
            parts = var_name.split('.')
            value = context.get(parts[0], {})
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part, '')
                else:
                    try:
                        value = getattr(value, part, '')
                    except:
                        value = ''
                        break
        else:
            value = context.get(var_name, '')
        
        template_content = template_content.replace(match.group(0), str(value))
    
    # Process conditionals
    if_pattern = r'{%\s*if\s+(.+?)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}'
    
    def evaluate_condition(condition, context):
        # Simple condition evaluation
        if ' and ' in condition:
            parts = condition.split(' and ')
            return all(evaluate_condition(part, context) for part in parts)
        elif ' or ' in condition:
            parts = condition.split(' or ')
            return any(evaluate_condition(part, context) for part in parts)
        elif condition.startswith('not '):
            return not evaluate_condition(condition[4:], context)
        else:
            # Handle comparisons
            if ' == ' in condition:
                var, val = condition.split(' == ')
                var = var.strip()
                val = val.strip().strip("'\"")
                return context.get(var, '') == val
            elif ' != ' in condition:
                var, val = condition.split(' != ')
                var = var.strip()
                val = val.strip().strip("'\"")
                return context.get(var, '') != val
            else:
                # Simple variable check
                return bool(context.get(condition.strip(), False))
    
    for match in re.finditer(if_pattern, template_content, re.DOTALL):
        condition, if_content, else_content = match.groups()
        else_content = else_content or ''
        
        if evaluate_condition(condition, context):
            replacement = if_content
        else:
            replacement = else_content
        
        template_content = template_content.replace(match.group(0), replacement)
    
    # Process loops
    for_pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'
    
    for match in re.finditer(for_pattern, template_content, re.DOTALL):
        item_name, collection_name, loop_content = match.groups()
        
        collection = context.get(collection_name, [])
        if not collection:
            template_content = template_content.replace(match.group(0), '')
            continue
        
        result = []
        for item in collection:
            # Create a new context for each iteration
            loop_context = context.copy()
            loop_context[item_name] = item
            
            # Replace variables in this iteration
            iteration_content = loop_content
            for var_match in re.finditer(var_pattern, loop_content):
                var_name = var_match.group(1)
                
                if var_name.startswith(item_name + '.'):
                    attr_name = var_name[len(item_name)+1:]
                    if isinstance(item, dict):
                        value = item.get(attr_name, '')
                    else:
                        value = getattr(item, attr_name, '')
                    
                    iteration_content = iteration_content.replace(var_match.group(0), str(value))
            
            result.append(iteration_content)
        
        template_content = template_content.replace(match.group(0), ''.join(result))
    
    # Return the rendered template
    return template_content
