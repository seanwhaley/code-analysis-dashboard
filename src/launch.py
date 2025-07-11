#!/usr/bin/env python3
"""
Launch script for USASpending Code Intelligence Dashboard

**Last Updated:** 2025-07-05 12:00:00

This script provides an easy way to start the dashboard server with proper
configuration and helpful output for development and production use.
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path
from time import sleep


def main():
    """Main launch function."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Launch USASpending Code Intelligence Dashboard"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--port", type=int, default=8001, help="Port to run server on (default: 8001)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    print("🎯 USASpending Code Intelligence Dashboard")
    print("=" * 50)
    if args.debug:
        print("🐛 DEBUG MODE ENABLED")
    print()

    # Check if we're in the right directory
    current_dir = Path(
        __file__
    ).parent.parent  # Go up one level from src to code-intelligence-dashboard
    expected_files = ["dashboard.html", "api/server.py", "components/dashboard-core.js"]

    missing_files = []
    for file in expected_files:
        if not (current_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Error: Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print()
        print(
            "Please ensure you're running this script from the code-intelligence-dashboard directory."
        )
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)

    print("✅ Environment checks passed")
    print()

    # Try to import required packages
    try:
        import fastapi
        import uvicorn

        print("✅ FastAPI dependencies found")
    except ImportError as e:
        print(f"❌ Error: Missing required package: {e}")
        print("Please install with: pip install fastapi uvicorn")
        sys.exit(1)

    # Check database
    db_path = (
        current_dir.parent
        / "docs"
        / "interactive-documentation-suite"
        / "documentation.db"
    )
    if not db_path.exists():
        print("❌ Error: Database not found at:")
        print(f"   {db_path}")
        print()
        print("Please ensure the documentation database has been generated.")
        sys.exit(1)

    print("✅ Database found")
    print()

    # Start server
    print("🚀 Starting Code Intelligence Dashboard Server...")
    print()
    print(f"📊 Dashboard will be available at: http://localhost:{args.port}")
    print(f"🔧 API documentation at: http://localhost:{args.port}/docs")
    print(f"❤️  Health check at: http://localhost:{args.port}/health")
    if args.debug:
        print("🐛 Debug logging enabled - detailed request/response logs will be shown")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    # Change to the correct directory
    os.chdir(current_dir)

    # Auto-open browser after a short delay
    def open_browser():
        sleep(2)
        try:
            webbrowser.open(f"http://localhost:{args.port}")
            print("🌐 Opened dashboard in your default browser")
        except Exception as e:
            print(f"Note: Could not auto-open browser: {e}")

    # Start browser opening in background
    import threading

    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Start the server
    try:
        import uvicorn

        # Import the server from the api directory
        sys.path.insert(0, str(current_dir / "api"))
        from server import app

        log_level = "debug" if args.debug else "info"
        uvicorn.run(app, host=args.host, port=args.port, log_level=log_level)

    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
