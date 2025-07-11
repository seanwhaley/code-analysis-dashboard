#!/usr/bin/env python3
"""
Panel Dashboard Views with Pydantic-Panel Integration

This module contains all the Panel-based UI components and views for the
code intelligence dashboard. It uses Pydantic-Panel for auto-generated
forms and Panel's reactive programming model for interactivity.

All UI components are built using Python only - no JavaScript required.
"""

import logging

# Import our models and database
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import panel as pn
import param
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.queries import DatabaseQuerier

from models.types import (
    AnalysisConfigForm,
    ComplexityLevel,
    DomainType,
    FileFilterForm,
    FileType,
    SystemStats,
)

# Configure Panel
pn.extension("bokeh", "tabulator", template="material")

# Configure logging
logger = logging.getLogger(__name__)


class DashboardState(param.Parameterized):
    """Central state management for the dashboard."""

    # Database connection
    db_querier = param.Parameter(default=None)

    # Current filters
    current_filters = param.Dict(default={})

    # Selected items
    selected_file_id = param.Integer(default=None, allow_None=True)
    selected_class_id = param.Integer(default=None, allow_None=True)
    selected_function_id = param.Integer(default=None, allow_None=True)

    # Search state
    search_term = param.String(default="")
    search_results = param.Dict(default={})

    # System statistics
    system_stats = param.Parameter(default=None)

    def __init__(self, db_path: str = "code_intelligence.db", **params):
        super().__init__(**params)
        self.db_querier = DatabaseQuerier(db_path)
        self.refresh_system_stats()

    def refresh_system_stats(self):
        """Refresh system statistics from database."""
        try:
            self.system_stats = self.db_querier.get_system_stats()
        except Exception as e:
            logger.error(f"Error refreshing system stats: {e}")
            self.system_stats = None


