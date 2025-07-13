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

Last Updated: 2025-01-27 15:30:00
"""

import os
import sys
from pathlib import Path
from typing import Any, Union

import panel as pn

sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.dashboard_logging import setup_logging
from dashboard.settings import DashboardSettings
from dashboard.templates.template_manager import (
    render_error_page,
    render_footer,
    render_header,
)
from dashboard.views import create_dashboard

# Load dashboard settings from YAML
settings = DashboardSettings.from_yaml()

# -------------------------------------------------------------
# Logging Setup (MANDATORY for all dashboard submodules)
# -------------------------------------------------------------
# This configures the global logger using dashboard settings.
# All logging in this module and submodules should use this logger.
logger = setup_logging(settings)

# Panel extension setup with enhanced visualization libraries
pn.extension(
    "bokeh",
    "plotly",
    "tabulator",
    css_files=[
        "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&family=Merriweather:wght@400;700&family=Roboto+Mono:wght@400;500&display=swap",
    ],
    raw_css=[
        """
        /* Import USWDS Theme directly */
        @import url('assets/uswds-theme.css');
        
        /* Inline critical USWDS styles for immediate application */
        :root {
          --usa-color-primary: #005ea2;
          --usa-color-primary-dark: #1a4480;
          --usa-color-primary-light: #73b3e7;
          --usa-color-base-lightest: #f9f9f9;
          --usa-color-base-darkest: #1b1b1b;
          --usa-font-family-sans: "Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          --usa-font-family-serif: "Merriweather", Georgia, serif;
        }
        
        /* USWDS Header */
        .usa-header {
          background-color: var(--usa-color-primary);
          color: white;
          padding: 1.5rem 2rem;
          border-bottom: 1px solid var(--usa-color-primary-dark);
        }
        
        .usa-header__title {
          font-family: var(--usa-font-family-serif);
          font-size: 1.75rem;
          font-weight: 700;
          margin: 0 0 0.5rem 0;
          color: white;
        }
        
        .usa-header__subtitle {
          font-size: 1.125rem;
          margin: 0;
          opacity: 0.9;
          color: var(--usa-color-primary-light);
        }
        
        /* USWDS Navigation */
        .usa-nav {
          background-color: var(--usa-color-primary-dark);
          padding: 0.5rem 2rem;
        }
        
        .usa-nav__list {
          display: flex;
          list-style: none;
          margin: 0;
          padding: 0;
          gap: 1.5rem;
        }
        
        .usa-nav__link {
          color: white;
          text-decoration: none;
          padding: 0.5rem 1rem;
          border-radius: 0.25rem;
          font-weight: 500;
        }
        
        .usa-nav__link:hover {
          background-color: rgba(255,255,255,0.1);
        }
        
        /* USWDS Cards */
        .usa-card {
          background-color: white;
          border: 1px solid #e6e6e6;
          border-radius: 0.5rem;
          box-shadow: 0 1px 5px rgba(0,0,0,0.15);
          margin-bottom: 2rem;
        }
        
        .usa-card__container {
          padding: 2rem;
        }
        
        .usa-card__header {
          background-color: var(--usa-color-base-lightest);
          border-bottom: 1px solid #e6e6e6;
          padding: 1.5rem 2rem;
          margin: -2rem -2rem 1.5rem -2rem;
        }
        
        .usa-card__heading {
          font-family: var(--usa-font-family-serif);
          font-size: 1.375rem;
          font-weight: 700;
          margin: 0;
          color: var(--usa-color-base-darkest);
        }
        
        /* USWDS Alerts */
        .usa-alert {
          border-left: 0.25rem solid;
          padding: 1rem 1.5rem;
          margin-bottom: 1rem;
        }
        
        .usa-alert--info {
          background-color: #e7f6f8;
          border-left-color: #00bde3;
        }
        
        .usa-alert--error {
          background-color: #f4e3db;
          border-left-color: #d54309;
        }
        
        .usa-alert__heading {
          font-weight: 700;
          margin: 0 0 0.5rem 0;
        }
        
        .usa-alert__text {
          margin: 0;
        }
        
        /* Dashboard Stats Grid */
        .dashboard-stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        
        .dashboard-stat-card {
          background-color: white;
          border: 1px solid #e6e6e6;
          border-radius: 0.5rem;
          padding: 1.5rem;
          text-align: center;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .dashboard-stat-card--primary {
          border-left: 0.25rem solid var(--usa-color-primary);
        }
        
        .dashboard-stat-value {
          font-family: var(--usa-font-family-serif);
          font-size: 2rem;
          font-weight: 700;
          margin: 0 0 0.5rem 0;
          color: var(--usa-color-primary);
        }
        
        .dashboard-stat-label {
          font-size: 0.875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #71767a;
          margin: 0;
        }
        
        /* USWDS Footer */
        .usa-footer {
          background-color: #454545;
          color: white;
          padding: 2rem;
          margin-top: 3rem;
        }
        
        .usa-summary-box {
          background-color: var(--usa-color-base-lightest);
          border: 1px solid #e6e6e6;
          border-left: 0.25rem solid var(--usa-color-primary);
          padding: 1.5rem;
          margin-bottom: 2rem;
          color: var(--usa-color-base-darkest);
        }
        
        .usa-summary-box__heading {
          font-family: var(--usa-font-family-serif);
          font-size: 1.375rem;
          font-weight: 700;
          margin: 0 0 1rem 0;
        }
        
        /* Apply USWDS fonts globally */
        body {
          font-family: var(--usa-font-family-sans);
          line-height: 1.5;
        }
        
        h1, h2, h3, h4, h5, h6 {
          font-family: var(--usa-font-family-serif);
        }
        
        /* Panel-specific overrides */
        .bk-root .bk-tab {
          font-family: var(--usa-font-family-sans);
        }
        
        .panel-widget-box {
          font-family: var(--usa-font-family-sans);
        }
        """
    ],
    js_files={
        "uswds_init": """
        // USWDS Accessibility and Interaction Enhancements
        document.addEventListener('DOMContentLoaded', function() {
            // Add ARIA labels to navigation
            const navLinks = document.querySelectorAll('.usa-nav__link');
            navLinks.forEach(link => {
                link.setAttribute('role', 'menuitem');
            });
            
            // Enhance table accessibility
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                table.setAttribute('role', 'table');
                table.classList.add('usa-table', 'usa-table--striped');
            });
            
            // Add focus management for better keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });
            
            document.addEventListener('mousedown', function() {
                document.body.classList.remove('keyboard-navigation');
            });
            
            console.log('USWDS enhancements loaded successfully');
        });
        """
    },
)

# Enable console output for debugging
pn.config.console_output = "accumulate"

# Fix Bokeh loading issue by adding proper initialization
# This ensures Bokeh scripts load before initialization code
pn.config.js_files = {
    "bokeh_fix": """
