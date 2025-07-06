#!/usr/bin/env python3
"""Test search for specific function with parameters"""
from api.sqlite_backend import DocumentationDatabase

db = DocumentationDatabase('../docs/interactive-documentation-suite/documentation.db')

# Search for a function we know has parameters
functions = db.search_functions(query="load_api_key_from_env", limit=5)
print(f"SEARCH FOR 'load_api_key_from_env' RETURNS {len(functions)} functions:")
for func in functions:
    print(f"  {func.get('name', 'NO_NAME')}: parameters='{func.get('parameters', 'NO_PARAMETERS_FIELD')}'")

# Also test the actual API endpoint
print("\nTesting API endpoint directly...")
import requests

try:
    response = requests.get("http://localhost:8001/api/functions?search=load_api_key_from_env&limit=5")
    data = response.json()
    if data.get('success'):
        for func in data.get('data', []):
            print(f"  API: {func.get('name', 'NO_NAME')}: parameters='{func.get('parameters', 'NO_PARAMETERS_FIELD')}'")
    else:
        print(f"  API Error: {data}")
except Exception as e:
    print(f"  API Error: {e}")