class FileExplorer(param.Parameterized):
    """File explorer component with filtering and search."""

    state = param.Parameter()

    def __init__(self, state: DashboardState, **params):
        super().__init__(state=state, **params)
        self.filter_form = None
        self.files_table = None
        self.setup_components()

    def setup_components(self):
        """Setup the file explorer components."""
        # Create filter form using Pydantic model
        self.filter_form = self.create_filter_form()

        # Create files table
        self.files_table = self.create_files_table()

    def create_filter_form(self) -> pn.Column:
        """Create the file filter form using Pydantic-Panel."""
        # For now, create manual form - Pydantic-Panel integration would go here
        domain_select = pn.widgets.Select(
            name="Domain",
            value=None,
            options=[None] + [d.value for d in DomainType],
            width=200,
        )

        file_type_select = pn.widgets.Select(
            name="File Type",
            value=None,
            options=[None] + [ft.value for ft in FileType],
            width=200,
        )

        complexity_select = pn.widgets.Select(
            name="Complexity Level",
            value=None,
            options=[None] + [cl.value for cl in ComplexityLevel],
            width=200,
        )

        min_lines_input = pn.widgets.IntInput(
            name="Min Lines", value=None, start=0, width=150
        )

        max_lines_input = pn.widgets.IntInput(
            name="Max Lines", value=None, start=0, width=150
        )

        search_input = pn.widgets.TextInput(
            name="Search", placeholder="Search files...", width=300
        )

        apply_button = pn.widgets.Button(
            name="Apply Filters", button_type="primary", width=150
        )

        clear_button = pn.widgets.Button(
            name="Clear Filters", button_type="light", width=150
        )

        # Bind callbacks
        apply_button.on_click(
            lambda event: self.apply_filters(
                domain_select.value,
                file_type_select.value,
                complexity_select.value,
                min_lines_input.value,
                max_lines_input.value,
                search_input.value,
            )
        )

        clear_button.on_click(
            lambda event: self.clear_filters(
                domain_select,
                file_type_select,
                complexity_select,
                min_lines_input,
                max_lines_input,
                search_input,
            )
        )

        return pn.Column(
            "## File Filters",
            pn.Row(domain_select, file_type_select, complexity_select),
            pn.Row(min_lines_input, max_lines_input),
            search_input,
            pn.Row(apply_button, clear_button),
            width=800,
        )

    def create_files_table(self) -> pn.widgets.Tabulator:
        """Create the files data table."""
        # Get initial data
        files, total_count = self.state.db_querier.get_all_files(limit=100)

        # Convert to DataFrame
        df = self.files_to_dataframe(files)

        # Create Tabulator widget
        table = pn.widgets.Tabulator(
            df,
            pagination="remote",
            page_size=25,
            sizing_mode="stretch_width",
            height=600,
            selectable=1,
            configuration={
                "columns": [
                    {"title": "Name", "field": "name", "width": 200},
                    {"title": "Path", "field": "path", "width": 300},
                    {"title": "Domain", "field": "domain", "width": 120},
                    {"title": "Type", "field": "file_type", "width": 100},
                    {"title": "Complexity", "field": "complexity", "width": 100},
                    {"title": "Lines", "field": "lines_of_code", "width": 80},
                    {"title": "Classes", "field": "classes_count", "width": 80},
                    {"title": "Functions", "field": "functions_count", "width": 80},
                ]
            },
        )

        # Bind selection callback
        table.param.watch(self.on_file_selected, "selection")

        return table

    def files_to_dataframe(self, files: List) -> pd.DataFrame:
        """Convert file records to DataFrame."""
        data = []
        for file in files:
            data.append(
                {
                    "id": file.id,
                    "name": file.name,
                    "path": file.path,
                    "domain": file.domain.value,
                    "file_type": file.file_type.value,
                    "complexity": file.complexity,
                    "complexity_level": file.complexity_level.value,
                    "lines_of_code": file.lines_of_code,
                    "classes_count": file.classes_count,
                    "functions_count": file.functions_count,
                    "imports_count": file.imports_count,
                    "pydantic_models_count": file.pydantic_models_count,
                }
            )

        return pd.DataFrame(data)

    def apply_filters(
        self, domain, file_type, complexity_level, min_lines, max_lines, search_term
    ):
        """Apply filters and refresh the table."""
        try:
            # Convert string values back to enums
            domain_enum = DomainType(domain) if domain else None
            file_type_enum = FileType(file_type) if file_type else None
            complexity_enum = (
                ComplexityLevel(complexity_level) if complexity_level else None
            )

            # Query with filters
            files, total_count = self.state.db_querier.get_all_files(
                domain=domain_enum,
                file_type=file_type_enum,
                complexity_level=complexity_enum,
                min_lines=min_lines,
                max_lines=max_lines,
                search_term=search_term,
                limit=1000,  # Increase limit for filtered results
            )

            # Update table
            df = self.files_to_dataframe(files)
            self.files_table.value = df

            # Update state
            self.state.current_filters = {
                "domain": domain,
                "file_type": file_type,
                "complexity_level": complexity_level,
                "min_lines": min_lines,
                "max_lines": max_lines,
                "search_term": search_term,
            }

            logger.info(f"Applied filters, found {len(files)} files")

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            pn.state.notifications.error(f"Error applying filters: {e}")

    def clear_filters(self, *widgets):
        """Clear all filters and reset the table."""
        try:
            # Reset widget values
            for widget in widgets:
                if hasattr(widget, "value"):
                    widget.value = None if widget.name != "Search" else ""

            # Reset table to show all files
            files, total_count = self.state.db_querier.get_all_files(limit=100)
            df = self.files_to_dataframe(files)
            self.files_table.value = df

            # Clear state
            self.state.current_filters = {}

            logger.info("Filters cleared")

        except Exception as e:
            logger.error(f"Error clearing filters: {e}")
            pn.state.notifications.error(f"Error clearing filters: {e}")

    def on_file_selected(self, event):
        """Handle file selection."""
        if event.new and len(event.new) > 0:
            selected_row = event.new[0]
            file_id = self.files_table.value.iloc[selected_row]["id"]
            self.state.selected_file_id = file_id
            logger.info(f"Selected file ID: {file_id}")

    def view(self) -> pn.Column:
        """Return the complete file explorer view."""
        return pn.Column(
            self.filter_form, "## Files", self.files_table, sizing_mode="stretch_width"
        )


