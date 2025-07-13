#!/usr/bin/env python3
"""
Panel Dashboard Views with Pydantic-Panel Integration

This module contains all the Panel-based UI components and views for the
code intelligence dashboard. It uses Pydantic-Panel for auto-generated
forms and Panel's reactive programming model for interactivity.

All UI components are built using Python only - no JavaScript required.
"""

# Import our models and database

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import panel as pn
import param
import pydantic_panel  # Auto-registers with panel
from dashboard.components.enhanced_network_graph import EnhancedNetworkGraphComponent
from dashboard.components.enhanced_visualizations import EnhancedVisualizationComponent
from dashboard.components.modal_system import modal_manager, show_file_details_modal
from dashboard.dashboard_logging import get_logger

## Import centralized models and services
from dashboard.models.dashboard_models import FileFilterModel
from dashboard.services.database_service import DashboardDatabaseService
from dashboard.settings import DashboardSettings
from dashboard.templates.dashboard_template_service import dashboard_template_service
from db.queries import DatabaseQuerier

logger = get_logger(__name__)

from models.types import (
    AnalysisConfigForm,
    ComplexityLevel,
    DomainType,
    FileFilterForm,
    FileType,
    NetworkGraphConfigForm,
)

## Other dashboard types are imported where needed


# Configure Panel - extension is configured in app.py, don't duplicate here
# pn.extension("bokeh", "tabulator", template="material")

# Load dashboard settings once for the module
try:
    settings = DashboardSettings.from_yaml()
except Exception:
    # Fallback if settings can't be loaded
    settings = DashboardSettings()


class DashboardState(param.Parameterized):
    """Central state management for the dashboard."""

    db_querier = param.Parameter(default=None)
    current_filters = param.Dict(default={})
    selected_file_id = param.Integer(default=0, allow_None=True)
    selected_class_id = param.Integer(default=0, allow_None=True)
    selected_function_id = param.Integer(default=0, allow_None=True)
    search_term = param.String(default="")
    search_results = param.Dict(default={})
    system_stats = param.Parameter(default=None)

    # Add explicit typing for our centralized service
    db_service: DashboardDatabaseService
    settings: DashboardSettings

    def __init__(
        self,
        db_path: Optional[str] = None,
        settings_obj: Optional[DashboardSettings] = None,
        **params: Any,
    ) -> None:
        super().__init__(**params)
        self.settings = settings_obj or DashboardSettings.from_yaml()
        db_path = db_path or self.settings.db_path
        self.db_querier = DatabaseQuerier(db_path)

        # Initialize centralized database service
        self.db_service = DashboardDatabaseService(self.db_querier)

        self.refresh_system_stats()

    def refresh_system_stats(self) -> None:
        """Refresh system statistics from database."""
        try:
            self.system_stats = self.db_service.safe_get_system_stats()
        except Exception as e:
            logger.error(f"Error refreshing system stats: {e}")
            self.system_stats = None


