#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").absolute()))

# Set debug logging
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    print("Testing dashboard creation...")
    from dashboard.views import create_dashboard

    dashboard = create_dashboard("code_intelligence.db")
    print("Dashboard created successfully")
    print(f"Dashboard type: {type(dashboard)}")

except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback

    traceback.print_exc()
