#!/usr/bin/env python3
"""
Architecture Analysis Component

This module provides comprehensive architectural analysis including layered architecture
validation, design pattern detection, and architectural quality metrics.
"""

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import pandas as pd
import panel as pn
import param
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20, RdYlBu11
from bokeh.plotting import figure

logger = logging.getLogger(__name__)


class ArchitectureAnalysisComponent(param.Parameterized):
    """Component for analyzing software architecture and design patterns."""

    analysis_scope = param.String(default="full")  # full, domain, layer
    show_violations = param.Boolean(default=True)

    def __init__(self, state: Any, **params: Any) -> None:
        super().__init__(**params)
        self.state = state
        self.architecture_graph: Optional[nx.DiGraph] = None
        self.layer_violations: List[Any] = []
        self.design_patterns: Dict[str, Any] = {}
        self.architectural_metrics: Dict[str, Any] = {}
        self.load_architecture_data()

    def load_architecture_data(self):
        """Load and analyze architectural data."""
        try:
            # Get all files and relationships
            files_result = self.state.db_querier.get_all_files(limit=1000)
            logger.debug(
                f"files_result type: {type(files_result)}; value: {repr(files_result)[:500]}"
            )
            # get_all_files returns (files, total_count) tuple
            files, total_count = files_result
            logger.debug(
                f"files unpacked type: {type(files)}; count: {len(files)}; total: {total_count}"
            )

            relationships = self.state.db_querier.get_all_relationships()

            classes_result = self.state.db_querier.get_all_classes()
            # get_all_classes returns (classes, total_count) tuple
            classes, _ = classes_result

            functions_result = self.state.db_querier.get_all_functions()
            # get_all_functions returns (functions, total_count) tuple
            functions, _ = functions_result

            # Build architecture graph
            self.build_architecture_graph(files, relationships, classes, functions)

            # Analyze layered architecture
            self.analyze_layered_architecture(files, relationships)

            # Detect design patterns
            self.detect_design_patterns(classes, functions)

            # Calculate architectural metrics
            self.calculate_architectural_metrics(files, relationships)

            logger.info("Loaded architecture analysis data")

        except Exception as e:
            logger.error(f"Error loading architecture data: {e}")

    def build_architecture_graph(self, files, relationships, classes, functions):
        """Build a graph representing the software architecture."""
        self.architecture_graph = nx.DiGraph()

        # Add nodes (files) with domain information
        for file in files:
            self.architecture_graph.add_node(
                file.id,
                name=file.name,
                path=file.path,
                domain=file.domain.value,
                layer=self.determine_layer(file),
                complexity=file.complexity,
                lines_of_code=file.lines_of_code,
            )

        # Create mappings from class/function IDs to file IDs
        class_to_file = {cls.id: cls.file_id for cls in classes}
        function_to_file = {func.id: func.file_id for func in functions}

        # Track file-to-file relationships to avoid duplicates
        file_relationships = set()

        # Add edges (derive file relationships from class/function relationships)
        for rel in relationships:
            source_file_id = None
            target_file_id = None

            # Determine source file
            if rel.source_type == "class":
                source_file_id = class_to_file.get(rel.source_id)
            elif rel.source_type == "function":
                source_file_id = function_to_file.get(rel.source_id)

            # Determine target file
            if rel.target_type == "class":
                target_file_id = class_to_file.get(rel.target_id)
            elif rel.target_type == "function":
                target_file_id = function_to_file.get(rel.target_id)

            # Add file-to-file edge if both files exist and are different
            if (
                source_file_id
                and target_file_id
                and source_file_id != target_file_id
                and (source_file_id, target_file_id) not in file_relationships
            ):

                self.architecture_graph.add_edge(
                    source_file_id,
                    target_file_id,
                    relationship_type=rel.relationship_type.value,
                    weight=1,
                )
                file_relationships.add((source_file_id, target_file_id))

    def determine_layer(self, file) -> str:
        """Determine the architectural layer of a file based on its domain and path."""
        domain = file.domain.value.lower()
        path = file.path.lower()

        # Define layer mapping based on common architectural patterns
        if domain in ["presentation", "api", "web"] or "api" in path or "web" in path:
            return "presentation"
        elif domain in ["application", "services"] or "service" in path:
            return "application"
        elif domain in ["domain", "business"] or "domain" in path:
            return "domain"
        elif domain in ["infrastructure", "data", "persistence"] or any(
            x in path for x in ["db", "database", "repository"]
        ):
            return "infrastructure"
        elif domain in ["models", "entities"] or "model" in path:
            return "domain"  # Models are typically part of domain layer
        elif domain in ["utils", "common", "shared"]:
            return "shared"
        else:
            return "unknown"

    def analyze_layered_architecture(self, files, relationships):
        """Analyze adherence to layered architecture principles."""
        # Define allowed dependencies between layers
        allowed_dependencies = {
            "presentation": ["application", "shared"],
            "application": ["domain", "infrastructure", "shared"],
            "domain": ["shared"],
            "infrastructure": ["domain", "shared"],
            "shared": [],
        }

        self.layer_violations = []

        # Check each relationship for layer violations
        file_lookup = {f.id: f for f in files}

        # Create file lookup for classes and functions
        classes, _ = self.state.db_querier.get_all_classes()
        functions, _ = self.state.db_querier.get_all_functions()

        # Create mappings from class/function IDs to file IDs
        class_to_file = {cls.id: cls.file_id for cls in classes}
        function_to_file = {func.id: func.file_id for func in functions}

        for rel in relationships:
            source_file_id = None
            target_file_id = None

            # Determine source file
            if rel.source_type == "class":
                source_file_id = class_to_file.get(rel.source_id)
            elif rel.source_type == "function":
                source_file_id = function_to_file.get(rel.source_id)

            # Determine target file
            if rel.target_type == "class":
                target_file_id = class_to_file.get(rel.target_id)
            elif rel.target_type == "function":
                target_file_id = function_to_file.get(rel.target_id)

            if source_file_id and target_file_id and source_file_id != target_file_id:
                source_file = file_lookup.get(source_file_id)
                target_file = file_lookup.get(target_file_id)

                if source_file and target_file:
                    source_layer = self.determine_layer(source_file)
                    target_layer = self.determine_layer(target_file)

                    # Check if this dependency is allowed
                    if (
                        source_layer in allowed_dependencies
                        and target_layer not in allowed_dependencies[source_layer]
                        and source_layer != target_layer
                    ):

                        violation = {
                            "source_file": source_file.name,
                            "source_path": source_file.path,
                            "source_layer": source_layer,
                            "target_file": target_file.name,
                            "target_path": target_file.path,
                            "target_layer": target_layer,
                            "relationship_type": rel.relationship_type.value,
                            "severity": self.calculate_violation_severity(
                                source_layer, target_layer
                            ),
                        }
                        self.layer_violations.append(violation)

    def calculate_violation_severity(self, source_layer: str, target_layer: str) -> str:
        """Calculate the severity of a layer violation."""
        # High severity violations
        if (
            source_layer == "domain"
            and target_layer in ["presentation", "infrastructure"]
        ) or (source_layer == "infrastructure" and target_layer == "presentation"):
            return "high"
        # Medium severity violations
        elif source_layer == "application" and target_layer == "presentation":
            return "medium"
        # Low severity violations
        else:
            return "low"

    def detect_design_patterns(self, classes, functions):
        """Detect common design patterns in the codebase."""
        self.design_patterns = {
            "singleton": [],
            "factory": [],
            "observer": [],
            "strategy": [],
            "decorator": [],
            "adapter": [],
            "repository": [],
            "service": [],
            "builder": [],
        }

        # Analyze classes for patterns
        for cls in classes:
            class_name = cls.name.lower()
            base_classes = [base.lower() for base in (cls.base_classes or [])]

            # Singleton pattern detection
            if "singleton" in class_name or any(
                "singleton" in base for base in base_classes
            ):
                self.design_patterns["singleton"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "high"}
                )

            # Factory pattern detection
            if "factory" in class_name or class_name.endswith("factory"):
                self.design_patterns["factory"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "high"}
                )

            # Repository pattern detection
            if "repository" in class_name or class_name.endswith("repo"):
                self.design_patterns["repository"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "high"}
                )

            # Service pattern detection
            if "service" in class_name or class_name.endswith("service"):
                self.design_patterns["service"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "high"}
                )

            # Builder pattern detection
            if "builder" in class_name or class_name.endswith("builder"):
                self.design_patterns["builder"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "high"}
                )

            # Observer pattern detection (simplified)
            if (
                any("observer" in base for base in base_classes)
                or "observer" in class_name
            ):
                self.design_patterns["observer"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "medium"}
                )

            # Strategy pattern detection (simplified)
            if (
                any("strategy" in base for base in base_classes)
                or "strategy" in class_name
            ):
                self.design_patterns["strategy"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "medium"}
                )

            # Decorator pattern detection
            if "decorator" in class_name or any(
                "decorator" in base for base in base_classes
            ):
                self.design_patterns["decorator"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "medium"}
                )

            # Adapter pattern detection
            if "adapter" in class_name or class_name.endswith("adapter"):
                self.design_patterns["adapter"].append(
                    {"class": cls.name, "file": cls.file_path, "confidence": "medium"}
                )

    def calculate_architectural_metrics(self, files, relationships):
        """Calculate various architectural quality metrics."""
        if not self.architecture_graph:
            self.architectural_metrics = {}
            return

        # Layer distribution
        layer_counts = Counter()
        for node in self.architecture_graph.nodes():
            layer = self.architecture_graph.nodes[node]["layer"]
            layer_counts[layer] += 1

        # Coupling metrics by layer
        layer_coupling = defaultdict(lambda: {"in": 0, "out": 0})
        for source, target in self.architecture_graph.edges():
            source_layer = self.architecture_graph.nodes[source]["layer"]
            target_layer = self.architecture_graph.nodes[target]["layer"]

            if source_layer != target_layer:
                layer_coupling[source_layer]["out"] += 1
                layer_coupling[target_layer]["in"] += 1

        # Calculate architectural debt
        architectural_debt = len(self.layer_violations) * 2  # 2 hours per violation

        # Calculate modularity using NetworkX
        try:
            # Create undirected graph for modularity calculation
            undirected_graph = self.architecture_graph.to_undirected()
            communities = nx.community.greedy_modularity_communities(undirected_graph)
            modularity = nx.community.modularity(undirected_graph, communities)
        except:
            modularity = 0.0

        self.architectural_metrics = {
            "total_files": len(files),
            "total_relationships": len(relationships),
            "layer_distribution": dict(layer_counts),
            "layer_coupling": dict(layer_coupling),
            "layer_violations": len(self.layer_violations),
            "architectural_debt_hours": architectural_debt,
            "modularity": modularity,
            "design_patterns_count": sum(
                len(patterns) for patterns in self.design_patterns.values()
            ),
            "average_coupling": (
                sum(dict(self.architecture_graph.degree()).values())
                / len(self.architecture_graph.nodes())
                if self.architecture_graph.nodes()
                else 0
            ),
        }

    def create_layer_architecture_view(self) -> pn.Column:
        """Create layered architecture analysis view."""
        if not self.architectural_metrics:
            return pn.pane.HTML("<p>No architectural data available</p>")

        metrics = self.architectural_metrics
        layer_dist = metrics["layer_distribution"]

        # Create layer distribution chart
        p = figure(
            width=600,
            height=400,
            title="Layer Distribution",
            x_range=list(layer_dist.keys()),
            tools="hover,save",
            toolbar_location="above",
        )

        source = ColumnDataSource(
            data={
                "layers": list(layer_dist.keys()),
                "counts": list(layer_dist.values()),
            }
        )

        p.vbar(
            x="layers", top="counts", source=source, width=0.8, color="blue", alpha=0.7
        )

        hover = p.select_one(HoverTool)
        hover.tooltips = [("Layer", "@layers"), ("Files", "@counts")]

        p.xaxis.major_label_orientation = 45

        # Create violations summary
        violations_by_severity = Counter(v["severity"] for v in self.layer_violations)

        architecture_html = f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">🏛️ Layered Architecture Analysis</h3>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #007bff;">Total Layers</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{len(layer_dist)}</p>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: {'#dc3545' if metrics['layer_violations'] > 0 else '#28a745'};">Layer Violations</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{metrics['layer_violations']}</p>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #ffc107;">Architectural Debt</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{metrics['architectural_debt_hours']}h</p>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #17a2b8;">Modularity</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{metrics['modularity']:.3f}</p>
                </div>
            </div>
        """

        if self.layer_violations:
            architecture_html += f"""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h4 style="color: #721c24; margin: 0 0 15px 0;">⚠️ Layer Violations Detected</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 15px;">
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                        <strong style="color: #dc3545;">{violations_by_severity.get('high', 0)}</strong><br>
                        <small>High Severity</small>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                        <strong style="color: #ffc107;">{violations_by_severity.get('medium', 0)}</strong><br>
                        <small>Medium Severity</small>
                    </div>
                    <div style="text-align: center; padding: 10px; background: white; border-radius: 4px;">
                        <strong style="color: #28a745;">{violations_by_severity.get('low', 0)}</strong><br>
                        <small>Low Severity</small>
                    </div>
                </div>
                
                <h5>Top Violations:</h5>
                <div style="max-height: 300px; overflow-y: auto;">
            """

            # Show top 10 violations
            sorted_violations = sorted(
                self.layer_violations,
                key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["severity"]],
                reverse=True,
            )

            for violation in sorted_violations[:10]:
                severity_color = {
                    "high": "#dc3545",
                    "medium": "#ffc107",
                    "low": "#28a745",
                }[violation["severity"]]
                architecture_html += f"""
                    <div style="border-left: 4px solid {severity_color}; padding: 10px; margin: 10px 0; background: white; border-radius: 4px;">
                        <strong>{violation['source_file']}</strong> ({violation['source_layer']}) 
                        → <strong>{violation['target_file']}</strong> ({violation['target_layer']})
                        <br><small style="color: #666;">
                            Relationship: {violation['relationship_type']} | 
                            Severity: {violation['severity'].title()}
                        </small>
                    </div>
                """

            architecture_html += "</div></div>"
        else:
            architecture_html += """
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h4 style="color: #155724; margin: 0;">✅ No Layer Violations Found</h4>
                <p style="color: #155724; margin: 5px 0 0 0;">Your architecture follows good layering principles!</p>
            </div>
            """

        architecture_html += "</div>"

        return pn.Column(
            pn.pane.Bokeh(p),
            pn.pane.HTML(architecture_html),
            sizing_mode="stretch_width",
        )

    def create_design_patterns_view(self) -> pn.Column:
        """Create design patterns analysis view."""
        if not self.design_patterns:
            return pn.pane.HTML("<p>No design pattern data available</p>")

        # Count patterns
        pattern_counts = {
            pattern: len(instances)
            for pattern, instances in self.design_patterns.items()
            if instances
        }

        if not pattern_counts:
            return pn.pane.HTML(
                """
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #856404; margin: 0 0 10px 0;">🔍 No Design Patterns Detected</h3>
                    <p style="color: #856404; margin: 0;">Consider implementing common design patterns to improve code organization.</p>
                </div>
            """
            )

        patterns_html = f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 20px 0; color: #333;">🎨 Design Patterns Analysis</h3>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #007bff;">Patterns Found</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{len(pattern_counts)}</p>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #28a745;">Total Instances</h4>
                    <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{sum(pattern_counts.values())}</p>
                </div>
                <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0; color: #ffc107;">Most Common</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0 0 0;">{max(pattern_counts, key=pattern_counts.get).title()}</p>
                </div>
            </div>
            
            <h4>Pattern Details:</h4>
        """

        # Pattern descriptions
        pattern_descriptions = {
            "singleton": "Ensures a class has only one instance",
            "factory": "Creates objects without specifying exact classes",
            "observer": "Defines one-to-many dependency between objects",
            "strategy": "Defines family of algorithms and makes them interchangeable",
            "decorator": "Adds behavior to objects dynamically",
            "adapter": "Allows incompatible interfaces to work together",
            "repository": "Encapsulates data access logic",
            "service": "Encapsulates business logic",
            "builder": "Constructs complex objects step by step",
        }

        for pattern_name, instances in self.design_patterns.items():
            if instances:
                patterns_html += f"""
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h5 style="margin: 0; color: #333;">{pattern_name.title()} Pattern</h5>
                        <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                            {len(instances)} instances
                        </span>
                    </div>
                    <p style="color: #666; margin: 5px 0 15px 0; font-style: italic;">
                        {pattern_descriptions.get(pattern_name, 'Design pattern detected')}
                    </p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">
                """

                for instance in instances[:5]:  # Show top 5 instances
                    confidence_color = {
                        "high": "#28a745",
                        "medium": "#ffc107",
                        "low": "#dc3545",
                    }[instance["confidence"]]
                    patterns_html += f"""
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 3px solid {confidence_color};">
                            <strong>{instance['class']}</strong><br>
                            <small style="color: #666;">{instance['file']}</small><br>
                            <small style="color: {confidence_color};">Confidence: {instance['confidence'].title()}</small>
                        </div>
                    """

                if len(instances) > 5:
                    patterns_html += f"<div style='padding: 10px; text-align: center; color: #666;'>... and {len(instances) - 5} more</div>"

                patterns_html += "</div></div>"

        patterns_html += "</div>"

        return pn.pane.HTML(patterns_html)

    def view(self) -> pn.Tabs:
        """Return the complete architecture analysis view."""
        layer_tab = self.create_layer_architecture_view()
        patterns_tab = self.create_design_patterns_view()

        return pn.Tabs(
            ("🏛️ Layer Architecture", layer_tab),
            ("🎨 Design Patterns", patterns_tab),
            dynamic=True,
            sizing_mode="stretch_width",
        )
