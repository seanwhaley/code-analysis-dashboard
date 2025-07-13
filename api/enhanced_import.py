#!/usr/bin/env python3
"""
Enhanced import module for code structure and relationship data.

This module provides functionality to import code structure and relationship
data into the SQLite dashboard database, following project standards for
type safety, error handling, and logging.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Note: This references an API that may not exist in current structure
# Keeping for compatibility but adding proper error handling

logger = logging.getLogger(__name__)


def import_with_relationships(
    json_path: str, db_path: str = "code_intelligence.db"
) -> bool:
    """
    Import code structure with relationships from JSON to database.

    Args:
        json_path: Path to JSON file containing code structure data
        db_path: Path to SQLite database file

    Returns:
        True if import successful, False otherwise
    """
    json_file = Path(json_path)
    if not json_file.exists():
        logger.error(f"JSON file not found: {json_path}")
        return False

    try:
        # Try to import the backend - may not exist in current structure
        try:
            from api.sqlite_backend import DocumentationDatabase
        except ImportError:
            logger.warning(
                "sqlite_backend module not found. "
                "This appears to be legacy code that needs updating."
            )
            return False

        db = DocumentationDatabase(db_path)

        # Load and validate JSON data
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or "files" not in data:
            logger.error("Invalid JSON structure: expected 'files' key")
            return False

        # Import basic data
        db.import_from_json(json_path)

        # Import enhanced relationships
        with db._get_connection() as conn:
            cursor = conn.cursor()
            relationship_count = 0

            for file_data in data["files"]:
                if not isinstance(file_data, dict):
                    continue

                relationships = file_data.get("relationships", [])
                for rel in relationships:
                    if not isinstance(rel, dict):
                        continue

                    try:
                        cursor.execute(
                            """
                            INSERT INTO enhanced_relationships 
                            (source_type, source_id, target_type, relationship_type, context)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                rel.get("source_type", "unknown"),
                                rel.get("source_id"),
                                rel.get("target_type", "unknown"),
                                rel.get("relationship_type", "unknown"),
                                rel.get("target_name", ""),
                            ),
                        )
                        relationship_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to import relationship: {e}")

            conn.commit()
            logger.info(
                f"Successfully imported {relationship_count} enhanced relationships"
            )

        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False


def main() -> None:
    """Main entry point for the import script."""
    parser = argparse.ArgumentParser(
        description="Import code structure with relationships from JSON to database"
    )
    parser.add_argument(
        "json_file", help="Path to JSON file containing code structure data"
    )
    parser.add_argument(
        "--db",
        default="code_intelligence.db",
        help="Path to SQLite database file (default: code_intelligence.db)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Perform import
    success = import_with_relationships(args.json_file, args.db)
    exit_code = 0 if success else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