class StatisticsPanel(param.Parameterized):
    """Statistics and analytics panel."""

    state = param.Parameter()

    def __init__(self, state: DashboardState, **params):
        super().__init__(state=state, **params)

    def create_overview_cards(self) -> pn.Row:
        """Create overview statistics cards."""
        if not self.state.system_stats:
            return pn.pane.HTML("<p>No statistics available</p>")

        stats = self.state.system_stats

        files_card = pn.pane.HTML(
            f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff;">
            <h3 style="margin: 0; color: #007bff;">{stats.total_files:,}</h3>
            <p style="margin: 5px 0 0 0; color: #6c757d;">Total Files</p>
        </div>
        """,
            width=200,
            height=100,
        )

        classes_card = pn.pane.HTML(
            f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #28a745;">
            <h3 style="margin: 0; color: #28a745;">{stats.total_classes:,}</h3>
            <p style="margin: 5px 0 0 0; color: #6c757d;">Total Classes</p>
        </div>
        """,
            width=200,
            height=100,
        )

        functions_card = pn.pane.HTML(
            f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #ffc107;">
            <h3 style="margin: 0; color: #ffc107;">{stats.total_functions:,}</h3>
            <p style="margin: 5px 0 0 0; color: #6c757d;">Total Functions</p>
        </div>
        """,
            width=200,
            height=100,
        )

        lines_card = pn.pane.HTML(
            f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #dc3545;">
            <h3 style="margin: 0; color: #dc3545;">{stats.total_lines:,}</h3>
            <p style="margin: 5px 0 0 0; color: #6c757d;">Lines of Code</p>
        </div>
        """,
            width=200,
            height=100,
        )

        return pn.Row(files_card, classes_card, functions_card, lines_card)

    def create_domain_chart(self) -> pn.pane.Bokeh:
        """Create domain distribution chart."""
        if not self.state.system_stats or not self.state.system_stats.domains:
            return pn.pane.HTML("<p>No domain data available</p>")

        domains = self.state.system_stats.domains

        # Prepare data
        domain_names = [d.domain.value.replace("_", " ").title() for d in domains]
        file_counts = [d.files_count for d in domains]

        # Create figure
        p = figure(
            x_range=domain_names,
            title="Files by Domain",
            height=400,
            width=600,
            toolbar_location=None,
        )

        # Add bars
        colors = (
            Category20[len(domain_names)] if len(domain_names) <= 20 else Category20[20]
        )
        p.vbar(
            x=domain_names,
            top=file_counts,
            width=0.8,
            color=colors[: len(domain_names)],
            alpha=0.8,
        )

        # Styling
        p.xgrid.grid_line_color = None
        p.xaxis.major_label_orientation = 45
        p.y_range.start = 0

        # Add hover tool
        hover = HoverTool(tooltips=[("Domain", "@x"), ("Files", "@top")])
        p.add_tools(hover)

        return pn.pane.Bokeh(p)

    def create_complexity_chart(self) -> pn.pane.Bokeh:
        """Create complexity distribution chart."""
        if (
            not self.state.system_stats
            or not self.state.system_stats.complexity_distribution
        ):
            return pn.pane.HTML("<p>No complexity data available</p>")

        complexity_dist = self.state.system_stats.complexity_distribution

        # Prepare data
        complexity_levels = [d.complexity_range for d in complexity_dist]
        counts = [d.count for d in complexity_dist]
        percentages = [d.percentage for d in complexity_dist]

        # Create figure
        p = figure(
            x_range=complexity_levels,
            title="Complexity Distribution",
            height=400,
            width=600,
            toolbar_location=None,
        )

        # Add bars with color mapping
        colors = ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]  # Green to Red
        p.vbar(
            x=complexity_levels,
            top=counts,
            width=0.8,
            color=colors[: len(complexity_levels)],
            alpha=0.8,
        )

        # Styling
        p.xgrid.grid_line_color = None
        p.y_range.start = 0

        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ("Complexity", "@x"),
                ("Count", "@top"),
                ("Percentage", f"{percentages}%"),
            ]
        )
        p.add_tools(hover)

        return pn.pane.Bokeh(p)

    def view(self) -> pn.Column:
        """Return the complete statistics panel."""
        return pn.Column(
            "# System Statistics",
            self.create_overview_cards(),
            pn.Row(self.create_domain_chart(), self.create_complexity_chart()),
            sizing_mode="stretch_width",
        )


