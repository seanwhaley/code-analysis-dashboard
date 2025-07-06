#!/usr/bin/env python3
"""Check function parameters in database"""
import sqlite3

# Connect to database
conn = sqlite3.connect('../docs/interactive-documentation-suite/documentation.db')
cursor = conn.cursor()

# Check functions with parameters
cursor.execute("SELECT COUNT(*) FROM functions WHERE parameters IS NOT NULL AND parameters != ''")
count_with_params = cursor.fetchone()[0]
print(f"Functions with parameters: {count_with_params}")

# Get some examples
cursor.execute("SELECT name, parameters FROM functions WHERE parameters IS NOT NULL AND parameters != '' LIMIT 5")
examples = cursor.fetchall()
print("\nExamples:")
for name, params in examples:
    print(f"  {name}: {params}")

# Test API query
cursor.execute("SELECT id, name, parameters FROM functions LIMIT 3")
api_test = cursor.fetchall()
print(f"\nAPI test (first 3 functions):")
for row in api_test:
    print(f"  ID {row[0]}: {row[1]} -> parameters: '{row[2]}'")

conn.close()