class FileExplorer(param.Parameterized):
    """File explorer component with filtering and search."""

    state = param.ClassSelector(class_=DashboardState)

    def __init__(self, state: DashboardState, **params: Any) -> None:
        super().__init__(state=state, **params)
        self.filter_form = None
        # Create empty model - all fields are optional with None defaults
        self.filter_model = FileFilterForm(
            domain=None,
            file_type=None,
            complexity_level=None,
            min_lines=None,
            max_lines=None,
            search_term="",
        )
        self.files_table = None
        self.setup_components()

    def setup_components(self) -> None:
        """Setup filter form and files table widgets."""
        # Create filter form using Pydantic model
        self.filter_form = self.create_filter_form()

        # Create files table
        self.files_table = self.create_files_table()

    def create_filter_form(self) -> pn.Column:
        """Create the file filter form using Pydantic-Panel auto-generation."""

        # Create auto-generated form from Pydantic model using pn.panel()
        form_panel = pn.panel(self.filter_model, width=800, name="File Filters")

        # Create control buttons
        apply_button: pn.widgets.Button = pn.widgets.Button(
            name="Apply Filters", button_type="primary", width=150
        )

        clear_button: pn.widgets.Button = pn.widgets.Button(
            name="Clear Filters", button_type="light", width=150
        )

        # Bind callbacks
        def safe_apply_filters(event: Any) -> None:
            """Apply filters using values from the Pydantic model."""
            # Get the updated model from the widget's value attribute
            if hasattr(form_panel, "value"):
                model_data = getattr(form_panel, "value", None)
                if isinstance(model_data, FileFilterForm):
                    self.apply_filters_from_model(model_data)

        def safe_clear_filters(event: Any) -> None:
            """Clear all filters by resetting the Pydantic model."""
            # Reset the widget's value to a new default model
            if hasattr(form_panel, "value"):
                setattr(
                    form_panel,
                    "value",
                    FileFilterForm(
                        domain=None,
                        file_type=None,
                        complexity_level=None,
                        min_lines=None,
                        max_lines=None,
                        search_term="",
                    ),
                )
                # Apply the clear filters
                model_data = getattr(form_panel, "value", None)
                if isinstance(model_data, FileFilterForm):
                    self.apply_filters_from_model(model_data)

        apply_button.on_click(safe_apply_filters)
        clear_button.on_click(safe_clear_filters)

        return pn.Column(
            "## File Filters",
            form_panel,
            pn.Row(apply_button, clear_button),
            width=800,
        )

    def create_files_table(self) -> pn.widgets.Tabulator:
        """Create the files data table using Tabulator widget."""
        # Get initial data using centralized service
        state: DashboardState = self.state
        result = state.db_service.safe_query_files(
            limit=getattr(state.settings, "max_query_limit", 1000)
        )
        files: List[FileFilterModel] = result.data if result.success else []
        # Convert to DataFrame
        df: pd.DataFrame = self.files_to_dataframe(files)
        table: pn.widgets.Tabulator = pn.widgets.Tabulator(
            df,
            pagination="remote",
            page_size=25,
            sizing_mode="stretch_width",
            height=600,
            selectable="highlight",  # Changed from 1 to "highlight" for read-only selection
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
                ],
                "layout": "fitColumns",
                "responsiveLayout": "hide",
                "tooltips": True,
                "addRowPos": "top",
                "history": True,
                "pagination": "local",
                "paginationSize": 25,
                "movableColumns": False,  # Prevent column reordering
                "resizableRows": False,  # Prevent row resizing
                "resizableColumns": True,  # Allow column resizing
                "initialSort": [{"column": "complexity", "dir": "desc"}],
                "clipboard": False,  # Disable clipboard operations
                "downloadConfig": False,  # Disable download options
                "printConfig": False,  # Disable print options
                "editableColumns": False,  # Make table read-only
            },
        )
        table.param.watch(self.on_file_clicked, "selection")
        return table

    def files_to_dataframe(self, files: List[FileFilterModel]) -> pd.DataFrame:
        """Convert file records to DataFrame using Pydantic FileFilterModel."""
        data: List[Dict[str, Any]] = [file.model_dump() for file in files]
        return pd.DataFrame(data)

    def apply_filters(
        self,
        domain: Optional[str],
        file_type: Optional[str],
        complexity_level: Optional[str],
        min_lines: Optional[int],
        max_lines: Optional[int],
        search_term: Optional[str],
    ) -> None:
        """Apply filters and refresh the table."""
        try:
            # Convert string values back to enums
            domain_enum = DomainType(domain) if domain else None
            file_type_enum = FileType(file_type) if file_type else None
            complexity_enum = (
                ComplexityLevel(complexity_level) if complexity_level else None
            )

            # Query with filters using centralized service
            state = self.state
            assert isinstance(state, DashboardState)

            result = state.db_service.safe_query_files(
                domain=domain_enum,
                file_type=file_type_enum,
                complexity_level=complexity_enum,
                min_lines=min_lines,
                max_lines=max_lines,
                search_term=search_term,
                limit=getattr(state.settings, "max_query_limit", 1000),
            )

            files = result.data if result.success else []
            total_count = result.total_count if result.success else 0

            # Update table
            df = self.files_to_dataframe(files)
            if self.files_table:
                self.files_table.value = df

            # Update state
            if hasattr(state, "current_filters"):
                state.current_filters = {
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
            if hasattr(pn.state, "notifications") and pn.state.notifications:
                pn.state.notifications.error(f"Error applying filters: {e}")  # type: ignore[attr-defined]

    def clear_filters(self, *widgets: Any) -> None:
        """Clear all filters and reset the table."""
        try:
            # Reset widget values
            for widget in widgets:
                if hasattr(widget, "value"):
                    widget.value = (
                        None if getattr(widget, "name", "") != "Search" else ""
                    )

            # Reset table to show all files using centralized service
            state = self.state  # type: ignore[attr-defined]
            assert isinstance(state, DashboardState)

            result = state.db_service.safe_query_files(
                limit=getattr(state.settings, "max_query_limit", 1000)
            )

            files = result.data if result.success else []
            df = self.files_to_dataframe(files)
            if self.files_table:
                self.files_table.value = df

            # Clear state
            if hasattr(state, "current_filters"):
                state.current_filters = {}

            logger.info("Filters cleared")

        except Exception as e:
            logger.error(f"Error clearing filters: {e}")
            if hasattr(pn.state, "notifications") and pn.state.notifications:
                pn.state.notifications.error(f"Error clearing filters: {e}")  # type: ignore[attr-defined]

    def on_file_clicked(self, event: Any) -> None:
        """Handle file click event from Tabulator with enhanced modal interaction."""
        try:
            if event.new and len(event.new) > 0:
                selected_row: int = event.new[0]
                if self.files_table and hasattr(self.files_table, "value"):
                    value = self.files_table.value
                    file_id: Optional[int] = None
                    import pandas as pd

                    if isinstance(value, pd.DataFrame) and selected_row < len(value):
                        file_data = value.iloc[selected_row]
                        file_id = int(file_data["id"])

                        if file_id is not None:
                            state: DashboardState = self.state
                            state.selected_file_id = file_id
                            logger.info(
                                f"Selected file ID: {file_id} - {file_data.get('name', 'Unknown')}"
                            )

                            # Show file details in modal
                            file_dict = file_data.to_dict()
                            show_file_details_modal(file_dict)

                            # Update state for other components
                            if (
                                hasattr(pn.state, "notifications")
                                and pn.state.notifications
                            ):
                                pn.state.notifications.info(
                                    f"Selected: {file_data.get('name', 'Unknown')}. "
                                    f"Switch to Code Explorer tab for detailed analysis."
                                )
                        else:
                            logger.warning("No valid file ID found in selected row")
                    else:
                        logger.warning(
                            f"Invalid selection: row {selected_row}, table size: {len(value) if isinstance(value, pd.DataFrame) else 'unknown'}"
                        )
        except Exception as e:
            logger.error(f"Error handling file selection: {e}")
            if hasattr(pn.state, "notifications") and pn.state.notifications:
                pn.state.notifications.error(f"Error selecting file: {e}")

    # File details methods removed - using simplified design focused on Code Explorer tab

    def _get_complexity_color(self, complexity: float) -> str:
        """Get color for complexity score."""
        if complexity <= 10:
            return "#28a745"  # Green
        elif complexity <= 25:
            return "#ffc107"  # Yellow
        elif complexity <= 50:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red

    def _get_complexity_recommendation(self, complexity: float) -> str:
        """Get complexity recommendation HTML."""
        if complexity <= 10:
            return '<div style="color: #28a745; font-size: 0.9em;"><strong>✅ Good:</strong> This file has low complexity and should be easy to maintain.</div>'
        elif complexity <= 25:
            return '<div style="color: #856404; font-size: 0.9em;"><strong>⚠️ Moderate:</strong> Complexity is acceptable but monitor for increases.</div>'
        elif complexity <= 50:
            return '<div style="color: #fd7e14; font-size: 0.9em;"><strong>🔥 High:</strong> Consider breaking this file into smaller, more focused modules.</div>'
        else:
            return '<div style="color: #dc3545; font-size: 0.9em;"><strong>🚨 Very High:</strong> This file should be refactored immediately to improve maintainability.</div>'

    def view(self) -> pn.Column:
        """Return the complete file explorer view as a Panel Column."""
        # Create a simple single-column layout focused on the files table
        main_content = pn.Column(
            self.filter_form,
            "## Files",
            pn.pane.HTML(
                """
                <div class="usa-alert usa-alert--info dashboard-file-tip" role="region" aria-labelledby="file-tip-heading">
                    <div class="usa-alert__body">
                        <h4 class="usa-alert__heading" id="file-tip-heading">💡 Navigation Tip</h4>
                        <p class="usa-alert__text">
                            Click on any file row to select it, then switch to the <strong>Code Explorer</strong> tab for detailed analysis.
                        </p>
                    </div>
                </div>
                """,
                sizing_mode="stretch_width",
            ),
            self.files_table,
            sizing_mode="stretch_width",
        )

        return main_content

    def apply_filters_from_model(self, model: FileFilterForm) -> None:
        """Apply filters using values from the Pydantic model."""
        self.apply_filters(
            domain=model.domain.value if model.domain else None,
            file_type=model.file_type.value if model.file_type else None,
            complexity_level=(
                model.complexity_level.value if model.complexity_level else None
            ),
            min_lines=model.min_lines,
            max_lines=model.max_lines,
            search_term=model.search_term,
        )


class StatisticsPanel(param.Parameterized):
    """Statistics and analytics panel with enhanced visualizations."""

    state = param.ClassSelector(class_=DashboardState)

    def __init__(self, state: DashboardState, **params: Any) -> None:
        super().__init__(state=state, **params)
        self.enhanced_viz = EnhancedVisualizationComponent(state)

    def create_overview_cards(self) -> pn.pane.HTML:
        """Create overview statistics cards."""
        state: DashboardState = self.state
        if not state.system_stats:
            return pn.pane.HTML(
                dashboard_template_service.render_no_data_message(
                    "No statistics available"
                )
            )

        # Use template service to render stats cards
        cards_html: str = dashboard_template_service.render_stats_cards_row(
            state.system_stats
        )
        return pn.pane.HTML(cards_html)

    def create_domain_chart(self) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create modern domain distribution chart with enhanced styling."""
        return self.enhanced_viz.create_domain_distribution_chart()

    def create_complexity_chart(self) -> Union[pn.pane.HTML, pn.pane.Plotly]:
        """Create modern complexity distribution chart with enhanced styling."""
        return self.enhanced_viz.create_complexity_distribution_chart()

    def view(self) -> pn.Column:
        """Return the complete statistics panel with enhanced layout."""
        # Create header section
        header_html = """
        <div class="usa-card usa-card--header-first" style="margin-bottom: 2rem;">
            <div class="usa-card__container">
                <div class="usa-card__header">
                    <h2 class="usa-card__heading">📊 System Statistics</h2>
                    <p class="usa-card__subtitle">Comprehensive overview of your codebase metrics and analysis results</p>
                </div>
                <div class="usa-card__body">
                    <p>This dashboard provides real-time insights into your code structure, complexity patterns, and architectural health.</p>
                </div>
            </div>
        </div>
        """

        # Create charts in polished containers
        domain_chart = self.create_domain_chart()
        complexity_chart = self.create_complexity_chart()

        # Create responsive layout
        charts_row = pn.Row(
            pn.Column(
                pn.pane.HTML(
                    '<h3 style="margin: 1rem 0 0.5rem 0; color: #1b1b1b;">Domain Distribution</h3>'
                ),
                domain_chart,
                sizing_mode="stretch_width",
            ),
            pn.Column(
                pn.pane.HTML(
                    '<h3 style="margin: 1rem 0 0.5rem 0; color: #1b1b1b;">Complexity Analysis</h3>'
                ),
                complexity_chart,
                sizing_mode="stretch_width",
            ),
            sizing_mode="stretch_width",
        )

        return pn.Column(
            pn.pane.HTML(header_html, sizing_mode="stretch_width"),
            self.create_overview_cards(),
            charts_row,
            sizing_mode="stretch_width",
            margin=(0, 20),
        )


class SearchPanel(param.Parameterized):
    """Global search functionality."""

    state = param.ClassSelector(class_=DashboardState)

    def __init__(self, state: DashboardState, **params: Any) -> None:
        super().__init__(state=state, **params)
        self.search_input = None
        self.results_panel = None
        self.search_controls = None
        self.setup_components()

    def setup_components(self) -> None:
        """Setup search input, button, and results panel widgets."""
        self.search_input = pn.widgets.TextInput(
            name="Search",
            placeholder="Search files, classes, and functions...",
            width=400,
            css_classes=["usa-input"],
        )

        search_button = pn.widgets.Button(
            name="Search",
            button_type="primary",
            width=100,
            css_classes=["usa-button"],
        )

        # Bind callbacks
        search_button.on_click(self.perform_search)
        if self.search_input:
            self.search_input.param.watch(self.on_search_enter, "value")

        self.results_panel = pn.Column(
            "### Search Results",
            pn.pane.HTML(
                "<p>Enter a search term to find files, classes, and functions.</p>"
            ),
            sizing_mode="stretch_width",
        )

        self.search_controls = pn.Row(self.search_input, search_button)

    def on_search_enter(self, event: Any) -> None:
        """Handle Enter key in search input widget."""
        if event.new and len(str(event.new).strip()) > 2:
            self.perform_search(None)

    def perform_search(self, event: Any) -> None:
        """Perform the search operation and update results panel."""
        if not self.search_input or not self.results_panel:
            return

        search_term = str(self.search_input.value).strip()

        if not search_term or len(search_term) < 2:
            self.results_panel[1] = pn.pane.HTML(
                dashboard_template_service.render_status_message(
                    "Please enter at least 2 characters to search.", "info"
                )
            )
            return

        try:
            # Perform search using centralized service
            results = self.state.db_service.safe_search_all(search_term, limit=50)
            self.state.search_results = results
            self.state.search_term = search_term

            # Update results panel
            results_html = dashboard_template_service.render_search_results(
                results, search_term
            )
            self.results_panel[1] = pn.pane.HTML(results_html)

            total_results = (
                sum(len(v) if isinstance(v, list) else 0 for v in results.values())
                if isinstance(results, dict)
                else 0
            )
            logger.info(
                f"Search completed for '{search_term}', found {total_results} results"
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            if self.results_panel:
                self.results_panel[1] = pn.pane.HTML(
                    f"<p style='color: red;'>Search error: {e}</p>"
                )

    def update_results_display(self, results: Dict[str, Any], search_term: str) -> None:
        """Update the results display panel with search results."""
        if not self.results_panel:
            return

        total_results = (
            sum(len(v) if isinstance(v, list) else 0 for v in results.values())
            if isinstance(results, dict)
            else 0
        )

        if total_results == 0:
            self.results_panel[1] = pn.pane.HTML(
                f"<p>No results found for '{search_term}'.</p>"
            )
            return

        # Create results sections
        sections = []

        # Files section
        if "files" in results and isinstance(results["files"], list):
            files_html = f"<h4>Files ({len(results['files'])})</h4><ul>"
            for item in results["files"][:10]:  # Limit to 10 items per section
                name = (
                    item.get("name", "Unknown") if isinstance(item, dict) else str(item)
                )
                path = item.get("path", "") if isinstance(item, dict) else ""
                details = item.get("details", "") if isinstance(item, dict) else ""
                files_html += f"<li><strong>{name}</strong> - {path}<br><small>{details}</small></li>"
            files_html += "</ul>"
            sections.append(pn.pane.HTML(files_html))

        # Classes section
        if "classes" in results and isinstance(results["classes"], list):
            classes_html = f"<h4>Classes ({len(results['classes'])})</h4><ul>"
            for item in results["classes"][:10]:
                name = (
                    item.get("name", "Unknown") if isinstance(item, dict) else str(item)
                )
                path = item.get("path", "") if isinstance(item, dict) else ""
                details = item.get("details", "") if isinstance(item, dict) else ""
                classes_html += f"<li><strong>{name}</strong> - {path}<br><small>{details}</small></li>"
            classes_html += "</ul>"
            sections.append(pn.pane.HTML(classes_html))

        # Functions section
        if "functions" in results and isinstance(results["functions"], list):
            functions_html = f"<h4>Functions ({len(results['functions'])})</h4><ul>"
            for item in results["functions"][:10]:
                name = (
                    item.get("name", "Unknown") if isinstance(item, dict) else str(item)
                )
                path = item.get("path", "") if isinstance(item, dict) else ""
                details = item.get("details", "") if isinstance(item, dict) else ""
                functions_html += f"<li><strong>{name}</strong> - {path}<br><small>{details}</small></li>"
            functions_html += "</ul>"
            sections.append(pn.pane.HTML(functions_html))

        # Update results panel
        self.results_panel.clear()
        self.results_panel.append(
            f"### Search Results for '{search_term}' ({total_results} total)"
        )
        self.results_panel.extend(sections)

    def view(self) -> pn.Column:
        """Return the complete search panel as a Panel Column."""
        return pn.Column(
            pn.pane.HTML(
                """
                <div class="usa-card">
                    <div class="usa-card__container">
                        <div class="usa-card__header">
                            <h2 class="usa-card__heading">🔍 Global Search</h2>
                        </div>
                        <div class="usa-card__body">
                            <p>Search across files, classes, and functions in your codebase.</p>
                        </div>
                    </div>
                </div>
                """,
                sizing_mode="stretch_width",
            ),
            self.search_controls,
            self.results_panel,
            sizing_mode="stretch_width",
        )


class AnalysisConfigPanel(param.Parameterized):
    """Configuration panel for running new analysis using Pydantic-Panel."""

    state = param.ClassSelector(class_=DashboardState)

    def __init__(self, state: DashboardState, **params: Any) -> None:
        super().__init__(state=state, **params)
        self.config_model = None
        self.config_form = None
        self.run_button = None
        self.status_panel = None
        self.setup_components()

    def setup_components(self) -> None:
        """Setup configuration form using AnalysisConfigForm and pydantic-panel."""
        from dashboard.settings import DashboardSettings

        config = DashboardSettings()

        # Create AnalysisConfigForm model with defaults
        self.config_model = AnalysisConfigForm(
            project_root=str(Path.cwd()),
            include_patterns=[
                "*.py",
                "*.js",
                "*.html",
                "*.css",
                "*.md",
                "*.json",
                "*.yml",
                "*.yaml",
            ],
            exclude_patterns=getattr(
                config, "exclude_dirs", ["__pycache__", "*.pyc", "node_modules", ".git"]
            ),
            max_file_size=1024 * 1024,  # 1MB
            enable_ast_analysis=True,
            calculate_complexity=True,
        )

        # Create auto-generated form from Pydantic model
        self.config_form = pn.panel(
            self.config_model, width=800, name="Analysis Configuration"
        )

        # Run analysis button
        self.run_button = pn.widgets.Button(
            name="Run Analysis", button_type="primary", width=200, height=50
        )

        self.run_button.on_click(self.run_analysis)

        # Status panel
        self.status_panel = pn.pane.HTML(
            dashboard_template_service.render_status_message(
                "Configure analysis settings and click 'Run Analysis' to populate the database.",
                "info",
            )
        )

    def run_analysis(self, event: Any) -> None:
        """Run the code analysis using values from the Pydantic form."""
        if not all([self.config_form, self.run_button, self.status_panel]):
            return

        try:
            # Get the current form values from the Pydantic model
            if hasattr(self.config_form, "value"):
                config_data = getattr(self.config_form, "value", None)
                if not isinstance(config_data, AnalysisConfigForm):
                    self.status_panel.object = (
                        "<p style='color: red;'>Error: Invalid configuration data</p>"
                    )
                    return
            else:
                self.status_panel.object = (
                    "<p style='color: red;'>Error: Configuration form not available</p>"
                )
                return

            # Validate project root
            project_root = Path(config_data.project_root)
            if not project_root.exists():
                self.status_panel.object = f"<p style='color: red;'>Error: Project root does not exist: {project_root}</p>"
                return

            # Get patterns from the model
            include_patterns = config_data.include_patterns
            exclude_patterns = config_data.exclude_patterns

            # Update status
            self.status_panel.object = "<p style='color: blue;'>Analysis started... This may take a few minutes.</p>"
            self.run_button.disabled = True

            # Import and run the populator
            from db.populate_db import DatabasePopulator

            populator = DatabasePopulator(
                getattr(self.state.db_querier, "db_path", "code_intelligence.db")
            )
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
            if self.status_panel:
                self.status_panel.object = (
                    f"<p style='color: red;'>Analysis error: {e}</p>"
                )

        finally:
            if self.run_button:
                self.run_button.disabled = False

    def view(self) -> pn.Column:
        """Return the complete analysis configuration panel using Pydantic-Panel auto-generated form."""
        return pn.Column(
            "# Analysis Configuration",
            "Configure the parameters for analyzing your codebase and populating the database.",
            self.config_form,
            self.run_button,
            "## Status",
            self.status_panel,
            sizing_mode="stretch_width",
        )


def create_dashboard(db_path: str = "code_intelligence.db") -> pn.Tabs:
    """Create the main dashboard with all panels."""
    logger.info(f"Creating dashboard with database: {db_path}")

    # Initialize state
    state = DashboardState(db_path)

    # Verify database connectivity
    try:
        files_result = state.db_service.safe_query_files(limit=1)
        if files_result.success:
            logger.info(
                f"Database connected successfully, found {len(files_result.data)} files"
            )
        else:
            logger.warning(f"Database query failed: {files_result.error}")
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}")

    # Import advanced components
    try:
        from dashboard.components.architecture_analysis import (
            ArchitectureAnalysisComponent,
        )
        from dashboard.components.class_diagrams import ClassDiagramComponent
        from dashboard.components.code_explorer import CodeExplorerComponent
        from dashboard.components.complexity_analysis import ComplexityAnalysisComponent
        from dashboard.components.network_graph import NetworkGraphComponent
        from dashboard.components.relationship_analysis import (
            RelationshipAnalysisComponent,
        )

        # Create basic components
        file_explorer = FileExplorer(state)
        statistics_panel = StatisticsPanel(state)
        search_panel = SearchPanel(state)
        config_panel = AnalysisConfigPanel(state)

        # Create enhanced components
        enhanced_network_graph = EnhancedNetworkGraphComponent(state)
        network_graph = NetworkGraphComponent(state)  # Keep as fallback
        class_diagrams = ClassDiagramComponent(state)
        complexity_analysis = ComplexityAnalysisComponent(state)
        relationship_analysis = RelationshipAnalysisComponent(state)
        code_explorer = CodeExplorerComponent(state)
        architecture_analysis = ArchitectureAnalysisComponent(state)

        # Create tabs with enhanced functionality and modern styling
        tabs = pn.Tabs(
            ("📊 Overview", statistics_panel.view()),
            ("📁 Files", file_explorer.view()),
            ("🔍 Code Explorer", code_explorer.view()),
            ("🌐 Network Graph", enhanced_network_graph.create_network_visualization()),
            ("🏗️ Class Diagrams", class_diagrams.view()),
            ("📈 Complexity Analysis", complexity_analysis.view()),
            ("🔗 Relationships", relationship_analysis.view()),
            ("🏛️ Architecture", architecture_analysis.view()),
            ("🔍 Search", search_panel.view()),
            ("⚙️ Analysis", config_panel.view()),
            dynamic=True,
            sizing_mode="stretch_width",
            tabs_location="above",
            margin=(0, 20),
        )

        logger.info("Created enhanced dashboard with all advanced components")

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(
            f"Could not import advanced components: {str(e)}. Full traceback:\n{error_details}. Using basic dashboard."
        )

        # Try basic components, with further fallback if needed
        try:
            file_explorer = FileExplorer(state)
            statistics_panel = StatisticsPanel(state)
            search_panel = SearchPanel(state)
            config_panel = AnalysisConfigPanel(state)

            tabs = pn.Tabs(
                ("📊 Overview", statistics_panel.view()),
                ("📁 Files", file_explorer.view()),
                ("🔍 Search", search_panel.view()),
                ("⚙️ Analysis", config_panel.view()),
                dynamic=True,
                sizing_mode="stretch_width",
            )
        except Exception as basic_error:
            logger.error(
                f"Even basic components failed: {basic_error}. Using minimal dashboard."
            )
            # Ultra-minimal fallback
            tabs = pn.Tabs(
                (
                    "📊 Overview",
                    pn.pane.HTML(
                        f"""
                    <div style="padding: 20px;">
                        <h2>🔍 Code Intelligence Dashboard</h2>
                        <p>Database: {db_path}</p>
                        <p>Status: Connected with {len(state.db_service.safe_query_files(limit=1).data) if state.db_service.safe_query_files(limit=1).success else 0} files</p>
                        <div style="color: orange;">
                            <h3>Component Loading Issues</h3>
                            <p>Advanced components: {str(e)}</p>
                            <p>Basic components: {str(basic_error)}</p>
                        </div>
                    </div>
                """
                    ),
                ),
                ("📁 Files", pn.pane.Markdown("File explorer temporarily unavailable")),
                ("� Search", pn.pane.Markdown("Search temporarily unavailable")),
                dynamic=True,
                sizing_mode="stretch_width",
            )

    return tabs
