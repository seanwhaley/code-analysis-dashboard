#!/usr/bin/env python3
"""
Code Analyzer for USASpending Code Intelligence Dashboard

**Last Updated:** 2025-07-10 15:45:00

This module analyzes the actual codebase and populates the database with real code structure data.
It performs AST analysis on Python files and basic analysis on other file types.
"""

import ast
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add the parent directory to sys.path so we can import the database module
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

try:
    from sqlite_backend import DocumentationDatabase
except ImportError as e:
    print(f"❌ Failed to import sqlite_backend: {e}")
    print("   Make sure you're running from the correct directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('code_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes codebase and populates database with real structure data."""
    
    def __init__(self, project_root: Path, db_path: Optional[str] = None):
        """Initialize the code analyzer."""
        self.project_root = Path(project_root)
        self.db_path = db_path or str(self.project_root / "api" / "documentation.db")
        self.db = DocumentationDatabase(self.db_path)
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'classes_found': 0,
            'functions_found': 0,
            'imports_found': 0,
            'decorators_found': 0,
            'variables_found': 0,
            'errors': 0
        }
        
        logger.info(f"🔍 Initialized CodeAnalyzer for {self.project_root}")
        logger.info(f"📊 Database path: {self.db_path}")
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project and populate the database."""
        logger.info("🚀 Starting project analysis...")
        
        try:
            # Clear existing data
            logger.info("🧹 Clearing existing database data...")
            self.db.clear_all_data()
            
            # Analyze all files
            self._analyze_directory(self.project_root)
            
            # Update domain statistics
            self._update_domain_statistics()
            
            # Generate final report
            final_stats = self.db.get_system_stats()
            final_stats.update(self.stats)
            
            logger.info("✅ Project analysis completed successfully!")
            logger.info(f"📊 Final Statistics: {final_stats}")
            
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Project analysis failed: {e}")
            self.stats['errors'] += 1
            raise
    
    def _analyze_directory(self, directory: Path) -> None:
        """Recursively analyze all files in a directory."""
        try:
            # Skip certain directories
            skip_dirs = {'.git', '__pycache__', '.vscode', 'node_modules', '.pytest_cache'}
            
            for item in directory.iterdir():
                if item.is_dir() and item.name not in skip_dirs:
                    self._analyze_directory(item)
                elif item.is_file():
                    self._analyze_file(item)
                    
        except PermissionError:
            logger.warning(f"⚠️ Permission denied accessing {directory}")
        except Exception as e:
            logger.error(f"❌ Error analyzing directory {directory}: {e}")
            self.stats['errors'] += 1
    
    def _analyze_file(self, file_path: Path) -> Optional[int]:
        """Analyze a single file and return file ID if successful."""
        try:
            # Skip certain file types
            skip_extensions = {'.pyc', '.pyo', '.db', '.log', '.tmp'}
            if file_path.suffix in skip_extensions:
                return None
            
            # Calculate relative path from project root
            try:
                relative_path = file_path.relative_to(self.project_root)
            except ValueError:
                logger.warning(f"⚠️ File {file_path} is outside project root")
                return None
            
            logger.debug(f"🔍 Analyzing file: {relative_path}")
            
            # Get basic file info
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"⚠️ Could not read {file_path}: {e}")
                content = ""
            
            # Count lines
            lines = len(content.splitlines()) if content else 0
            
            # Determine domain based on path
            domain = self._determine_domain(relative_path)
            
            # Basic file record
            file_record = {
                'name': file_path.name,
                'path': str(relative_path),
                'domain': domain,
                'complexity': 0,
                'classes': 0,
                'functions': 0,
                'lines': lines,
                'pydantic_models_count': 0,
                'file_type': self._get_file_type(file_path)
            }
            
            # Language-specific analysis
            if file_path.suffix == '.py':
                file_record.update(self._analyze_python_file(file_path, content))
            elif file_path.suffix in ['.js', '.ts']:
                file_record.update(self._analyze_javascript_file(file_path, content))
            elif file_path.suffix in ['.html', '.htm']:
                file_record.update(self._analyze_html_file(file_path, content))
            elif file_path.suffix in ['.css']:
                file_record.update(self._analyze_css_file(file_path, content))
            elif file_path.suffix in ['.json']:
                file_record.update(self._analyze_json_file(file_path, content))
            
            # Insert file record into database
            file_id = self._insert_file_record(file_record)
            
            if file_id:
                self.stats['files_processed'] += 1
                logger.debug(f"✅ Processed {relative_path} (ID: {file_id})")
            
            return file_id
            
        except Exception as e:
            logger.error(f"❌ Error analyzing file {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def _analyze_python_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Python file using AST."""
        analysis = {
            'complexity': 0,
            'classes': 0,
            'functions': 0,
            'pydantic_models_count': 0
        }
        
        if not content.strip():
            return analysis
        
        try:
            tree = ast.parse(content)
            
            # Get relative path for database storage
            relative_path = file_path.relative_to(self.project_root)
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes'] += 1
                    self._analyze_class(node, file_path, relative_path)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    analysis['functions'] += 1
                    self._analyze_function(node, file_path, relative_path)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._analyze_import(node, file_path, relative_path)
            
            # Calculate complexity (simple cyclomatic complexity)
            analysis['complexity'] = self._calculate_complexity(tree)
            
            # Check for Pydantic models
            analysis['pydantic_models_count'] = self._count_pydantic_models(tree, content)
            
        except SyntaxError as e:
            logger.warning(f"⚠️ Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error parsing Python file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return analysis
    
    def _analyze_class(self, node: ast.ClassDef, file_path: Path, relative_path: Path) -> None:
        """Analyze a Python class."""
        try:
            # Determine class type
            class_type = "class"
            if any(isinstance(decorator, ast.Name) and decorator.id == "dataclass" 
                   for decorator in node.decorator_list):
                class_type = "dataclass"
            elif any(base.id in ["BaseModel", "Enum"] if isinstance(base, ast.Name) else False 
                     for base in node.bases):
                class_type = "pydantic" if any(base.id == "BaseModel" if isinstance(base, ast.Name) else False 
                                               for base in node.bases) else "enum"
            
            # Count methods and properties
            methods_count = 0
            properties_count = 0
            
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods_count += 1
                    if any(isinstance(decorator, ast.Name) and decorator.id == "property" 
                           for decorator in item.decorator_list):
                        properties_count += 1
            
            # Get base classes
            base_classes = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_classes.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_classes.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else str(base.attr))
            
            # Get decorators
            decorators = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            # Create class record
            class_record = {
                'name': node.name,
                'file_path': str(relative_path),
                'line_number': node.lineno,
                'end_line_number': getattr(node, 'end_lineno', node.lineno),
                'domain': self._determine_domain(relative_path),
                'class_type': class_type,
                'methods_count': methods_count,
                'properties_count': properties_count,
                'base_classes': json.dumps(base_classes),
                'decorators': json.dumps(decorators),
                'docstring': docstring,
                'is_abstract': any("Abstract" in base for base in base_classes),
                'is_public': not node.name.startswith('_'),
                'complexity_score': self._calculate_node_complexity(node)
            }
            
            self._insert_class_record(class_record, file_path)
            self.stats['classes_found'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error analyzing class {node.name} in {file_path}: {e}")
            self.stats['errors'] += 1
    
    def _analyze_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                         file_path: Path, relative_path: Path, class_id: Optional[int] = None) -> None:
        """Analyze a Python function or method."""
        try:
            # Determine function type
            function_type = "function"
            if class_id:
                if node.name == "__init__":
                    function_type = "constructor"
                elif any(isinstance(decorator, ast.Name) and decorator.id in ["staticmethod", "classmethod", "property"] 
                         for decorator in node.decorator_list):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id in ["staticmethod", "classmethod", "property"]:
                            function_type = decorator.id
                            break
                else:
                    function_type = "method"
            
            # Get parameters
            parameters = []
            for arg in node.args.args:
                param_info = arg.arg
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        param_info += f": {arg.annotation.id}"
                    elif isinstance(arg.annotation, ast.Constant):
                        param_info += f": {arg.annotation.value}"
                parameters.append(param_info)
            
            # Get return type
            return_type = None
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    return_type = node.returns.id
                elif isinstance(node.returns, ast.Constant):
                    return_type = str(node.returns.value)
            
            # Get decorators
            decorators = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            # Analyze function calls and variables used
            calls_made = []
            variables_used = []
            
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    calls_made.append(child.func.id)
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    variables_used.append(child.id)
            
            # Create function record
            function_record = {
                'name': node.name,
                'file_path': str(relative_path),
                'line_number': node.lineno,
                'end_line_number': getattr(node, 'end_lineno', node.lineno),
                'function_type': function_type,
                'parameters_count': len(parameters),
                'parameters': json.dumps(parameters),
                'return_type': return_type,
                'decorators': json.dumps(decorators),
                'docstring': docstring,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'is_public': not node.name.startswith('_'),
                'complexity_score': self._calculate_node_complexity(node),
                'calls_made': json.dumps(list(set(calls_made))[:10]),  # Limit to avoid huge data
                'variables_used': json.dumps(list(set(variables_used))[:10])
            }
            
            self._insert_function_record(function_record, file_path, class_id)
            self.stats['functions_found'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error analyzing function {node.name} in {file_path}: {e}")
            self.stats['errors'] += 1
    
    def _analyze_import(self, node: Union[ast.Import, ast.ImportFrom], 
                       file_path: Path, relative_path: Path) -> None:
        """Analyze import statements."""
        try:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_record = {
                        'module_name': alias.name,
                        'import_type': 'import',
                        'imported_names': json.dumps([alias.name]),
                        'alias': alias.asname,
                        'line_number': node.lineno,
                        'is_standard_library': self._is_standard_library(alias.name),
                        'is_third_party': self._is_third_party(alias.name),
                        'is_local': self._is_local_import(alias.name)
                    }
                    self._insert_import_record(import_record, file_path)
                    
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ''
                imported_names = [alias.name for alias in node.names]
                
                import_record = {
                    'module_name': module_name,
                    'import_type': 'from_import' if node.level == 0 else 'relative_import',
                    'imported_names': json.dumps(imported_names),
                    'alias': None,
                    'line_number': node.lineno,
                    'is_standard_library': self._is_standard_library(module_name),
                    'is_third_party': self._is_third_party(module_name),
                    'is_local': self._is_local_import(module_name)
                }
                self._insert_import_record(import_record, file_path)
            
            self.stats['imports_found'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error analyzing import in {file_path}: {e}")
            self.stats['errors'] += 1
    
    def _analyze_javascript_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Basic analysis of JavaScript files."""
        analysis = {
            'complexity': 0,
            'classes': 0,
            'functions': 0
        }
        
        # Count classes (class keyword)
        analysis['classes'] = len(re.findall(r'\bclass\s+\w+', content))
        
        # Count functions (function keyword, arrow functions, method definitions)
        function_patterns = [
            r'\bfunction\s+\w+',           # function declarations
            r'\w+\s*:\s*function',         # object methods
            r'\w+\s*=>\s*{',              # arrow functions
            r'async\s+function\s+\w+',     # async functions
        ]
        
        for pattern in function_patterns:
            analysis['functions'] += len(re.findall(pattern, content))
        
        # Simple complexity based on control flow keywords
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', 'try']
        analysis['complexity'] = sum(len(re.findall(rf'\b{keyword}\b', content)) 
                                   for keyword in complexity_keywords)
        
        return analysis
    
    def _analyze_html_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Basic analysis of HTML files."""
        analysis = {
            'complexity': 0,
            'classes': 0,
            'functions': 0
        }
        
        # Count script tags and inline JavaScript
        script_tags = len(re.findall(r'<script[^>]*>', content, re.IGNORECASE))
        inline_js = len(re.findall(r'onclick=|onload=|onchange=', content, re.IGNORECASE))
        
        analysis['complexity'] = script_tags + inline_js
        
        return analysis
    
    def _analyze_css_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Basic analysis of CSS files."""
        analysis = {
            'complexity': 0,
            'classes': 0,
            'functions': 0
        }
        
        # Count CSS rules
        css_rules = len(re.findall(r'{[^}]*}', content))
        analysis['complexity'] = css_rules
        
        return analysis
    
    def _analyze_json_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Basic analysis of JSON files."""
        analysis = {
            'complexity': 0,
            'classes': 0,
            'functions': 0
        }
        
        try:
            data = json.loads(content)
            # Complexity based on nesting depth and number of keys
            analysis['complexity'] = self._json_complexity(data)
        except json.JSONDecodeError:
            pass
        
        return analysis
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                               ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate complexity for a specific node."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _count_pydantic_models(self, tree: ast.AST, content: str) -> int:
        """Count Pydantic models in the file."""
        count = 0
        
        # Check if BaseModel is imported
        has_basemodel = 'BaseModel' in content
        
        if has_basemodel:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if (isinstance(base, ast.Name) and base.id == 'BaseModel') or \
                           (isinstance(base, ast.Attribute) and base.attr == 'BaseModel'):
                            count += 1
                            break
        
        return count
    
    def _determine_domain(self, path: Path) -> str:
        """Determine the domain/layer based on file path."""
        path_str = str(path).lower()
        
        if 'api' in path_str or 'server' in path_str:
            return 'api'
        elif 'component' in path_str or 'assets' in path_str or path_str.endswith('.html'):
            return 'presentation'
        elif 'src' in path_str and ('service' in path_str or 'business' in path_str):
            return 'application'
        elif 'model' in path_str or 'entity' in path_str:
            return 'domain'
        elif 'database' in path_str or 'db' in path_str or 'repo' in path_str:
            return 'infrastructure'
        elif 'test' in path_str:
            return 'testing'
        elif 'config' in path_str or 'settings' in path_str:
            return 'configuration'
        elif 'doc' in path_str or 'readme' in path_str:
            return 'documentation'
        else:
            return 'utility'
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type based on extension."""
        extension = file_path.suffix.lower()
        
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bat': 'batch',
            '.ps1': 'powershell'
        }
        
        return type_map.get(extension, 'unknown')
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is from Python standard library."""
        # Basic check for common standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 'logging', 'datetime', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 'operator', 're',
            'math', 'random', 'uuid', 'urllib', 'http', 'asyncio',
            'sqlite3', 'csv', 'xml', 'html', 'email', 'base64'
        }
        
        base_module = module_name.split('.')[0] if module_name else ''
        return base_module in stdlib_modules
    
    def _is_third_party(self, module_name: str) -> bool:
        """Check if module is third-party."""
        if not module_name:
            return False
            
        # Common third-party modules
        third_party_modules = {
            'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'alembic',
            'requests', 'httpx', 'aiohttp', 'flask', 'django',
            'pandas', 'numpy', 'matplotlib', 'pytest', 'click'
        }
        
        base_module = module_name.split('.')[0]
        return base_module in third_party_modules
    
    def _is_local_import(self, module_name: str) -> bool:
        """Check if import is local to the project."""
        if not module_name:
            return True
        
        return not (self._is_standard_library(module_name) or self._is_third_party(module_name))
    
    def _json_complexity(self, obj: Any, depth: int = 0) -> int:
        """Calculate complexity of JSON structure."""
        if depth > 10:  # Prevent infinite recursion
            return 1
        
        if isinstance(obj, dict):
            return 1 + sum(self._json_complexity(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return 1 + sum(self._json_complexity(item, depth + 1) for item in obj[:5])  # Limit for performance
        else:
            return 1
    
    def _insert_file_record(self, file_data: Dict[str, Any]) -> Optional[int]:
        """Insert file record into database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO files (name, path, domain, complexity, classes, functions, 
                                     lines, pydantic_models_count, file_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_data['name'],
                    file_data['path'],
                    file_data['domain'],
                    file_data['complexity'],
                    file_data['classes'],
                    file_data['functions'],
                    file_data['lines'],
                    file_data['pydantic_models_count'],
                    file_data['file_type']
                ))
                
                file_id = cursor.lastrowid
                conn.commit()
                return file_id
                
        except Exception as e:
            logger.error(f"❌ Error inserting file record: {e}")
            return None
    
    def _insert_class_record(self, class_data: Dict[str, Any], file_path: Path) -> Optional[int]:
        """Insert class record into database."""
        try:
            # Get file_id
            file_id = self._get_file_id(file_path)
            if not file_id:
                return None
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO classes (name, file_id, file_path, line_number, end_line_number,
                                       domain, class_type, methods_count, properties_count,
                                       base_classes, decorators, docstring, is_abstract,
                                       is_public, complexity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    class_data['name'],
                    file_id,
                    class_data['file_path'],
                    class_data['line_number'],
                    class_data['end_line_number'],
                    class_data['domain'],
                    class_data['class_type'],
                    class_data['methods_count'],
                    class_data['properties_count'],
                    class_data['base_classes'],
                    class_data['decorators'],
                    class_data['docstring'],
                    class_data['is_abstract'],
                    class_data['is_public'],
                    class_data['complexity_score']
                ))
                
                class_id = cursor.lastrowid
                conn.commit()
                return class_id
                
        except Exception as e:
            logger.error(f"❌ Error inserting class record: {e}")
            return None
    
    def _insert_function_record(self, func_data: Dict[str, Any], file_path: Path, class_id: Optional[int] = None) -> Optional[int]:
        """Insert function record into database."""
        try:
            # Get file_id
            file_id = self._get_file_id(file_path)
            if not file_id:
                return None
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO functions (name, file_id, class_id, file_path, line_number,
                                         end_line_number, function_type, parameters_count,
                                         parameters, return_type, decorators, docstring,
                                         is_async, is_public, complexity_score, calls_made,
                                         variables_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    func_data['name'],
                    file_id,
                    class_id,
                    func_data['file_path'],
                    func_data['line_number'],
                    func_data['end_line_number'],
                    func_data['function_type'],
                    func_data['parameters_count'],
                    func_data['parameters'],
                    func_data['return_type'],
                    func_data['decorators'],
                    func_data['docstring'],
                    func_data['is_async'],
                    func_data['is_public'],
                    func_data['complexity_score'],
                    func_data['calls_made'],
                    func_data['variables_used']
                ))
                
                function_id = cursor.lastrowid
                conn.commit()
                return function_id
                
        except Exception as e:
            logger.error(f"❌ Error inserting function record: {e}")
            return None
    
    def _insert_import_record(self, import_data: Dict[str, Any], file_path: Path) -> Optional[int]:
        """Insert import record into database."""
        try:
            # Get file_id
            file_id = self._get_file_id(file_path)
            if not file_id:
                return None
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO imports (file_id, module_name, import_type, imported_names,
                                       alias, line_number, is_standard_library, is_third_party,
                                       is_local)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    import_data['module_name'],
                    import_data['import_type'],
                    import_data['imported_names'],
                    import_data['alias'],
                    import_data['line_number'],
                    import_data['is_standard_library'],
                    import_data['is_third_party'],
                    import_data['is_local']
                ))
                
                import_id = cursor.lastrowid
                conn.commit()
                return import_id
                
        except Exception as e:
            logger.error(f"❌ Error inserting import record: {e}")
            return None
    
    def _get_file_id(self, file_path: Path) -> Optional[int]:
        """Get file ID from database."""
        try:
            relative_path = file_path.relative_to(self.project_root)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM files WHERE path = ?", (str(relative_path),))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"❌ Error getting file ID: {e}")
            return None
    
    def _update_domain_statistics(self) -> None:
        """Update domain statistics in the database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing domain stats
                cursor.execute("DELETE FROM domains")
                
                # Calculate new domain stats
                cursor.execute("""
                    INSERT INTO domains (name, file_count, model_count, avg_complexity, total_lines)
                    SELECT 
                        f.domain,
                        COUNT(DISTINCT f.id) as file_count,
                        COUNT(DISTINCT m.id) as model_count,
                        COALESCE(AVG(f.complexity), 0) as avg_complexity,
                        COALESCE(SUM(f.lines), 0) as total_lines
                    FROM files f
                    LEFT JOIN models m ON f.id = m.file_id
                    GROUP BY f.domain
                """)
                
                conn.commit()
                logger.info("✅ Domain statistics updated")
                
        except Exception as e:
            logger.error(f"❌ Error updating domain statistics: {e}")


def main() -> None:
    """Main function to run the code analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze codebase and populate database")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--db-path", help="Database file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    project_root = Path(args.project_root).resolve()
    analyzer = CodeAnalyzer(project_root, args.db_path)
    
    try:
        # Run analysis
        print("🚀 Starting codebase analysis...")
        results = analyzer.analyze_project()
        
        print("✅ Analysis completed successfully!")
        print(f"📊 Results: {results}")
        
        # Generate summary report
        report_path = project_root / "temp" / "code_analysis_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Report saved to: {report_path}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
