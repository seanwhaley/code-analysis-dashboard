#!/usr/bin/env python3
"""
Database Schema Manager

This module provides centralized database schema management operations
including table creation, index creation, and data clearing operations.
All SQL commands are externalized to separate .sql files for maintainability.

Last Updated: 2025-01-27 15:30:00
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from dashboard.templates.sql_template_manager import SQLTemplateManager

logger = logging.getLogger(__name__)


class DatabaseSchemaManager:
    """
    Manages database schema operations using externalized SQL files.

    This class provides methods for creating tables, indexes, and performing
    maintenance operations while keeping SQL separated from Python code.
    """

    def __init__(self, db_path: str, sql_template_dir: Optional[Path] = None) -> None:
        """
        Initialize the database schema manager.

        Args:
            db_path: Path to the SQLite database file
            sql_template_dir: Optional custom SQL template directory
        """
        self.db_path = db_path
        self.sql_manager = SQLTemplateManager(sql_template_dir)

    def create_tables(self) -> None:
        """
        Create all database tables using the schema SQL file.

        Raises:
            sqlite3.Error: If database operations fail
            FileNotFoundError: If schema SQL file is not found
        """
        try:
            schema_sql = self.sql_manager.render_sql_template("create_schema")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Execute the schema creation SQL
                cursor.executescript(schema_sql)
                conn.commit()

            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def create_indexes(self) -> None:
        """
        Create all performance indexes using the indexes SQL file.

        Raises:
            sqlite3.Error: If database operations fail
            FileNotFoundError: If indexes SQL file is not found
        """
        try:
            indexes_sql = self.sql_manager.render_sql_template("create_indexes")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Execute the index creation SQL
                cursor.executescript(indexes_sql)
                conn.commit()

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise

    def clear_data(self) -> None:
        """
        Clear all data from the database using the clear data SQL file.

        Raises:
            sqlite3.Error: If database operations fail
            FileNotFoundError: If clear data SQL file is not found
        """
        try:
            clear_sql = self.sql_manager.render_sql_template("clear_data")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Execute the data clearing SQL
                cursor.executescript(clear_sql)
                conn.commit()

            logger.info("Database data cleared successfully")

        except Exception as e:
            logger.error(f"Error clearing database data: {e}")
            raise

    def initialize_database(self) -> None:
        """
        Initialize a new database with tables and indexes.

        This is a convenience method that creates tables and indexes
        in the correct order for a new database setup.
        """
        try:
            logger.info(f"Initializing database: {self.db_path}")

            # Create tables first
            self.create_tables()

            # Then create indexes
            self.create_indexes()

            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def reset_database(self) -> None:
        """
        Reset the database by clearing data and reinitializing.

        This method clears all existing data and recreates the schema,
        effectively providing a clean database state.
        """
        try:
            logger.info(f"Resetting database: {self.db_path}")

            # Clear existing data
            self.clear_data()

            # Reinitialize schema (tables should already exist, but indexes might need refresh)
            self.create_indexes()

            logger.info("Database reset completed successfully")

        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database schema and contents.

        Returns:
            Dict[str, Any]: Database information including table counts and schema details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                # Get row counts for each table
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]

                # Get index information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]

                return {
                    "database_path": self.db_path,
                    "tables": tables,
                    "table_counts": table_counts,
                    "indexes": indexes,
                    "total_records": sum(table_counts.values()),
                }

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
