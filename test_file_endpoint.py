#!/usr/bin/env python3
import requests

# Get available file IDs
response = requests.get("http://localhost:8001/api/files?limit=3")
data = response.json()

print("Available files:")
for file_data in data["data"]:
    file_id = file_data["id"]
    file_name = file_data["name"]
    print(f"  File ID: {file_id}, Name: {file_name}")

    # Test detailed endpoint
    detail_response = requests.get(f"http://localhost:8001/api/file/{file_id}/detailed")
    print(f"    Detailed endpoint: {detail_response.status_code}")
    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        classes_count = len(detail_data.get("data", {}).get("classes", []))
        functions_count = len(detail_data.get("data", {}).get("functions", []))
        print(f"    Classes: {classes_count}, Functions: {functions_count}")
    break  # Test just the first one
