#!/usr/bin/env python3
"""
Main Panel Application Entry Point

This is the main entry point for the Panel-based code intelligence dashboard.
Run with: panel serve dashboard/app.py --show --autoreload

The application provides a comprehensive code analysis dashboard with:
- File exploration and filtering
- System statistics and visualizations
- Global search functionality
- Analysis configuration and execution

All functionality is implemented in Python using Panel's reactive framework.
"""

import logging
import os
import sys
from pathlib import Path

import panel as pn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import dashboard components
from dashboard.views import create_dashboard

# Configure Panel
pn.extension("bokeh", "tabulator", template="material", sizing_mode="stretch_width")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dashboard.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def create_header() -> pn.Row:
    """Create the dashboard header."""
    title = pn.pane.HTML(
        """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 2.5em; font-weight: 300;">
            🧠 Code Intelligence Dashboard
        </h1>
        <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">
            Comprehensive Python-based code analysis and exploration
        </p>
    </div>
    """,
        sizing_mode="stretch_width",
    )

    return title


def create_footer() -> pn.Row:
    """Create the dashboard footer."""
    footer = pn.pane.HTML(
        """
    <div style="text-align: center; padding: 20px; color: #6c757d; border-top: 1px solid #dee2e6; margin-top: 40px;">
        <p>Built with ❤️ using <a href="https://panel.holoviz.org/" target="_blank">Panel</a>, 
           <a href="https://docs.pydantic.dev/" target="_blank">Pydantic</a>, and Python AST</p>
        <p><small>Code Intelligence Dashboard v1.0 | Python-only implementation</small></p>
    </div>
    """,
        sizing_mode="stretch_width",
    )

    return footer


def main():
    """Main application function."""
    logger.info("Starting Code Intelligence Dashboard")

    # Determine database path
    db_path = os.environ.get("DASHBOARD_DB_PATH", "code_intelligence.db")

    # Check if database exists
    if not Path(db_path).exists():
        logger.warning(
            f"Database not found at {db_path}. You'll need to run analysis first."
        )

    # Create the main dashboard
    try:
        dashboard = create_dashboard(db_path)

        # Create the complete application layout
        app = pn.Column(
            create_header(),
            dashboard,
            create_footer(),
            sizing_mode="stretch_width",
            margin=(20, 20),
        )

        logger.info("Dashboard created successfully")
        return app

    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")

        # Return error page
        error_page = pn.Column(
            create_header(),
            pn.pane.HTML(
                f"""
            <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; border: 1px solid #f5c6cb;">
                <h3>⚠️ Dashboard Error</h3>
                <p><strong>Error:</strong> {e}</p>
                <p><strong>Possible solutions:</strong></p>
                <ul>
                    <li>Make sure the database file exists: <code>{db_path}</code></li>
                    <li>Run the analysis first using the Analysis tab</li>
                    <li>Check the logs for more details</li>
                    <li>Verify all dependencies are installed: <code>pip install -r requirements.txt</code></li>
                </ul>
                <p><strong>Quick start:</strong></p>
                <ol>
                    <li>Go to the Analysis tab</li>
                    <li>Set your project root path</li>
                    <li>Click "Run Analysis" to populate the database</li>
                    <li>Explore your code in the other tabs</li>
                </ol>
            </div>
            """
            ),
            create_footer(),
            sizing_mode="stretch_width",
            margin=(20, 20),
        )

        return error_page


# Create the servable application
if __name__ == "__main__":
    # For direct execution
    app = main()
    app.show(port=5007)
else:
    # For panel serve
    app = main()


# Make the app servable
pn.serve(
    main,
    port=5007,
    allow_websocket_origin=["localhost:5007"],
    show=True,
    autoreload=True,
)