class SearchPanel(param.Parameterized):
    """Global search functionality."""

    state = param.Parameter()

    def __init__(self, state: DashboardState, **params):
        super().__init__(state=state, **params)
        self.search_input = None
        self.results_panel = None
        self.setup_components()

    def setup_components(self):
        """Setup search components."""
        self.search_input = pn.widgets.TextInput(
            name="Search", placeholder="Search files, classes, functions...", width=400
        )

        search_button = pn.widgets.Button(
            name="Search", button_type="primary", width=100
        )

        # Bind callbacks
        search_button.on_click(self.perform_search)
        self.search_input.param.watch(self.on_search_enter, "value")

        self.results_panel = pn.Column(
            "### Search Results",
            pn.pane.HTML(
                "<p>Enter a search term to find files, classes, and functions.</p>"
            ),
            sizing_mode="stretch_width",
        )

        self.search_controls = pn.Row(self.search_input, search_button)

    def on_search_enter(self, event):
        """Handle Enter key in search input."""
        if event.new and len(event.new.strip()) > 2:
            self.perform_search(None)

    def perform_search(self, event):
        """Perform the search operation."""
        search_term = self.search_input.value.strip()

        if not search_term or len(search_term) < 2:
            self.results_panel[1] = pn.pane.HTML(
                "<p>Please enter at least 2 characters to search.</p>"
            )
            return

        try:
            # Perform search
            results = self.state.db_querier.search_all(search_term, limit=50)
            self.state.search_results = results
            self.state.search_term = search_term

            # Update results panel
            self.update_results_display(results, search_term)

            logger.info(
                f"Search completed for '{search_term}', found {sum(len(v) for v in results.values())} results"
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            self.results_panel[1] = pn.pane.HTML(
                f"<p style='color: red;'>Search error: {e}</p>"
            )

    def update_results_display(self, results: Dict[str, List], search_term: str):
        """Update the results display."""
        total_results = sum(len(v) for v in results.values())

        if total_results == 0:
            self.results_panel[1] = pn.pane.HTML(
                f"<p>No results found for '{search_term}'.</p>"
            )
            return

        # Create results sections
        sections = []

        # Files section
        if results["files"]:
            files_html = f"<h4>Files ({len(results['files'])})</h4><ul>"
            for item in results["files"][:10]:  # Limit to 10 items per section
                files_html += f"<li><strong>{item['name']}</strong> - {item['path']}<br><small>{item['details']}</small></li>"
            files_html += "</ul>"
            sections.append(pn.pane.HTML(files_html))

        # Classes section
        if results["classes"]:
            classes_html = f"<h4>Classes ({len(results['classes'])})</h4><ul>"
            for item in results["classes"][:10]:
                classes_html += f"<li><strong>{item['name']}</strong> - {item['path']}<br><small>{item['details']}</small></li>"
            classes_html += "</ul>"
            sections.append(pn.pane.HTML(classes_html))

        # Functions section
        if results["functions"]:
            functions_html = f"<h4>Functions ({len(results['functions'])})</h4><ul>"
            for item in results["functions"][:10]:
                functions_html += f"<li><strong>{item['name']}</strong> - {item['path']}<br><small>{item['details']}</small></li>"
            functions_html += "</ul>"
            sections.append(pn.pane.HTML(functions_html))

        # Update results panel
        self.results_panel.clear()
        self.results_panel.append(
            f"### Search Results for '{search_term}' ({total_results} total)"
        )
        self.results_panel.extend(sections)

    def view(self) -> pn.Column:
        """Return the complete search panel."""
        return pn.Column(
            "# Search",
            self.search_controls,
            self.results_panel,
            sizing_mode="stretch_width",
        )


class AnalysisConfigPanel(param.Parameterized):
    """Configuration panel for running new analysis."""

    state = param.Parameter()

    def __init__(self, state: DashboardState, **params):
        super().__init__(state=state, **params)
        self.setup_components()

    def setup_components(self):
        """Setup configuration components."""
        # Project root input
        self.project_root_input = pn.widgets.TextInput(
            name="Project Root Path", value=str(Path.cwd()), width=500
        )

        # Include patterns
        self.include_patterns_input = pn.widgets.TextAreaInput(
            name="Include Patterns (one per line)",
            value="*.py\n*.js\n*.html\n*.css\n*.md\n*.json\n*.yml\n*.yaml",
            height=100,
            width=400,
        )

        # Exclude patterns
        self.exclude_patterns_input = pn.widgets.TextAreaInput(
            name="Exclude Patterns (one per line)",
            value="__pycache__\n*.pyc\nnode_modules\n.git\n.vscode\n*.egg-info",
            height=100,
            width=400,
        )

        # Options
        self.enable_ast_checkbox = pn.widgets.Checkbox(
            name="Enable AST Analysis (Python files)", value=True
        )

        self.calculate_complexity_checkbox = pn.widgets.Checkbox(
            name="Calculate Complexity Metrics", value=True
        )

        # Run analysis button
        self.run_button = pn.widgets.Button(
            name="Run Analysis", button_type="primary", width=200, height=50
        )

        self.run_button.on_click(self.run_analysis)

        # Status panel
        self.status_panel = pn.pane.HTML(
            "<p>Configure analysis settings and click 'Run Analysis' to populate the database.</p>"
        )

    def run_analysis(self, event):
        """Run the code analysis."""
        try:
            # Validate inputs
            project_root = Path(self.project_root_input.value)
            if not project_root.exists():
                self.status_panel.object = f"<p style='color: red;'>Error: Project root does not exist: {project_root}</p>"
                return

            # Parse patterns
            include_patterns = [
                p.strip()
                for p in self.include_patterns_input.value.split("\n")
                if p.strip()
            ]
            exclude_patterns = [
                p.strip()
                for p in self.exclude_patterns_input.value.split("\n")
                if p.strip()
            ]

            # Update status
            self.status_panel.object = "<p style='color: blue;'>Analysis started... This may take a few minutes.</p>"
            self.run_button.disabled = True

            # Import and run the populator
            from db.populate_db import DatabasePopulator

            populator = DatabasePopulator(self.state.db_querier.db_path)
            populator.create_tables()
            populator.populate_from_directory(
                project_root, include_patterns, exclude_patterns
            )

            # Refresh system stats
            self.state.refresh_system_stats()

            # Update status
            self.status_panel.object = "<p style='color: green;'>Analysis completed successfully! Database has been updated.</p>"

            logger.info("Analysis completed successfully")

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            self.status_panel.object = f"<p style='color: red;'>Analysis error: {e}</p>"

        finally:
            self.run_button.disabled = False

    def view(self) -> pn.Column:
        """Return the complete analysis configuration panel."""
        return pn.Column(
            "# Analysis Configuration",
            "Configure the parameters for analyzing your codebase and populating the database.",
            pn.Row(
                pn.Column(
                    self.project_root_input, self.include_patterns_input, width=500
                ),
                pn.Column(
                    pn.Spacer(height=50),  # Align with project root input
                    self.exclude_patterns_input,
                    width=500,
                ),
            ),
            pn.Row(self.enable_ast_checkbox, self.calculate_complexity_checkbox),
            self.run_button,
            "## Status",
            self.status_panel,
            sizing_mode="stretch_width",
        )


def create_dashboard(db_path: str = "code_intelligence.db") -> pn.Tabs:
    """Create the main dashboard with all panels."""
    # Initialize state
    state = DashboardState(db_path)

    # Create components
    file_explorer = FileExplorer(state)
    statistics_panel = StatisticsPanel(state)
    search_panel = SearchPanel(state)
    config_panel = AnalysisConfigPanel(state)

    # Create tabs
    tabs = pn.Tabs(
        ("📊 Overview", statistics_panel.view()),
        ("📁 Files", file_explorer.view()),
        ("🔍 Search", search_panel.view()),
        ("⚙️ Analysis", config_panel.view()),
        dynamic=True,
        sizing_mode="stretch_width",
    )

    return tabs
