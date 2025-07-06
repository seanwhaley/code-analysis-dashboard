#!/usr/bin/env python3
"""Debug file detailed content vs direct database query"""
import sqlite3
from api.sqlite_backend import DocumentationDatabase

# Test file 469 which should have functions with parameters
file_id = 469

# Direct database query
conn = sqlite3.connect('../docs/interactive-documentation-suite/documentation.db')
cursor = conn.cursor()

print("DIRECT DATABASE QUERY:")
cursor.execute("SELECT name, parameters FROM functions WHERE file_id = ? AND parameters != '' LIMIT 5", (file_id,))
direct_functions = cursor.fetchall()
print(f"Functions with parameters (direct query): {len(direct_functions)}")
for name, params in direct_functions[:3]:
    print(f"  {name}: '{params}'")

# Get all functions for this file (direct)
cursor.execute("SELECT COUNT(*) FROM functions WHERE file_id = ?", (file_id,))
total_direct = cursor.fetchone()[0]
print(f"Total functions in file (direct): {total_direct}")

# Get functions via get_file_detailed_content
print("\nFILE DETAILED CONTENT METHOD:")
db = DocumentationDatabase('../docs/interactive-documentation-suite/documentation.db')
file_data = db.get_file_detailed_content(file_id)

functions = file_data.get('functions', [])
print(f"Total functions returned by get_file_detailed_content: {len(functions)}")

# Check if any have parameters
functions_with_params = [f for f in functions if f.get('parameters') and f.get('parameters').strip()]
print(f"Functions with parameters: {len(functions_with_params)}")

# Show first few functions from get_file_detailed_content
print("First 3 functions from get_file_detailed_content:")
for func in functions[:3]:
    params = func.get('parameters', 'NO_FIELD')
    print(f"  {func.get('name')}: '{params}'")

conn.close()