// Enhanced Bokeh initialization with proper loading checks
(function() {
    'use strict';
    
    // Store original embed function if it exists
    var originalEmbed = window.embed_document;
    
    // Enhanced embed function with proper Bokeh availability checking
    window.embed_document = function(root) {
        function waitForBokeh(maxAttempts = 200, interval = 50) {
            var attempts = 0;
            
            function check() {
                // Check if Bokeh is available and has required methods
                if (typeof Bokeh !== 'undefined' && 
                    Bokeh.embed && 
                    typeof Bokeh.embed.embed_items === 'function') {
                    
                    console.log('Bokeh loaded successfully, initializing dashboard...');
                    
                    // Call original embed function if it exists
                    if (originalEmbed && typeof originalEmbed === 'function') {
                        try {
                            originalEmbed(root);
                        } catch (e) {
                            console.error('Error in original embed function:', e);
                        }
                    }
                    return;
                }
                
                attempts++;
                if (attempts >= maxAttempts) {
                    console.error('Bokeh failed to load after ' + maxAttempts + ' attempts');
                    
                    // Show user-friendly error message
                    var errorDiv = document.createElement('div');
                    errorDiv.style.cssText = 'padding: 20px; text-align: center; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; margin: 20px;';
                    errorDiv.innerHTML = '<h3 style="color: #dc3545;">Dashboard Loading Issue</h3><p>The dashboard components are taking longer than expected to load. Please refresh the page or check your internet connection.</p><button onclick="location.reload()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">Refresh Page</button>';
                    
                    // Find a suitable container or use body
                    var container = document.querySelector('[data-root-id]') || document.body;
                    if (container) {
                        container.appendChild(errorDiv);
                    }
                    return;
                }
                
                // Show loading indicator for user feedback
                if (attempts === 1) {
                    var loadingDiv = document.createElement('div');
                    loadingDiv.id = 'bokeh-loading-indicator';
                    loadingDiv.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #17a2b8; color: white; padding: 8px 12px; border-radius: 3px; font-size: 12px; z-index: 9999;';
                    loadingDiv.innerHTML = 'Loading dashboard components...';
                    document.body.appendChild(loadingDiv);
                }
                
                setTimeout(check, interval);
            }
            
            check();
        }
        
        // Start the enhanced loading process
        waitForBokeh();
    };
    
    // Remove loading indicator when Bokeh is ready
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            var loadingIndicator = document.getElementById('bokeh-loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }, 5000); // Remove after 5 seconds regardless
    });
    
})();
"""
}


def create_header() -> pn.pane.HTML:
    """
    Create the dashboard header.

    Returns:
        pn.pane.HTML: Header component with navigation and branding
    """
    try:
        header_content: str = render_header()  # Ensure render_header returns a string
        return pn.pane.HTML(
            header_content,
            sizing_mode="stretch_width",
        )
    except Exception as e:
        logger.error(f"Error creating header: {e}")
        return pn.pane.HTML(
            "<div class='error'>Error loading header</div>",
            sizing_mode="stretch_width",
        )


def create_footer() -> pn.pane.HTML:
    """
    Create the dashboard footer.

    Returns:
        pn.pane.HTML: Footer component with links and information
    """
    try:
        footer_content: str = render_footer()  # Ensure render_footer returns a string
        return pn.pane.HTML(
            footer_content,
            sizing_mode="stretch_width",
        )
    except Exception as e:
        logger.error(f"Error creating footer: {e}")
        return pn.pane.HTML(
            "<div class='error'>Error loading footer</div>",
            sizing_mode="stretch_width",
        )


def validate_database_path(db_path: str) -> bool:
    """
    Validate that the database path exists and is accessible.

    Args:
        db_path: Path to the database file

    Returns:
        bool: True if database is valid and accessible
    """
    try:
        path = Path(db_path)
        if not path.exists():
            logger.warning(f"Database not found at {db_path}")
            return False
        if not path.is_file():
            logger.error(f"Database path is not a file: {db_path}")
            return False
        if not os.access(db_path, os.R_OK):
            logger.error(f"Database is not readable: {db_path}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating database path {db_path}: {e}")
        return False


def create_error_layout(error_message: str, db_path: str) -> pn.Column:
    """
    Create an error layout for display when the main dashboard fails.

    Args:
        error_message: The error message to display
        db_path: The database path that caused the error

    Returns:
        pn.Column: Error layout component
    """
    try:
        error_html = render_error_page(error_message, db_path)
        return pn.Column(
            create_header(),
            pn.pane.HTML(error_html),
            create_footer(),
            sizing_mode=settings.ui.sizing_mode,
            margin=(20, 20),
        )
    except Exception as e:
        logger.error(f"Error creating error layout: {e}")
        # Fallback minimal error display
        return pn.Column(
            pn.pane.HTML(f"<h1>Critical Error</h1><p>{error_message}</p>"),
            sizing_mode="stretch_width",
        )


def main() -> Union[pn.Tabs, pn.Column]:
    """
    Main application function.

    Returns:
        Union[pn.Tabs, pn.Column]: The main dashboard application or error page
    """
    logger.info("Starting Code Intelligence Dashboard")

    # Determine database path (YAML overrides default)
    db_path = os.environ.get("DASHBOARD_DB_PATH", settings.db_path)
    logger.info(f"Using database path: {db_path}")

    # Validate database
    if not validate_database_path(db_path):
        error_msg = f"Database validation failed. Please ensure the database exists at {db_path}"
        return create_error_layout(error_msg, db_path)

    # Create the main dashboard
    try:
        dashboard = create_dashboard(db_path)

        # Simplified layout - just return the dashboard directly
        # This avoids potential issues with complex Column layouts
        logger.info("Dashboard created successfully")
        return dashboard

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        error_message = f"Error creating dashboard: {str(e)}"
        logger.error(f"{error_message}. Full traceback:\n{error_details}")

        # Return a simple error message instead of complex layout
        return pn.pane.HTML(
            f"""
            <div style="padding: 20px; text-align: center;">
                <h1>🔍 Code Intelligence Dashboard</h1>
                <div style="color: red; margin: 20px;">
                    <h2>Error</h2>
                    <p>{error_message}</p>
                    <details>
                        <summary>Technical Details</summary>
                        <pre style="text-align: left; background: #f5f5f5; padding: 10px;">{error_details}</pre>
                    </details>
                </div>
            </div>
        """
        )


def serve_app() -> Any:
    """
    Function to serve the app - call this to start the server.

    Returns:
        Any: Panel server instance
    """
    try:
        return pn.serve(
            main,
            port=settings.ui.port,
            allow_websocket_origin=[f"localhost:{settings.ui.port}"],
            show=True,
            autoreload=True,
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


# Create the servable application
if __name__ == "__main__":
    # For direct execution
    try:
        app = main()
        app.show(port=settings.ui.port)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
else:
    # For panel serve - create the app and make it servable
    try:
        logger.info("Creating servable app for Panel server")
        app = main()
        logger.info(f"App created successfully: {type(app)}")
        app.servable()
        logger.info("App made servable")
    except Exception as e:
        logger.error(f"Error creating servable app: {e}")
        import traceback

        traceback.print_exc()
        # Create a minimal error app
        error_app = pn.pane.HTML(f"<h1>Error</h1><p>{e}</p>")
        error_app.servable()
