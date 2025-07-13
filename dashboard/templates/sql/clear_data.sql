-- Database Cleanup Operations for Code Intelligence Dashboard
-- 
-- This file contains SQL commands for clearing/resetting the database.
-- Used during population processes and maintenance operations.
-- 
-- Last Updated: 2025-01-27 15:30:00

-- Clear all data while preserving schema (in dependency order)
DELETE FROM relationships;
DELETE FROM imports;
DELETE FROM variables;
DELETE FROM functions;
DELETE FROM classes;
DELETE FROM files;

-- Reset auto-increment counters
DELETE FROM sqlite_sequence WHERE name IN ('files', 'classes', 'functions', 'relationships', 'variables', 'imports');
