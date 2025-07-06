#!/usr/bin/env python3
"""Test file detailed content method"""
from api.sqlite_backend import DocumentationDatabase

db = DocumentationDatabase('../docs/interactive-documentation-suite/documentation.db')

# Get file detailed content for file 689 (logging.py)
file_data = db.get_file_detailed_content(689)

print("FILE DETAILED CONTENT:")
print(f"File: {file_data.get('name')}")
print(f"Functions count: {len(file_data.get('functions', []))}")

# Check first few functions
functions = file_data.get('functions', [])
print(f"\nFirst 3 functions:")
for i, func in enumerate(functions[:3]):
    params = func.get('parameters', 'NO_PARAMETERS_FIELD')
    print(f"  {func.get('name', 'NO_NAME')}: parameters='{params}'")
    if i == 0:
        print(f"    All keys: {list(func.keys())}")

# Check if any functions have parameters
functions_with_params = [f for f in functions if f.get('parameters') and f.get('parameters').strip()]
print(f"\nFunctions with parameters in file detail: {len(functions_with_params)}")

if functions_with_params:
    for func in functions_with_params[:3]:
        print(f"  {func.get('name')}: '{func.get('parameters')}'")
