"""
Import code structure and relationship data into SQLite dashboard DB.
"""

import json
from api.sqlite_backend import DocumentationDatabase

def import_with_relationships(json_path, db_path="documentation.db"):
    db = DocumentationDatabase(db_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    db.import_from_json(json_path)
    with db._get_connection() as conn:
        cursor = conn.cursor()
        for file in data["files"]:
            for rel in file.get("relationships", []):
                # You may need to resolve names to IDs or do a join if your schema expects it
                cursor.execute(
                    """
                    INSERT INTO enhanced_relationships (source_type, source_id, target_type, relationship_type, context)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        rel["source_type"],
                        rel.get("source_id", None),
                        rel["target_type"],
                        rel["relationship_type"],
                        rel.get("target_name", ""),
                    ),
                )
        conn.commit()
        print("Enhanced relationships imported.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("--db", default="documentation.db")
    args = parser.parse_args()
    import_with_relationships(args.json_file, args.db)