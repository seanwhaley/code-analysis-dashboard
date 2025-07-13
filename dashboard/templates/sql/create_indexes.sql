-- Database Indexes for Code Intelligence Dashboard
-- 
-- This file defines performance optimization indexes for efficient querying.
-- These indexes support the most common query patterns in the dashboard.
-- 
-- Last Updated: 2025-01-27 15:30:00

-- Files table indexes
CREATE INDEX IF NOT EXISTS idx_files_domain ON files (domain);
CREATE INDEX IF NOT EXISTS idx_files_type ON files (file_type);
CREATE INDEX IF NOT EXISTS idx_files_complexity ON files (complexity);
CREATE INDEX IF NOT EXISTS idx_files_complexity_level ON files (complexity_level);
CREATE INDEX IF NOT EXISTS idx_files_lines ON files (lines_of_code);
CREATE INDEX IF NOT EXISTS idx_files_path ON files (path);

-- Classes table indexes  
CREATE INDEX IF NOT EXISTS idx_classes_file_id ON classes (file_id);
CREATE INDEX IF NOT EXISTS idx_classes_name ON classes (name);
CREATE INDEX IF NOT EXISTS idx_classes_type ON classes (class_type);
CREATE INDEX IF NOT EXISTS idx_classes_pydantic ON classes (is_pydantic_model);
CREATE INDEX IF NOT EXISTS idx_classes_domain ON classes (domain);

-- Functions table indexes
CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions (file_id);
CREATE INDEX IF NOT EXISTS idx_functions_class_id ON functions (class_id);
CREATE INDEX IF NOT EXISTS idx_functions_name ON functions (name);
CREATE INDEX IF NOT EXISTS idx_functions_type ON functions (function_type);
CREATE INDEX IF NOT EXISTS idx_functions_async ON functions (is_async);

-- Relationships table indexes
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships (relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_file ON relationships (file_path);

-- Variables table indexes
CREATE INDEX IF NOT EXISTS idx_variables_file_id ON variables (file_id);
CREATE INDEX IF NOT EXISTS idx_variables_class_id ON variables (class_id);
CREATE INDEX IF NOT EXISTS idx_variables_function_id ON variables (function_id);
CREATE INDEX IF NOT EXISTS idx_variables_name ON variables (name);
CREATE INDEX IF NOT EXISTS idx_variables_scope ON variables (scope);

-- Imports table indexes
CREATE INDEX IF NOT EXISTS idx_imports_file_id ON imports (file_id);
CREATE INDEX IF NOT EXISTS idx_imports_module ON imports (module_name);
CREATE INDEX IF NOT EXISTS idx_imports_type ON imports (import_type);
CREATE INDEX IF NOT EXISTS idx_imports_standard ON imports (is_standard_library);
CREATE INDEX IF NOT EXISTS idx_imports_third_party ON imports (is_third_party);
CREATE INDEX IF NOT EXISTS idx_imports_local ON imports (is_local);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_files_domain_type ON files (domain, file_type);
CREATE INDEX IF NOT EXISTS idx_classes_file_type ON classes (file_id, class_type);
CREATE INDEX IF NOT EXISTS idx_functions_file_class ON functions (file_id, class_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source_target ON relationships (source_type, target_type);
