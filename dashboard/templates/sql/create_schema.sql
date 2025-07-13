-- Database Schema Creation for Code Intelligence Dashboard
-- 
-- This file defines the complete database schema including tables,
-- indexes, and constraints for the code intelligence system.
-- 
-- Last Updated: 2025-01-27 15:30:00

-- Files table - stores file-level metadata and metrics
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    file_type TEXT NOT NULL,
    complexity INTEGER DEFAULT 0,
    complexity_level TEXT DEFAULT 'low',
    lines_of_code INTEGER DEFAULT 0,
    classes_count INTEGER DEFAULT 0,
    functions_count INTEGER DEFAULT 0,
    imports_count INTEGER DEFAULT 0,
    pydantic_models_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classes table - stores class definitions and metadata
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    domain TEXT NOT NULL,
    class_type TEXT DEFAULT 'class',
    line_number INTEGER DEFAULT 1,
    methods_count INTEGER DEFAULT 0,
    is_abstract BOOLEAN DEFAULT FALSE,
    is_pydantic_model BOOLEAN DEFAULT FALSE,
    base_classes TEXT DEFAULT '[]',
    decorators TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
);

-- Functions table - stores function and method definitions
CREATE TABLE IF NOT EXISTS functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    class_id INTEGER,
    file_path TEXT NOT NULL,
    function_type TEXT DEFAULT 'function',
    line_number INTEGER DEFAULT 1,
    parameters_count INTEGER DEFAULT 0,
    parameters TEXT DEFAULT '[]',
    return_type TEXT,
    is_async BOOLEAN DEFAULT FALSE,
    is_generator BOOLEAN DEFAULT FALSE,
    decorators TEXT DEFAULT '[]',
    complexity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE SET NULL
);

-- Relationships table - stores relationships between code entities
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    source_name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Variables table - stores variable definitions and usage
CREATE TABLE IF NOT EXISTS variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    class_id INTEGER,
    function_id INTEGER,
    variable_type TEXT,
    scope TEXT DEFAULT 'local',
    line_number INTEGER DEFAULT 1,
    is_constant BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE SET NULL,
    FOREIGN KEY (function_id) REFERENCES functions (id) ON DELETE SET NULL
);

-- Imports table - stores import statements and dependencies
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    import_type TEXT NOT NULL, -- 'import' or 'from'
    imported_names TEXT DEFAULT '[]',
    alias TEXT,
    line_number INTEGER DEFAULT 1,
    is_standard_library BOOLEAN DEFAULT FALSE,
    is_third_party BOOLEAN DEFAULT FALSE,
    is_local BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
);
