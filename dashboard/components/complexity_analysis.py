#!/usr/bin/env python3
"""
Code Complexity and Quality Analysis Component

This module provides comprehensive code quality analysis including complexity metrics,
code smells detection, maintainability indices, and quality trends.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import panel as pn
import param
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.palettes import Category20, RdYlBu11, Spectral11, Viridis256
from bokeh.plotting import figure
from bokeh.transform import linear_cmap

logger = logging.getLogger(__name__)


class ComplexityAnalysisComponent(param.Parameterized):
    """Component for analyzing code complexity and quality metrics."""

    analysis_scope = param.String(default="all")  # all, file, domain, class
    complexity_threshold = param.Integer(default=10)
    show_trends = param.Boolean(default=True)

    def __init__(self, state, **params):
        super().__init__(**params)
        self.state = state
        self.complexity_data = None
        self.quality_metrics = None
        self.load_complexity_data()

    def load_complexity_data(self):
        """Load and process complexity data from database."""
        try:
            # Get files with complexity data
            files, _ = self.state.db_querier.get_all_files(limit=1000)
            functions, _ = self.state.db_querier.get_all_functions()
            classes, _ = self.state.db_querier.get_all_classes()

            # Process file-level complexity
            self.complexity_data = []
            for file in files:
                file_functions = [f for f in functions if f.file_id == file.id]
                file_classes = [c for c in classes if c.file_id == file.id]

                # Calculate derived metrics
                avg_function_complexity = (
                    sum(f.complexity for f in file_functions) / len(file_functions)
                    if file_functions
                    else 0
                )

                max_function_complexity = (
                    max(f.complexity for f in file_functions) if file_functions else 0
                )

                # Maintainability Index (simplified version)
                # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
                # Simplified: MI = 100 - complexity_factor - size_factor
                complexity_factor = min(50, file.complexity * 2)
                size_factor = min(30, file.lines_of_code / 50)
                maintainability_index = max(0, 100 - complexity_factor - size_factor)

                # Technical debt estimation (in hours)
                # Based on complexity and size
                technical_debt = (file.complexity * 0.5) + (file.lines_of_code * 0.01)

                complexity_info = {
                    "file_id": file.id,
                    "name": file.name,
                    "path": file.path,
                    "domain": file.domain.value,
                    "file_type": file.file_type.value,
                    "lines_of_code": file.lines_of_code,
                    "complexity": file.complexity,
                    "complexity_level": file.complexity_level.value,
                    "classes_count": file.classes_count,
                    "functions_count": file.functions_count,
                    "avg_function_complexity": avg_function_complexity,
                    "max_function_complexity": max_function_complexity,
                    "maintainability_index": maintainability_index,
                    "technical_debt_hours": technical_debt,
                    "quality_score": self.calculate_quality_score(
                        file, file_functions, file_classes
                    ),
                }
                self.complexity_data.append(complexity_info)

            # Calculate quality metrics
            self.calculate_quality_metrics()

            logger.info(f"Loaded complexity data for {len(self.complexity_data)} files")

        except Exception as e:
            logger.error(f"Error loading complexity data: {e}")
            self.complexity_data = []

    def calculate_quality_score(self, file, functions, classes) -> float:
        """Calculate overall quality score for a file (0-100)."""
        score = 100.0

        # Penalize high complexity
        if file.complexity > 50:
            score -= 30
        elif file.complexity > 20:
            score -= 15
        elif file.complexity > 10:
            score -= 5

        # Penalize large files
        if file.lines_of_code > 1000:
            score -= 20
        elif file.lines_of_code > 500:
            score -= 10

        # Penalize files with too many functions/classes
        if file.functions_count > 20:
            score -= 10
        if file.classes_count > 10:
            score -= 10

        # Bonus for good structure
        if functions:
            avg_func_complexity = sum(f.complexity for f in functions) / len(functions)
            if avg_func_complexity < 5:
                score += 5

        # Bonus for documentation (if available)
        documented_functions = sum(
            1 for f in functions if getattr(f, "docstring", None)
        )
        if functions and documented_functions / len(functions) > 0.5:
            score += 10

        return max(0, min(100, score))

    def calculate_quality_metrics(self):
        """Calculate overall quality metrics for the codebase."""
        if not self.complexity_data:
            self.quality_metrics = {}
            return

        df = pd.DataFrame(self.complexity_data)

        self.quality_metrics = {
            "total_files": len(df),
            "avg_complexity": df["complexity"].mean(),
            "avg_maintainability": df["maintainability_index"].mean(),
            "avg_quality_score": df["quality_score"].mean(),
            "total_technical_debt": df["technical_debt_hours"].sum(),
            "high_complexity_files": len(df[df["complexity"] > 20]),
            "low_maintainability_files": len(df[df["maintainability_index"] < 50]),
            "files_by_domain": df.groupby("domain").size().to_dict(),
            "complexity_by_domain": df.groupby("domain")["complexity"].mean().to_dict(),
            "quality_by_domain": df.groupby("domain")["quality_score"].mean().to_dict(),
        }

    def create_complexity_heatmap(self) -> pn.pane.Bokeh:
        """Create a heatmap showing complexity across files and domains."""
        if not self.complexity_data:
            return pn.pane.HTML("<p>No complexity data available</p>")

        df = pd.DataFrame(self.complexity_data)

        # Create pivot table for heatmap
        # Group files by domain and complexity level
        heatmap_data = (
            df.groupby(["domain", "complexity_level"]).size().reset_index(name="count")
        )

        # Create figure
        p = figure(
            width=800,
            height=400,
            title="Complexity Distribution Heatmap",
            x_range=list(df["domain"].unique()),
            y_range=["low", "medium", "high", "very_high"],
            tools="hover,save",
            toolbar_location="above",
        )

        # Prepare data for heatmap
        domains = list(df["domain"].unique())
        complexity_levels = ["low", "medium", "high", "very_high"]

        # Create a matrix of counts
        matrix = np.zeros((len(complexity_levels), len(domains)))
        for _, row in heatmap_data.iterrows():
            domain_idx = domains.index(row["domain"])
            complexity_idx = complexity_levels.index(row["complexity_level"])
            matrix[complexity_idx, domain_idx] = row["count"]

        # Flatten for Bokeh
        x_coords = []
        y_coords = []
        colors = []
        counts = []

        max_count = matrix.max() if matrix.max() > 0 else 1

        for i, complexity in enumerate(complexity_levels):
            for j, domain in enumerate(domains):
                x_coords.append(domain)
                y_coords.append(complexity)
                count = matrix[i, j]
                counts.append(count)
                # Color based on count (normalized)
                color_intensity = count / max_count
                colors.append(color_intensity)

        source = ColumnDataSource(
            data={"x": x_coords, "y": y_coords, "count": counts, "color": colors}
        )

        # Add rectangles
        p.rect(
            "x",
            "y",
            width=0.9,
            height=0.9,
            source=source,
            fill_color=linear_cmap("color", Viridis256, 0, 1),
            line_color="white",
        )

        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [
            ("Domain", "@x"),
            ("Complexity", "@y"),
            ("File Count", "@count"),
        ]

        # Style
        p.axis.axis_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.major_label_text_font_size = "10pt"
        p.axis.major_label_standoff = 0
        p.xaxis.major_label_orientation = 45

        return pn.pane.Bokeh(p)

    def create_quality_dashboard(self) -> pn.Column:
        """Create a comprehensive quality dashboard."""
        if not self.quality_metrics:
            return pn.pane.HTML("<p>No quality metrics available</p>")

        metrics = self.quality_metrics

        # Create quality score gauge (simplified as progress bar)
        quality_score = metrics["avg_quality_score"]
        quality_color = (
            "#28a745"
            if quality_score >= 80
            else "#ffc107" if quality_score >= 60 else "#dc3545"
        )

        dashboard_html = f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
            <!-- Quality Score -->
            <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #333;">Overall Quality Score</h3>
                <div style="text-align: center;">
                    <div style="font-size: 48px; font-weight: bold; color: {quality_color}; margin: 10px 0;">
                        {quality_score:.1f}
                    </div>
                    <div style="background: #f0f0f0; height: 10px; border-radius: 5px; overflow: hidden;">
                        <div style="background: {quality_color}; height: 100%; width: {quality_score}%; transition: width 0.3s;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Complexity Metrics -->
            <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #333;">Complexity Metrics</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Average Complexity:</span>
                        <strong>{metrics['avg_complexity']:.1f}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>High Complexity Files:</span>
                        <strong style="color: #dc3545;">{metrics['high_complexity_files']}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Total Files:</span>
                        <strong>{metrics['total_files']}</strong>
                    </div>
                </div>
            </div>
            
            <!-- Maintainability -->
            <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #333;">Maintainability</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Average Index:</span>
                        <strong>{metrics['avg_maintainability']:.1f}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Low Maintainability:</span>
                        <strong style="color: #dc3545;">{metrics['low_maintainability_files']}</strong>
                    </div>
                </div>
            </div>
            
            <!-- Technical Debt -->
            <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 15px 0; color: #333;">Technical Debt</h3>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: bold; color: #ff6b6b; margin: 10px 0;">
                        {metrics['total_technical_debt']:.1f}h
                    </div>
                    <div style="font-size: 14px; color: #666;">
                        Estimated refactoring time
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Domain Quality Breakdown -->
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">Quality by Domain</h3>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Domain</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Files</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Avg Complexity</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Quality Score</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for domain in metrics["files_by_domain"]:
            file_count = metrics["files_by_domain"][domain]
            avg_complexity = metrics["complexity_by_domain"].get(domain, 0)
            quality_score = metrics["quality_by_domain"].get(domain, 0)

            # Color code quality score
            if quality_score >= 80:
                quality_color = "#28a745"
            elif quality_score >= 60:
                quality_color = "#ffc107"
            else:
                quality_color = "#dc3545"

            dashboard_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold;">{domain.title()}</td>
                            <td style="border: 1px solid #ddd; padding: 12px; text-align: center;">{file_count}</td>
                            <td style="border: 1px solid #ddd; padding: 12px; text-align: center;">{avg_complexity:.1f}</td>
                            <td style="border: 1px solid #ddd; padding: 12px; text-align: center;">
                                <span style="color: {quality_color}; font-weight: bold;">{quality_score:.1f}</span>
                            </td>
                        </tr>
            """

        dashboard_html += """
                    </tbody>
                </table>
            </div>
        </div>
        """

        return pn.pane.HTML(dashboard_html)

    def create_complexity_scatter(self) -> pn.pane.Bokeh:
        """Create scatter plot of complexity vs lines of code."""
        if not self.complexity_data:
            return pn.pane.HTML("<p>No complexity data available</p>")

        df = pd.DataFrame(self.complexity_data)

        # Create figure
        p = figure(
            width=800,
            height=600,
            title="Complexity vs Lines of Code",
            x_axis_label="Lines of Code",
            y_axis_label="Complexity Score",
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
        )

        # Color by domain
        domains = df["domain"].unique()
        # Category20 requires at least 3 colors, so use a fallback for smaller datasets
        if len(domains) <= 2:
            colors = ["#1f77b4", "#ff7f0e"][: len(domains)]
        elif len(domains) <= 20:
            colors = Category20[max(3, len(domains))]
        else:
            colors = Spectral11
        domain_colors = {
            domain: colors[i % len(colors)] for i, domain in enumerate(domains)
        }

        # Add scatter points for each domain
        for domain in domains:
            domain_data = df[df["domain"] == domain]

            source = ColumnDataSource(
                data={
                    "x": domain_data["lines_of_code"],
                    "y": domain_data["complexity"],
                    "name": domain_data["name"],
                    "path": domain_data["path"],
                    "quality_score": domain_data["quality_score"],
                    "maintainability": domain_data["maintainability_index"],
                    "technical_debt": domain_data["technical_debt_hours"],
                }
            )

            p.scatter(
                "x",
                "y",
                source=source,
                size=8,
                color=domain_colors[domain],
                alpha=0.7,
                legend_label=domain.title(),
            )

        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [
            ("File", "@name"),
            ("Path", "@path"),
            ("Lines of Code", "@x"),
            ("Complexity", "@y"),
            ("Quality Score", "@quality_score{0.0}"),
            ("Maintainability", "@maintainability{0.0}"),
            ("Technical Debt", "@technical_debt{0.0}h"),
        ]

        # Style legend
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        return pn.pane.Bokeh(p)

    def create_code_smells_detector(self) -> pn.Column:
        """Create code smells detection and reporting."""
        if not self.complexity_data:
            return pn.pane.HTML("<p>No data available for code smell detection</p>")

        df = pd.DataFrame(self.complexity_data)

        # Detect various code smells
        smells = {
            "Large Files": df[df["lines_of_code"] > 500],
            "Complex Files": df[df["complexity"] > 20],
            "God Classes": df[df["classes_count"] > 10],
            "Long Parameter Lists": df[df["functions_count"] > 20],
            "Low Maintainability": df[df["maintainability_index"] < 50],
            "High Technical Debt": df[df["technical_debt_hours"] > 10],
        }

        # Create summary
        smells_html = """
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">🔍 Code Smells Detection</h3>
        """

        for smell_name, smell_files in smells.items():
            count = len(smell_files)
            if count > 0:
                severity = "high" if count > 10 else "medium" if count > 5 else "low"
                color = (
                    "#dc3545"
                    if severity == "high"
                    else "#ffc107" if severity == "medium" else "#28a745"
                )

                smells_html += f"""
                <div style="border-left: 4px solid {color}; padding: 15px; margin: 15px 0; background: #f8f9fa;">
                    <h4 style="margin: 0 0 10px 0; color: {color};">{smell_name} ({count} files)</h4>
                    <div style="max-height: 200px; overflow-y: auto;">
                """

                for _, file in smell_files.head(10).iterrows():  # Show top 10
                    smells_html += f"""
                        <div style="padding: 5px 0; border-bottom: 1px solid #eee;">
                            <strong>{file['name']}</strong> - {file['path']}<br>
                            <small style="color: #666;">
                                Complexity: {file['complexity']}, 
                                Lines: {file['lines_of_code']}, 
                                Quality: {file['quality_score']:.1f}
                            </small>
                        </div>
                    """

                if len(smell_files) > 10:
                    smells_html += f"<div style='padding: 10px; text-align: center; color: #666;'>... and {len(smell_files) - 10} more files</div>"

                smells_html += "</div></div>"

        smells_html += "</div>"

        return pn.pane.HTML(smells_html)

    def view(self) -> pn.Tabs:
        """Return the complete complexity analysis view."""
        # Create different analysis tabs
        quality_tab = self.create_quality_dashboard()
        heatmap_tab = self.create_complexity_heatmap()
        scatter_tab = self.create_complexity_scatter()
        smells_tab = self.create_code_smells_detector()

        return pn.Tabs(
            ("📊 Quality Dashboard", quality_tab),
            ("🔥 Complexity Heatmap", heatmap_tab),
            ("📈 Complexity Analysis", scatter_tab),
            ("🔍 Code Smells", smells_tab),
            dynamic=True,
            sizing_mode="stretch_width",
        )
