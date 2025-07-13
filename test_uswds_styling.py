#!/usr/bin/env python3
"""
Test USWDS styling implementation
Creates a simple test page to verify USWDS components are working.
"""

import sys
from pathlib import Path

import panel as pn

# Add dashboard to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure Panel with USWDS styling
pn.extension(
    css_files=[
        "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&family=Merriweather:wght@400;700&family=Roboto+Mono:wght@400;500&display=swap",
    ],
    raw_css=[
        """
        /* USWDS Test Styles */
        :root {
          --usa-color-primary: #005ea2;
          --usa-color-primary-dark: #1a4480;
          --usa-color-primary-light: #73b3e7;
          --usa-color-base-lightest: #f9f9f9;
          --usa-color-base-darkest: #1b1b1b;
          --usa-font-family-sans: "Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          --usa-font-family-serif: "Merriweather", Georgia, serif;
        }
        
        body {
          font-family: var(--usa-font-family-sans);
          line-height: 1.5;
          background-color: var(--usa-color-base-lightest);
        }
        
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
        
        .usa-alert {
          border-left: 0.25rem solid;
          padding: 1rem 1.5rem;
          margin-bottom: 1rem;
        }
        
        .usa-alert--info {
          background-color: #e7f6f8;
          border-left-color: #00bde3;
        }
        
        .usa-alert--success {
          background-color: #ecf3ec;
          border-left-color: #00a91c;
        }
        
        .usa-alert__heading {
          font-weight: 700;
          margin: 0 0 0.5rem 0;
        }
        
        .usa-alert__text {
          margin: 0;
        }
        
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
        
        .dashboard-stat-card--success {
          border-left: 0.25rem solid #00a91c;
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
        
        .test-section {
          margin: 2rem 0;
        }
        """
    ],
)


def create_test_page():
    """Create a test page showing USWDS components."""

    # Header
    header = pn.pane.HTML(
        """
        <div class="usa-header">
            <h1 class="usa-header__title">🧠 USWDS Test Page</h1>
            <p class="usa-header__subtitle">Testing U.S. Web Design System implementation</p>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Test card
    test_card = pn.pane.HTML(
        """
        <div class="usa-card">
            <div class="usa-card__container">
                <div class="usa-card__header">
                    <h2 class="usa-card__heading">🎨 USWDS Components Test</h2>
                </div>
                <div class="usa-card__body">
                    <p>This page tests if USWDS styling is properly applied.</p>
                </div>
            </div>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Alert components
    alerts = pn.pane.HTML(
        """
        <div class="test-section">
            <h3>Alert Components</h3>
            <div class="usa-alert usa-alert--info">
                <div class="usa-alert__body">
                    <h4 class="usa-alert__heading">Info Alert</h4>
                    <p class="usa-alert__text">This is an informational alert using USWDS styling.</p>
                </div>
            </div>
            
            <div class="usa-alert usa-alert--success">
                <div class="usa-alert__body">
                    <h4 class="usa-alert__heading">Success Alert</h4>
                    <p class="usa-alert__text">This is a success alert using USWDS styling.</p>
                </div>
            </div>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Stats cards
    stats = pn.pane.HTML(
        """
        <div class="test-section">
            <h3>Statistics Cards</h3>
            <div class="dashboard-stats-grid">
                <div class="dashboard-stat-card dashboard-stat-card--primary">
                    <div class="dashboard-stat-value">1,234</div>
                    <div class="dashboard-stat-label">Total Files</div>
                </div>
                <div class="dashboard-stat-card dashboard-stat-card--success">
                    <div class="dashboard-stat-value">567</div>
                    <div class="dashboard-stat-label">Classes</div>
                </div>
                <div class="dashboard-stat-card dashboard-stat-card--primary">
                    <div class="dashboard-stat-value">890</div>
                    <div class="dashboard-stat-label">Functions</div>
                </div>
            </div>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Typography test
    typography = pn.pane.HTML(
        """
        <div class="test-section">
            <h3>Typography Test</h3>
            <p><strong>Body text</strong> should use Source Sans Pro font family.</p>
            <h1>Heading 1 - Merriweather Serif</h1>
            <h2>Heading 2 - Merriweather Serif</h2>
            <h3>Heading 3 - Merriweather Serif</h3>
            <code style="font-family: 'Roboto Mono', monospace;">Code text - Roboto Mono</code>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    # Status message
    status = pn.pane.HTML(
        """
        <div class="test-section">
            <h3>Status Check</h3>
            <p><strong>✅ If you can see:</strong></p>
            <ul>
                <li>Blue header with white text</li>
                <li>Professional card layouts with shadows</li>
                <li>Colored alert boxes</li>
                <li>Statistics cards with colored left borders</li>
                <li>Different fonts for headings vs body text</li>
            </ul>
            <p><strong>Then USWDS styling is working correctly!</strong></p>
        </div>
        """,
        sizing_mode="stretch_width",
    )

    return pn.Column(
        header,
        test_card,
        alerts,
        stats,
        typography,
        status,
        sizing_mode="stretch_width",
    )


def main():
    """Create and serve the test page."""
    test_page = create_test_page()
    return test_page


if __name__ == "__main__":
    # For direct execution
    app = main()
    app.show(port=5007)
else:
    # For panel serve
    app = main()
    app.servable()
