#!/usr/bin/env python3
"""
Interactive Code Explorer Component

This module provides an interactive code exploration interface with detailed
file analysis, cross-references, and navigation capabilities.
"""

import ast
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
import panel as pn
import param
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20
from bokeh.plotting import figure

logger = logging.getLogger(__name__)


class CodeExplorerComponent(param.Parameterized):
    """Interactive code explorer with detailed file analysis."""

    selected_file_id = param.Integer(default=0, allow_None=True)
    selected_class_id = param.Integer(default=0, allow_None=True)
    selected_function_id = param.Integer(default=0, allow_None=True)
    show_source_code = param.Boolean(default=False)

    def __init__(self, state: Any, **params: Any) -> None:
        super().__init__(**params)
        self.state = state
        self.current_file: Optional[Any] = None
        self.current_classes: List[Any] = []
        self.current_functions: List[Any] = []
        self.current_relationships: List[Any] = []

        # Watch for state changes
        if hasattr(state, "param") and hasattr(state.param, "watch"):
            state.param.watch(self._on_state_file_selected, "selected_file_id")

    def _on_state_file_selected(self, event):
        """Handle file selection from global state."""
        if event.new and event.new != self.selected_file_id:
            self.selected_file_id = event.new
            self.load_file_details(event.new)

    def load_file_details(self, file_id: Any) -> None:
        """Load detailed information for a specific file."""
        try:
            # Get file information
            self.current_file = getattr(
                self.state.db_querier, "get_file_by_id", lambda x: None
            )(file_id)
            if not self.current_file:
                return

            # Get classes in this file
            all_classes_result = getattr(
                self.state.db_querier, "get_all_classes", lambda: ([], 0)
            )()
            all_classes = (
                all_classes_result[0]
                if isinstance(all_classes_result, tuple)
                else all_classes_result
            )
            self.current_classes = [
                cls
                for cls in (all_classes or [])
                if getattr(cls, "file_id", None) == file_id
            ]

            # Get functions in this file
            all_functions_result = getattr(
                self.state.db_querier, "get_all_functions", lambda: ([], 0)
            )()
            all_functions = (
                all_functions_result[0]
                if isinstance(all_functions_result, tuple)
                else all_functions_result
            )
            self.current_functions = [
                func
                for func in (all_functions or [])
                if getattr(func, "file_id", None) == file_id
            ]

            # Get relationships involving this file
            all_relationships = getattr(
                self.state.db_querier, "get_all_relationships", lambda: []
            )()
            self.current_relationships = [
                rel
                for rel in (all_relationships or [])
                if (
                    getattr(rel, "source_type", None) == "file"
                    and getattr(rel, "source_id", None) == file_id
                )
                or (
                    getattr(rel, "target_type", None) == "file"
                    and getattr(rel, "target_id", None) == file_id
                )
            ]

            logger.info(
                f"Loaded details for file: {getattr(self.current_file, 'name', 'Unknown')}"
            )

        except Exception as e:
            logger.error(f"Error loading file details: {e}")
            self.current_file = None
            self.current_classes = []
            self.current_functions = []
            self.current_relationships = []

    def create_file_overview(self) -> Union[pn.Column, pn.pane.HTML]:
        """Create file overview panel."""
        if not self.current_file:
            return pn.pane.HTML("<p>No file selected</p>")

        file = self.current_file

        # Calculate additional metrics
        avg_function_complexity = (
            sum(f.complexity for f in self.current_functions)
            / len(self.current_functions)
            if self.current_functions
            else 0
        )

        # Determine file health status
        health_score = 100
        health_issues = []

        if file.complexity > 50:
            health_score -= 30
            health_issues.append("High complexity")
        if file.lines_of_code > 1000:
            health_score -= 20
            health_issues.append("Large file")
        if len(self.current_functions) > 20:
            health_score -= 15
            health_issues.append("Too many functions")
        if avg_function_complexity > 10:
            health_score -= 15
            health_issues.append("Complex functions")

        health_color = (
            "#28a745"
            if health_score >= 80
            else "#ffc107" if health_score >= 60 else "#dc3545"
        )
        health_status = (
            "Excellent"
            if health_score >= 80
            else "Good" if health_score >= 60 else "Needs Attention"
        )

        overview_html = f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <h2 style="margin: 0; color: #333;">{file.name}</h2>
                    <p style="margin: 5px 0 0 0; color: #666; font-family: monospace;">{file.path}</p>
                </div>
                <div style="text-align: center;">
                    <div style="background: {health_color}; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold;">
                        {health_status}
                    </div>
                    <div style="font-size: 24px; font-weight: bold; color: {health_color}; margin-top: 5px;">
                        {health_score}/100
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #007bff;">Domain</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.domain.value.title()}</p>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #28a745;">Lines of Code</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.lines_of_code:,}</p>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #ffc107;">Complexity</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.complexity}</p>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #17a2b8;">Classes</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.classes_count}</p>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #6f42c1;">Functions</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.functions_count}</p>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: #e83e8c;">Imports</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{file.imports_count}</p>
                </div>
            </div>
            
            {f'''
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">⚠️ Health Issues</h4>
                <ul style="margin: 0; color: #856404;">
                    {"".join(f"<li>{issue}</li>" for issue in health_issues)}
                </ul>
            </div>
            ''' if health_issues else ''}
        </div>
        """

        return pn.pane.HTML(overview_html)

    def create_classes_panel(self) -> pn.Column:
        """Create classes analysis panel."""
        if not self.current_classes:
            return pn.pane.HTML("<p>No classes found in this file</p>")

        classes_html = """
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">🏗️ Classes</h3>
        """

        for cls in self.current_classes:
            # Get methods for this class
            class_methods = [f for f in self.current_functions if f.class_id == cls.id]

            # Calculate class metrics
            total_complexity = sum(m.complexity for m in class_methods)
            avg_complexity = (
                total_complexity / len(class_methods) if class_methods else 0
            )

            # Class type indicators
            indicators = []
            if cls.is_pydantic_model:
                indicators.append(
                    '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Pydantic</span>'
                )
            if cls.base_classes:
                indicators.append(
                    '<span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Inherits</span>'
                )
            if any(
                m.name.startswith("__") and m.name.endswith("__") for m in class_methods
            ):
                indicators.append(
                    '<span style="background: #6f42c1; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Magic Methods</span>'
                )

            classes_html += f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 15px 0; background: #fafafa;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #333;">{cls.name}</h4>
                    <div>{' '.join(indicators)}</div>
                </div>
                
                {f'<p style="margin: 5px 0; color: #666;"><strong>Base Classes:</strong> {", ".join(cls.base_classes)}</p>' if cls.base_classes else ''}
                {f'<p style="margin: 5px 0; color: #666; font-style: italic;">"{getattr(cls, "docstring", "")}"</p>' if getattr(cls, "docstring", "") else ''}
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 10px 0;">
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong>{len(class_methods)}</strong><br>
                        <small>Methods</small>
                    </div>
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong>{total_complexity}</strong><br>
                        <small>Total Complexity</small>
                    </div>
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong>{avg_complexity:.1f}</strong><br>
                        <small>Avg Complexity</small>
                    </div>
                </div>
                
                {f'''
                <div style="margin-top: 15px;">
                    <h5 style="margin: 0 0 10px 0; color: #555;">Methods:</h5>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px;">
                        {"".join(f'''
                        <div style="background: white; padding: 8px; border-radius: 4px; border-left: 3px solid {"#dc3545" if m.complexity > 10 else "#28a745" if m.complexity < 5 else "#ffc107"};">
                            <strong>{m.name}</strong>
                            <br><small>Complexity: {m.complexity}, Params: {m.parameters_count}</small>
                        </div>
                        ''' for m in class_methods)}
                    </div>
                </div>
                ''' if class_methods else ''}
            </div>
            """

        classes_html += "</div>"
        return pn.pane.HTML(classes_html)

    def create_functions_panel(self) -> pn.Column:
        """Create functions analysis panel."""
        if not self.current_functions:
            return pn.pane.HTML("<p>No functions found in this file</p>")

        # Separate methods from standalone functions
        standalone_functions = [f for f in self.current_functions if not f.class_id]

        if not standalone_functions:
            return pn.pane.HTML("<p>No standalone functions found in this file</p>")

        functions_html = """
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">⚙️ Functions</h3>
        """

        # Sort functions by complexity
        sorted_functions = sorted(
            standalone_functions, key=lambda x: x.complexity, reverse=True
        )

        for func in sorted_functions:
            # Function type indicators
            indicators = []
            if func.is_async:
                indicators.append(
                    '<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Async</span>'
                )
            if func.name.startswith("_"):
                indicators.append(
                    '<span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Private</span>'
                )
            if func.complexity > 10:
                indicators.append(
                    '<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Complex</span>'
                )
            elif func.complexity < 3:
                indicators.append(
                    '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Simple</span>'
                )

            # Complexity color
            complexity_color = (
                "#dc3545"
                if func.complexity > 10
                else "#ffc107" if func.complexity > 5 else "#28a745"
            )

            functions_html += f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 15px 0; background: #fafafa;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #333;">{func.name}()</h4>
                    <div>{' '.join(indicators)}</div>
                </div>
                
                {f'<p style="margin: 5px 0; color: #666; font-style: italic;">"{getattr(func, "docstring", "")}"</p>' if getattr(func, "docstring", "") else ''}
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 10px 0;">
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong style="color: {complexity_color};">{func.complexity}</strong><br>
                        <small>Complexity</small>
                    </div>
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong>{func.parameters_count}</strong><br>
                        <small>Parameters</small>
                    </div>
                    <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                        <strong>{func.line_number}</strong><br>
                        <small>Line #</small>
                    </div>
                </div>
            </div>
            """

        functions_html += "</div>"
        return pn.pane.HTML(functions_html)

    def create_relationships_panel(self) -> pn.Column:
        """Create relationships analysis panel."""
        if not self.current_relationships:
            return pn.pane.HTML("<p>No relationships found for this file</p>")

        # Get classes and functions in current file
        current_file_classes = [cls.id for cls in self.current_classes]
        current_file_functions = [func.id for func in self.current_functions]

        # Group relationships by type - find relationships involving entities in current file
        incoming = [
            r
            for r in self.current_relationships
            if (
                (r.target_type == "class" and r.target_id in current_file_classes)
                or (
                    r.target_type == "function"
                    and r.target_id in current_file_functions
                )
            )
        ]
        outgoing = [
            r
            for r in self.current_relationships
            if (
                (r.source_type == "class" and r.source_id in current_file_classes)
                or (
                    r.source_type == "function"
                    and r.source_id in current_file_functions
                )
            )
        ]

        # Get file lookup for names
        all_files, _ = self.state.db_querier.get_all_files(limit=1000)
        file_lookup = {f.id: f for f in all_files}

        relationships_html = f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">🔗 Relationships</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4 style="color: #28a745;">📥 Incoming Dependencies ({len(incoming)})</h4>
                    <div style="max-height: 300px; overflow-y: auto;">
        """

        # Group incoming by relationship type
        incoming_by_type = {}
        for rel in incoming:
            rel_type = rel.relationship_type.value
            if rel_type not in incoming_by_type:
                incoming_by_type[rel_type] = []
            incoming_by_type[rel_type].append(rel)

        for rel_type, rels in incoming_by_type.items():
            relationships_html += f"""
                        <div style="margin: 10px 0;">
                            <h5 style="color: #666; margin: 5px 0;">{rel_type.title()} ({len(rels)})</h5>
            """
            for rel in rels[:5]:  # Show top 5
                # Get source file based on relationship type
                source_file = None
                if rel.source_type == "class":
                    source_class = next(
                        (
                            cls
                            for cls in self.state.db_querier.get_all_classes()
                            if cls.id == rel.source_id
                        ),
                        None,
                    )
                    if source_class:
                        source_file = file_lookup.get(source_class.file_id)
                elif rel.source_type == "function":
                    source_function = next(
                        (
                            func
                            for func in self.state.db_querier.get_all_functions()
                            if func.id == rel.source_id
                        ),
                        None,
                    )
                    if source_function:
                        source_file = file_lookup.get(source_function.file_id)

                if source_file:
                    relationships_html += f"""
                            <div style="background: #f8f9fa; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #28a745;">
                                <strong>{source_file.name}</strong><br>
                                <small style="color: #666;">{source_file.path}</small>
                                {f'<br><small>Entity: {rel.source_name} ({rel.source_type})</small>' if rel.source_name else ''}
                            </div>
                    """
            if len(rels) > 5:
                relationships_html += (
                    f"<small style='color: #666;'>... and {len(rels) - 5} more</small>"
                )
            relationships_html += "</div>"

        relationships_html += """
                    </div>
                </div>
                <div>
                    <h4 style="color: #dc3545;">📤 Outgoing Dependencies ({len(outgoing)})</h4>
                    <div style="max-height: 300px; overflow-y: auto;">
        """

        # Group outgoing by relationship type
        outgoing_by_type = {}
        for rel in outgoing:
            rel_type = rel.relationship_type.value
            if rel_type not in outgoing_by_type:
                outgoing_by_type[rel_type] = []
            outgoing_by_type[rel_type].append(rel)

        for rel_type, rels in outgoing_by_type.items():
            relationships_html += f"""
                        <div style="margin: 10px 0;">
                            <h5 style="color: #666; margin: 5px 0;">{rel_type.title()} ({len(rels)})</h5>
            """
            for rel in rels[:5]:  # Show top 5
                target_file = file_lookup.get(rel.target_file_id)
                if target_file:
                    relationships_html += f"""
                            <div style="background: #f8f9fa; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #dc3545;">
                                <strong>{target_file.name}</strong><br>
                                <small style="color: #666;">{target_file.path}</small>
                                {f'<br><small>Entity: {rel.target_entity_name}</small>' if rel.target_entity_name else ''}
                            </div>
                    """
            if len(rels) > 5:
                relationships_html += (
                    f"<small style='color: #666;'>... and {len(rels) - 5} more</small>"
                )
            relationships_html += "</div>"

        relationships_html += """
                    </div>
                </div>
            </div>
        </div>
        """

        return pn.pane.HTML(relationships_html)

    def create_file_selector(self) -> pn.Column:
        """Create file selection interface."""
        # Get all files for selection
        files, _ = self.state.db_querier.get_all_files(limit=1000)

        # Create file options grouped by domain
        file_options = []
        files_by_domain = {}
        for file in files:
            domain = file.domain.value
            if domain not in files_by_domain:
                files_by_domain[domain] = []
            files_by_domain[domain].append(file)

        # Create hierarchical options
        for domain in sorted(files_by_domain.keys()):
            file_options.append((f"--- {domain.upper()} ---", None))
            for file in sorted(files_by_domain[domain], key=lambda x: x.name):
                display_name = f"  {file.name} ({file.complexity})"
                file_options.append((display_name, file.id))

        file_select = pn.widgets.Select(
            name="Select File to Explore", options=file_options, width=400, height=50
        )

        # Create detail panels (initially empty)
        self.overview_pane = pn.pane.HTML("<p>Select a file to view details</p>")
        self.classes_pane = pn.pane.HTML("<p>Select a file to view classes</p>")
        self.functions_pane = pn.pane.HTML("<p>Select a file to view functions</p>")
        self.relationships_pane = pn.pane.HTML(
            "<p>Select a file to view relationships</p>"
        )

        def update_file_details(event):
            if event.new and event.new is not None:
                self.selected_file_id = event.new
                self.load_file_details(event.new)

                # Update all panels - handle both HTML panes and other panel types
                try:
                    overview_content = self.create_file_overview()
                    if hasattr(overview_content, "object"):
                        self.overview_pane.object = overview_content.object
                    else:
                        self.overview_pane.object = str(overview_content)

                    classes_content = self.create_classes_panel()
                    if hasattr(classes_content, "object"):
                        self.classes_pane.object = classes_content.object
                    else:
                        self.classes_pane.object = str(classes_content)

                    functions_content = self.create_functions_panel()
                    if hasattr(functions_content, "object"):
                        self.functions_pane.object = functions_content.object
                    else:
                        self.functions_pane.object = str(functions_content)

                    relationships_content = self.create_relationships_panel()
                    if hasattr(relationships_content, "object"):
                        self.relationships_pane.object = relationships_content.object
                    else:
                        self.relationships_pane.object = str(relationships_content)

                except Exception as e:
                    logger.error(f"Error updating file details panels: {e}")
                    self.overview_pane.object = (
                        f"<p>Error loading file details: {e}</p>"
                    )
                    self.classes_pane.object = f"<p>Error loading classes: {e}</p>"
                    self.functions_pane.object = f"<p>Error loading functions: {e}</p>"
                    self.relationships_pane.object = (
                        f"<p>Error loading relationships: {e}</p>"
                    )

        file_select.param.watch(update_file_details, "value")

        # If a file is already selected in the global state, set it as the default
        if self.state.selected_file_id and self.state.selected_file_id != 0:
            # Find the file in our options and set it as selected
            for display_name, file_id in file_options:
                if file_id == self.state.selected_file_id:
                    file_select.value = file_id
                    # Trigger the update manually
                    self.load_file_details(file_id)
                    update_file_details(type("Event", (), {"new": file_id})())
                    break

        return pn.Column("## File Explorer", file_select, sizing_mode="stretch_width")

    def view(self) -> pn.Column:
        """Return the complete code explorer view."""
        # Create header with USWDS styling
        header = pn.pane.HTML(
            """
            <div class="usa-card">
                <div class="usa-card__container">
                    <div class="usa-card__header">
                        <h2 class="usa-card__heading">🔍 Code Explorer</h2>
                    </div>
                    <div class="usa-card__body">
                        <p>Select a file to explore its structure, classes, functions, and relationships.</p>
                    </div>
                </div>
            </div>
            """,
            sizing_mode="stretch_width",
        )

        # Create file selector
        file_selector = self.create_file_selector()

        # Create tabs for different views
        detail_tabs = pn.Tabs(
            ("📋 Overview", self.overview_pane),
            ("🏗️ Classes", self.classes_pane),
            ("⚙️ Functions", self.functions_pane),
            ("🔗 Relationships", self.relationships_pane),
            dynamic=True,
            sizing_mode="stretch_width",
        )

        return pn.Column(
            header, file_selector, detail_tabs, sizing_mode="stretch_width"
        )
