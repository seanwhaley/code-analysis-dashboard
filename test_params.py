#!/usr/bin/env python3
import sqlite3

import requests

# Check database directly
print("Functions with parameters in DB:")
conn = sqlite3.connect("../docs/interactive-documentation-suite/documentation.db")
cursor = conn.cursor()
cursor.execute(
    'SELECT id, name, parameters FROM functions WHERE parameters IS NOT NULL AND parameters != "" LIMIT 5'
)
results = cursor.fetchall()
for r in results:
    print(f"  {r[0]}: {r[1]} -> {r[2]}")
conn.close()

# Check API
print("\nAPI Response:")
response = requests.get("http://localhost:8001/api/functions?limit=20")
data = response.json()

count = 0
for func in data["data"]:
    if func.get("parameters") and func["parameters"].strip():
        print(f'  {func["name"]}: {func["parameters"]}')
        count += 1
        if count >= 5:
            break

if count == 0:
    print("No functions with parameters found in API response")
    print("\nSample API function data:")
    for func in data["data"][:3]:
        print(
            f'  ID: {func["id"]}, Name: {func["name"]}, Params: "{func.get("parameters", "MISSING")}", Count: {func.get("parameters_count", 0)}'
        )
