#!/usr/bin/env python3
"""Test API response vs database content"""
import sqlite3
import json

# Connect to database
conn = sqlite3.connect('../docs/interactive-documentation-suite/documentation.db')
cursor = conn.cursor()

# Get functions with parameters from database directly
cursor.execute("SELECT name, parameters FROM functions WHERE parameters IS NOT NULL AND parameters != '' LIMIT 3")
db_functions = cursor.fetchall()

print("DATABASE DATA:")
for name, params in db_functions:
    print(f"  {name}: '{params}'")

# Test what the search_functions method returns
from api.sqlite_backend import DocumentationDatabase
db = DocumentationDatabase('../docs/interactive-documentation-suite/documentation.db')

functions = db.search_functions(limit=5)
print(f"\nSEARCH_FUNCTIONS METHOD RETURNS {len(functions)} functions:")
for func in functions[:3]:
    print(f"  {func.get('name', 'NO_NAME')}: parameters='{func.get('parameters', 'NO_PARAMETERS_FIELD')}'")
    print(f"    Keys: {list(func.keys())}")

conn.close()
