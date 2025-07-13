#!/usr/bin/env python3
"""
Check relationships in database with proper type hints and error handling.

This script provides comprehensive analysis of relationships stored in the
code intelligence database, following project standards.
"""

import sqlite3
from pathlib import Path


def check_relationships(db_path: str = "code_intelligence.db") -> None:
    """
    Check and analyze relationships in the code intelligence database.

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

        # Check total relationships
        cursor.execute("SELECT COUNT(*) FROM relationships")
        total = cursor.fetchone()[0]
        print(f"📊 Total relationships: {total}")

        if total == 0:
            print("⚠️ No relationships found in database")
            return

        # Check relationships by type
        cursor.execute(
            """
            SELECT source_type, target_type, COUNT(*) as count 
            FROM relationships 
            GROUP BY source_type, target_type 
            ORDER BY count DESC
            """
        )
        print("\n🔗 Relationships by type:")
        for row in cursor.fetchall():
            print(f"  {row[0]} → {row[1]}: {row[2]:,}")

        # Check relationship types
        cursor.execute(
            """
            SELECT relationship_type, COUNT(*) as count 
            FROM relationships 
            GROUP BY relationship_type 
            ORDER BY count DESC
            """
        )
        print("\n📋 Relationship types:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,}")

        # Check all relationship type combinations
        cursor.execute(
            """
            SELECT DISTINCT source_type, target_type, relationship_type 
            FROM relationships 
            ORDER BY source_type, target_type, relationship_type
            """
        )
        print("\n🔍 All relationship combinations:")
        for row in cursor.fetchall():
            print(f"  {row[0]} → {row[1]} ({row[2]})")

        # Check some sample relationships with details
        cursor.execute(
            """
            SELECT source_name, source_type, target_name, target_type, 
                   relationship_type, file_path, line_number
            FROM relationships 
            LIMIT 5
            """
        )
        print("\n📝 Sample relationships:")
        for row in cursor.fetchall():
            (
                source_name,
                source_type,
                target_name,
                target_type,
                rel_type,
                file_path,
                line_num,
            ) = row
            line_info = f" (line {line_num})" if line_num else ""
            print(f"  {source_name} ({source_type}) → {target_name} ({target_type})")
            print(f"    Relationship: {rel_type}")
            print(f"    File: {file_path}{line_info}")
            print()

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if "conn" in locals() and conn:
            conn.close()


if __name__ == "__main__":
    check_relationships()
