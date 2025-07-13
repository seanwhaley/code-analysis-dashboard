#!/usr/bin/env python3
"""
Check database schema with comprehensive analysis.

This script provides detailed schema information for the code intelligence
database, following project standards for type safety and error handling.
"""

import sqlite3
from pathlib import Path
from typing import Any, List


def format_column_info(columns: List[Any]) -> None:
    """Format and display column information in a readable format."""
    if not columns:
        print("    No columns found")
        return

    print("    Columns:")
    for _, name, col_type, not_null, default_val, primary_key in columns:
        nullable = "NOT NULL" if not_null else "NULL"
        pk_status = "PRIMARY KEY" if primary_key else ""
        default_info = f" DEFAULT {default_val}" if default_val is not None else ""
        print(
            f"      {name:<20} {col_type:<15} {nullable:<8} {pk_status}{default_info}"
        )


def check_table_schema(cursor: sqlite3.Cursor, table_name: str) -> None:
    """Check and display schema for a specific table."""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        print(f"\n📋 {table_name.title()} table (rows: {row_count:,}):")
        format_column_info(columns)

    except sqlite3.Error as e:
        print(f"    ❌ Error checking {table_name}: {e}")


def check_schema(db_path: str = "code_intelligence.db") -> None:
    """
    Check and analyze database schema.

    Args:
        db_path: Path to the SQLite database file
    """
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"❌ Database file not found: {db_path}")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"🗄️ Database Schema Analysis: {db_path}")
        print("=" * 60)

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("⚠️ No tables found in database")
            return

        print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")

        # Check each table
        for table in tables:
            check_table_schema(cursor, table)

        # Check indexes
        print(f"\n🔍 Indexes:")
        cursor.execute(
            """
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """
        )
        indexes = cursor.fetchall()

        if indexes:
            for name, table, _ in indexes:
                print(f"    {name} on {table}")
        else:
            print("    No custom indexes found")

        # Database file size
        db_size = db_file.stat().st_size
        size_mb = db_size / (1024 * 1024)
        print(f"\n💾 Database file size: {size_mb:.2f} MB ({db_size:,} bytes)")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_schema()
