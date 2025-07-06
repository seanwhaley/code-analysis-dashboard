#!/usr/bin/env python3
"""Find files that have functions with parameters"""
import sqlite3

# Connect to database
conn = sqlite3.connect('../docs/interactive-documentation-suite/documentation.db')
cursor = conn.cursor()

# Find files that contain functions with parameters
cursor.execute("""
    SELECT DISTINCT f.id, f.name, COUNT(*) as functions_with_params
    FROM files f
    JOIN functions func ON f.id = func.file_id 
    WHERE func.parameters IS NOT NULL AND func.parameters != ''
    GROUP BY f.id, f.name
    ORDER BY functions_with_params DESC
    LIMIT 5
""")

files_with_params = cursor.fetchall()
print("Files with functions that have parameters:")
for file_id, file_name, count in files_with_params:
    print(f"  File {file_id} ({file_name}): {count} functions with parameters")

# Test the file detailed endpoint for one of these files
if files_with_params:
    test_file_id = files_with_params[0][0]
    print(f"\nTesting file detail for file {test_file_id}...")
    
    from api.sqlite_backend import DocumentationDatabase
    db = DocumentationDatabase('../docs/interactive-documentation-suite/documentation.db')
    
    file_data = db.get_file_detailed_content(test_file_id)
    functions = file_data.get('functions', [])
    
    functions_with_params = [f for f in functions if f.get('parameters') and f.get('parameters').strip()]
    print(f"Functions with parameters in file detail: {len(functions_with_params)}")
    
    for func in functions_with_params[:3]:
        print(f"  {func.get('name')}: '{func.get('parameters')}'")

conn.close()
