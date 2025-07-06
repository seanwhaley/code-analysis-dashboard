#!/usr/bin/env python3
import requests

# Test specific function IDs that have parameters in DB
target_ids = [14, 15, 16, 17, 18]

response = requests.get("http://localhost:8001/api/functions?limit=1000")
data = response.json()

print("Testing specific functions with parameters:")
found_count = 0
for func in data["data"]:
    if func["id"] in target_ids:
        params = func.get("parameters", "MISSING")
        print(f'  Function {func["id"]}: {func["name"]} -> "{params}"')
        found_count += 1

print(f"\nFound {found_count}/{len(target_ids)} target functions")

# Also check if any functions in the API response have parameters
print("\nAny functions with parameters in API:")
param_count = 0
for func in data["data"][:50]:  # Check first 50
    if func.get("parameters") and func["parameters"].strip():
        print(f'  {func["name"]}: {func["parameters"]}')
        param_count += 1
        if param_count >= 5:
            break

if param_count == 0:
    print("  No functions with parameters found in first 50 API results")
