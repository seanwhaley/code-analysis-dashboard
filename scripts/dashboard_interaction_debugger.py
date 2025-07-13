#!/usr/bin/env python3
"""
Dashboard Interaction Debugger

This script provides detailed debugging for dashboard component interactions,
focusing on file selection, state management, and cross-component communication.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the dashboard to Python path
dashboard_path = Path(__file__).parent / "code-intelligence-dashboard"
sys.path.insert(0, str(dashboard_path))

try:
    import pandas as pd
    import panel as pn
    import param
    from dashboard.components.code_explorer import CodeExplorerComponent
    from dashboard.components.network_graph import NetworkGraphComponent
    from dashboard.views import DashboardState, FileExplorer
    from db.queries import DatabaseQuerier
except ImportError as e:
    print(f"Error importing dashboard components: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dashboard_interaction_debug.log"),
    ],
)
logger = logging.getLogger(__name__)


class InteractionDebugger:
    """Debug dashboard component interactions and state management."""

    def __init__(
        self, db_path: str = "code-intelligence-dashboard/code_intelligence.db"
    ):
        self.db_path = db_path
        self.state = None
        self.file_explorer = None
        self.code_explorer = None
        self.network_graph = None
        self.debug_log = []

    def log_debug(self, message: str, component: str = "DEBUGGER"):
        """Add debug message to log."""
        timestamp = time.strftime("%H:%M:%S")
        debug_entry = f"[{timestamp}] {component}: {message}"
        self.debug_log.append(debug_entry)
        logger.debug(debug_entry)

    def setup_components(self) -> bool:
        """Initialize all dashboard components for testing."""
        try:
            self.log_debug("Initializing dashboard state...")
            self.state = DashboardState(self.db_path)

            self.log_debug("Creating FileExplorer component...")
            self.file_explorer = FileExplorer(self.state)

            self.log_debug("Creating CodeExplorer component...")
            self.code_explorer = CodeExplorerComponent(self.state)

            self.log_debug("Creating NetworkGraph component...")
            self.network_graph = NetworkGraphComponent(self.state)

            self.log_debug("All components initialized successfully")
            return True

        except Exception as e:
            self.log_debug(f"Component setup failed: {e}")
            return False

    def debug_file_selection_flow(self) -> Dict[str, Any]:
        """Debug the complete file selection workflow."""
        self.log_debug("Starting file selection flow debug...")
        results = {
            "test_name": "File Selection Flow",
            "steps": {},
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Step 1: Get available files
            self.log_debug("Step 1: Getting available files...")
            files_result = self.state.db_service.safe_query_files(limit=5)

            if not files_result.success:
                results["issues_found"].append(
                    f"Failed to load files: {files_result.error}"
                )
                return results

            files = files_result.data
            results["steps"]["file_loading"] = {
                "success": True,
                "files_count": len(files),
                "sample_file": files[0].name if files else None,
            }
            self.log_debug(f"✓ Loaded {len(files)} files")

            # Step 2: Test table creation
            self.log_debug("Step 2: Testing table creation...")
            try:
                files_table = self.file_explorer.create_files_table()

                # Check table properties
                table_info = {
                    "created": files_table is not None,
                    "type": type(files_table).__name__,
                    "has_selection_param": (
                        hasattr(files_table, "selection") if files_table else False
                    ),
                    "has_value_param": (
                        hasattr(files_table, "value") if files_table else False
                    ),
                }

                results["steps"]["table_creation"] = table_info
                self.log_debug(f"✓ Table created: {table_info}")

                if files_table is None:
                    results["issues_found"].append("Files table creation returned None")

            except Exception as e:
                results["steps"]["table_creation"] = {"success": False, "error": str(e)}
                results["issues_found"].append(f"Table creation failed: {e}")

            # Step 3: Test selection mechanism
            self.log_debug("Step 3: Testing selection mechanism...")
            try:
                # Simulate file selection
                if files:
                    test_file_id = files[0].id
                    original_selected_id = self.state.selected_file_id

                    # Test direct state update
                    self.state.selected_file_id = test_file_id

                    selection_test = {
                        "original_id": original_selected_id,
                        "test_id": test_file_id,
                        "updated_id": self.state.selected_file_id,
                        "state_updated": self.state.selected_file_id == test_file_id,
                    }

                    results["steps"]["state_update"] = selection_test
                    self.log_debug(f"✓ State update test: {selection_test}")

                    # Test selection handler
                    class MockSelectionEvent:
                        def __init__(self, new_selection):
                            self.new = new_selection

                    mock_event = MockSelectionEvent([0])  # Select first row

                    try:
                        self.file_explorer.on_file_selected(mock_event)
                        results["steps"]["selection_handler"] = {"success": True}
                        self.log_debug("✓ Selection handler executed successfully")
                    except Exception as e:
                        results["steps"]["selection_handler"] = {
                            "success": False,
                            "error": str(e),
                        }
                        results["issues_found"].append(f"Selection handler failed: {e}")

                    # Reset state
                    self.state.selected_file_id = original_selected_id

            except Exception as e:
                results["issues_found"].append(f"Selection mechanism test failed: {e}")

            # Step 4: Test cross-component communication
            self.log_debug("Step 4: Testing cross-component communication...")
            try:
                if files:
                    test_file_id = files[0].id

                    # Update state and check if code explorer responds
                    self.state.selected_file_id = test_file_id

                    # Check if code explorer loads file details
                    self.code_explorer.load_file_details(test_file_id)

                    communication_test = {
                        "state_file_id": self.state.selected_file_id,
                        "explorer_has_file": self.code_explorer.current_file
                        is not None,
                        "explorer_file_matches": (
                            self.code_explorer.current_file.id == test_file_id
                            if self.code_explorer.current_file
                            else False
                        ),
                    }

                    results["steps"]["cross_component"] = communication_test
                    self.log_debug(
                        f"✓ Cross-component communication: {communication_test}"
                    )

                    if not communication_test["explorer_file_matches"]:
                        results["issues_found"].append(
                            "Code explorer not responding to file selection"
                        )

            except Exception as e:
                results["issues_found"].append(
                    f"Cross-component communication test failed: {e}"
                )

        except Exception as e:
            results["issues_found"].append(f"File selection flow debug failed: {e}")

        # Generate recommendations
        if results["issues_found"]:
            results["recommendations"].extend(
                [
                    "Check Tabulator table configuration for proper selection events",
                    "Verify parameter watching setup between components",
                    "Ensure database queries are returning expected data structures",
                    "Test event propagation in browser developer tools",
                ]
            )

        return results

    def debug_code_explorer_rendering(self) -> Dict[str, Any]:
        """Debug code explorer component rendering issues."""
        self.log_debug("Starting code explorer rendering debug...")
        results = {
            "test_name": "Code Explorer Rendering",
            "steps": {},
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Get test file
            files_result = self.state.db_service.safe_query_files(limit=1)
            if not files_result.success or not files_result.data:
                results["issues_found"].append("No files available for testing")
                return results

            test_file = files_result.data[0]

            # Test file details loading
            self.log_debug(f"Testing file details loading for: {test_file.name}")
            self.code_explorer.load_file_details(test_file.id)

            loading_results = {
                "file_loaded": self.code_explorer.current_file is not None,
                "classes_count": len(self.code_explorer.current_classes),
                "functions_count": len(self.code_explorer.current_functions),
                "relationships_count": len(self.code_explorer.current_relationships),
            }

            results["steps"]["data_loading"] = loading_results
            self.log_debug(f"✓ Data loading results: {loading_results}")

            # Test view creation methods
            view_tests = {}

            # Test file overview
            try:
                overview = self.code_explorer.create_file_overview()
                view_tests["file_overview"] = {
                    "created": overview is not None,
                    "type": type(overview).__name__ if overview else None,
                }
                self.log_debug(f"✓ File overview: {view_tests['file_overview']}")
            except Exception as e:
                view_tests["file_overview"] = {"created": False, "error": str(e)}
                results["issues_found"].append(f"File overview creation failed: {e}")

            # Test classes panel
            try:
                classes_panel = self.code_explorer.create_classes_panel()
                view_tests["classes_panel"] = {
                    "created": classes_panel is not None,
                    "type": type(classes_panel).__name__ if classes_panel else None,
                }
                self.log_debug(f"✓ Classes panel: {view_tests['classes_panel']}")
            except Exception as e:
                view_tests["classes_panel"] = {"created": False, "error": str(e)}
                results["issues_found"].append(f"Classes panel creation failed: {e}")

            # Test functions panel
            try:
                functions_panel = self.code_explorer.create_functions_panel()
                view_tests["functions_panel"] = {
                    "created": functions_panel is not None,
                    "type": type(functions_panel).__name__ if functions_panel else None,
                }
                self.log_debug(f"✓ Functions panel: {view_tests['functions_panel']}")
            except Exception as e:
                view_tests["functions_panel"] = {"created": False, "error": str(e)}
                results["issues_found"].append(f"Functions panel creation failed: {e}")

            results["steps"]["view_creation"] = view_tests

            # Test main view method
            try:
                main_view = self.code_explorer.view()
                results["steps"]["main_view"] = {
                    "created": main_view is not None,
                    "type": type(main_view).__name__ if main_view else None,
                }
                self.log_debug(f"✓ Main view: {results['steps']['main_view']}")
            except Exception as e:
                results["steps"]["main_view"] = {"created": False, "error": str(e)}
                results["issues_found"].append(f"Main view creation failed: {e}")

        except Exception as e:
            results["issues_found"].append(f"Code explorer rendering debug failed: {e}")

        # Generate recommendations
        if results["issues_found"]:
            results["recommendations"].extend(
                [
                    "Check database schema for missing class/function data",
                    "Verify HTML template rendering in create_*_panel methods",
                    "Test Panel component creation and layout",
                    "Check for missing attributes in database models",
                ]
            )

        return results

    def debug_network_graph_layout(self) -> Dict[str, Any]:
        """Debug network graph layout and rendering issues."""
        self.log_debug("Starting network graph layout debug...")
        results = {
            "test_name": "Network Graph Layout",
            "steps": {},
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Test graph initialization
            graph_info = {
                "graph_exists": self.network_graph.graph is not None,
                "nodes_count": (
                    len(self.network_graph.graph.nodes)
                    if self.network_graph.graph
                    else 0
                ),
                "edges_count": (
                    len(self.network_graph.graph.edges)
                    if self.network_graph.graph
                    else 0
                ),
            }

            results["steps"]["graph_initialization"] = graph_info
            self.log_debug(f"✓ Graph initialization: {graph_info}")

            if graph_info["nodes_count"] == 0:
                results["issues_found"].append("Network graph has no nodes")

            # Test layout algorithms
            layout_algorithms = [
                "spring",
                "circular",
                "kamada_kawai",
                "shell",
                "random",
            ]
            layout_results = {}

            for algorithm in layout_algorithms:
                try:
                    self.log_debug(f"Testing layout algorithm: {algorithm}")

                    # Set layout algorithm
                    self.network_graph.layout_algorithm = algorithm

                    # Test if layout method exists and works
                    if hasattr(self.network_graph, "calculate_layout"):
                        positions = self.network_graph.calculate_layout()
                        layout_results[algorithm] = {
                            "success": True,
                            "positions_count": len(positions) if positions else 0,
                        }
                    else:
                        layout_results[algorithm] = {
                            "success": False,
                            "error": "calculate_layout method not found",
                        }

                except Exception as e:
                    layout_results[algorithm] = {"success": False, "error": str(e)}

            results["steps"]["layout_algorithms"] = layout_results
            self.log_debug(f"✓ Layout algorithms tested: {layout_results}")

            # Count successful layouts
            successful_layouts = [
                alg for alg, result in layout_results.items() if result.get("success")
            ]
            if not successful_layouts:
                results["issues_found"].append("No layout algorithms working")
            elif len(successful_layouts) == 1 and "circular" in successful_layouts:
                results["issues_found"].append(
                    "Only circular layout working - other algorithms failing"
                )

            # Test view creation
            try:
                view = self.network_graph.view()
                results["steps"]["view_creation"] = {
                    "created": view is not None,
                    "type": type(view).__name__ if view else None,
                }
                self.log_debug(f"✓ View creation: {results['steps']['view_creation']}")
            except Exception as e:
                results["steps"]["view_creation"] = {"created": False, "error": str(e)}
                results["issues_found"].append(
                    f"Network graph view creation failed: {e}"
                )

        except Exception as e:
            results["issues_found"].append(f"Network graph layout debug failed: {e}")

        # Generate recommendations
        if results["issues_found"]:
            results["recommendations"].extend(
                [
                    "Check NetworkX installation and version compatibility",
                    "Verify graph data structure and node/edge attributes",
                    "Test layout algorithms individually with sample data",
                    "Check Bokeh figure configuration and rendering pipeline",
                ]
            )

        return results

    def run_comprehensive_debug(self) -> Dict[str, Any]:
        """Run comprehensive debugging of all dashboard interactions."""
        self.log_debug("Starting comprehensive dashboard interaction debug...")

        if not self.setup_components():
            return {"error": "Failed to setup components for debugging"}

        debug_results = {
            "file_selection_flow": self.debug_file_selection_flow(),
            "code_explorer_rendering": self.debug_code_explorer_rendering(),
            "network_graph_layout": self.debug_network_graph_layout(),
            "debug_log": self.debug_log,
        }

        # Generate overall summary
        total_issues = sum(
            len(result.get("issues_found", []))
            for result in debug_results.values()
            if isinstance(result, dict)
        )

        summary = {"total_tests": 3, "total_issues": total_issues, "critical_areas": []}

        for test_name, result in debug_results.items():
            if isinstance(result, dict) and result.get("issues_found"):
                summary["critical_areas"].append(
                    {
                        "test": test_name,
                        "issues_count": len(result["issues_found"]),
                        "issues": result["issues_found"],
                    }
                )

        debug_results["summary"] = summary

        self.log_debug("=" * 60)
        self.log_debug("DASHBOARD INTERACTION DEBUG SUMMARY")
        self.log_debug("=" * 60)
        self.log_debug(f"Total Tests Run: {summary['total_tests']}")
        self.log_debug(f"Total Issues Found: {summary['total_issues']}")

        if summary["critical_areas"]:
            self.log_debug("\nCRITICAL AREAS REQUIRING ATTENTION:")
            for area in summary["critical_areas"]:
                self.log_debug(f"  {area['test']}: {area['issues_count']} issues")
                for issue in area["issues"]:
                    self.log_debug(f"    - {issue}")
        else:
            self.log_debug("\n✓ No critical issues found in interaction debugging!")

        return debug_results


def main():
    """Main debug execution."""
    debugger = InteractionDebugger()
    results = debugger.run_comprehensive_debug()

    # Save results to file
    import json

    with open("dashboard_interaction_debug_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Debug results saved to: dashboard_interaction_debug_results.json")

    return results


if __name__ == "__main__":
    main()
