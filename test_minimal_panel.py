#!/usr/bin/env python3
"""
Minimal Panel test to isolate serving issues
"""

import panel as pn

# Configure Panel with minimal settings
pn.extension("bokeh", template="bootstrap")


def create_minimal_app():
    """Create a minimal Panel app for testing."""
    return pn.pane.HTML(
        "<h1>🔍 Test Dashboard</h1><p>If you see this, Panel is working!</p>"
    )


# Make it servable
create_minimal_app().servable()
