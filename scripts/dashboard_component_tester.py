#!/usr/bin/env python3
"""
Dashboard Component Testing Framework

This script provides comprehensive testing for dashboard components to identify
and diagnose issues with file selection, code explorer, and network graph.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the dashboard to Python path
dashboard_path = Path(__file__).parent / "code-intelligence-dashboard"
sys.path.insert(0, str(dashboard_path))

try:
    import pandas as pd
    import panel as pn
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
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dashboard_component_test.log"),
    ],
)
logger = logging.getLogger(__name__)


class DashboardComponentTester:
    """Comprehensive testing framework for dashboard components."""

    def __init__(
        self, db_path: str = "code-intelligence-dashboard/code_intelligence.db"
    ):
        self.db_path = db_path
        self.state = None
        self.test_results = {}

    def setup_test_environment(self) -> bool:
        """Initialize test environment and verify database connectivity."""
        try:
            logger.info("Setting up test environment...")

            # Initialize dashboard state
            self.state = DashboardState(self.db_path)

            # Test database connectivity
            files_result = self.state.db_service.safe_query_files(limit=5)
            if not files_result.success:
                logger.error(f"Database connectivity failed: {files_result.error}")
                return False

            logger.info(
                f"Database connected successfully, found {len(files_result.data)} files"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False

    def test_file_explorer_component(self) -> Dict[str, Any]:
        """Test FileExplorer component functionality."""
        logger.info("Testing FileExplorer component...")
        results = {
            "component_name": "FileExplorer",
            "initialization": False,
            "data_loading": False,
            "table_creation": False,
            "selection_handler": False,
            "errors": [],
        }

        try:
            # Test component initialization
            file_explorer = FileExplorer(self.state)
            results["initialization"] = True
            logger.info("✓ FileExplorer initialization successful")

            # Test data loading
            files_result = self.state.db_service.safe_query_files(limit=10)
            if files_result.success and files_result.data:
                results["data_loading"] = True
                logger.info(
                    f"✓ Data loading successful: {len(files_result.data)} files"
                )
            else:
                results["errors"].append(f"Data loading failed: {files_result.error}")

            # Test table creation
            try:
                files_table = file_explorer.create_files_table()
                if files_table is not None:
                    results["table_creation"] = True
                    logger.info("✓ Files table creation successful")
                else:
                    results["errors"].append("Files table creation returned None")
            except Exception as e:
                results["errors"].append(f"Files table creation failed: {e}")

            # Test selection handler
            try:
                # Simulate selection event
                class MockEvent:
                    def __init__(self, new_selection):
                        self.new = new_selection

                mock_event = MockEvent([0])  # Select first row
                file_explorer.on_file_selected(mock_event)
                results["selection_handler"] = True
                logger.info("✓ Selection handler executed without errors")
            except Exception as e:
                results["errors"].append(f"Selection handler failed: {e}")

        except Exception as e:
            results["errors"].append(f"FileExplorer component test failed: {e}")
            logger.error(f"✗ FileExplorer component test failed: {e}")

        return results

    def test_code_explorer_component(self) -> Dict[str, Any]:
        """Test CodeExplorer component functionality."""
        logger.info("Testing CodeExplorer component...")
        results = {
            "component_name": "CodeExplorer",
            "initialization": False,
            "file_loading": False,
            "view_creation": False,
            "data_queries": False,
            "errors": [],
        }

        try:
            # Test component initialization
            code_explorer = CodeExplorerComponent(self.state)
            results["initialization"] = True
            logger.info("✓ CodeExplorer initialization successful")

            # Test file loading with actual file ID
            files_result = self.state.db_service.safe_query_files(limit=1)
            if files_result.success and files_result.data:
                test_file = files_result.data[0]
                file_id = test_file.id

                try:
                    code_explorer.load_file_details(file_id)
                    results["file_loading"] = True
                    logger.info(f"✓ File loading successful for file ID: {file_id}")
                except Exception as e:
                    results["errors"].append(f"File loading failed: {e}")

                # Test data queries
                try:
                    if code_explorer.current_file is not None:
                        results["data_queries"] = True
                        logger.info("✓ Data queries successful")
                        logger.info(
                            f"  - Current file: {code_explorer.current_file.name}"
                        )
                        logger.info(
                            f"  - Classes found: {len(code_explorer.current_classes)}"
                        )
                        logger.info(
                            f"  - Functions found: {len(code_explorer.current_functions)}"
                        )
                    else:
                        results["errors"].append("Data queries returned no file data")
                except Exception as e:
                    results["errors"].append(f"Data queries failed: {e}")

                # Test view creation
                try:
                    overview = code_explorer.create_file_overview()
                    if overview is not None:
                        results["view_creation"] = True
                        logger.info("✓ View creation successful")
                    else:
                        results["errors"].append("View creation returned None")
                except Exception as e:
                    results["errors"].append(f"View creation failed: {e}")
            else:
                results["errors"].append("No files available for testing")

        except Exception as e:
            results["errors"].append(f"CodeExplorer component test failed: {e}")
            logger.error(f"✗ CodeExplorer component test failed: {e}")

        return results

    def test_network_graph_component(self) -> Dict[str, Any]:
        """Test NetworkGraph component functionality."""
        logger.info("Testing NetworkGraph component...")
        results = {
            "component_name": "NetworkGraph",
            "initialization": False,
            "graph_setup": False,
            "layout_algorithms": False,
            "view_creation": False,
            "errors": [],
        }

        try:
            # Test component initialization
            network_graph = NetworkGraphComponent(self.state)
            results["initialization"] = True
            logger.info("✓ NetworkGraph initialization successful")

            # Test graph setup
            try:
                if (
                    network_graph.graph is not None
                    and len(network_graph.graph.nodes) > 0
                ):
                    results["graph_setup"] = True
                    logger.info(
                        f"✓ Graph setup successful: {len(network_graph.graph.nodes)} nodes"
                    )
                else:
                    results["errors"].append("Graph setup failed: no nodes found")
            except Exception as e:
                results["errors"].append(f"Graph setup failed: {e}")

            # Test layout algorithms
            layout_algorithms = ["spring", "circular", "kamada_kawai", "shell"]
            working_layouts = []

            for layout in layout_algorithms:
                try:
                    network_graph.layout_algorithm = layout
                    # Test if layout can be applied
                    if hasattr(network_graph, "calculate_layout"):
                        network_graph.calculate_layout()
                        working_layouts.append(layout)
                except Exception as e:
                    results["errors"].append(f"Layout '{layout}' failed: {e}")

            if working_layouts:
                results["layout_algorithms"] = True
                logger.info(f"✓ Layout algorithms working: {working_layouts}")
            else:
                results["errors"].append("No layout algorithms working")

            # Test view creation
            try:
                view = network_graph.view()
                if view is not None:
                    results["view_creation"] = True
                    logger.info("✓ Network graph view creation successful")
                else:
                    results["errors"].append(
                        "Network graph view creation returned None"
                    )
            except Exception as e:
                results["errors"].append(f"Network graph view creation failed: {e}")

        except Exception as e:
            results["errors"].append(f"NetworkGraph component test failed: {e}")
            logger.error(f"✗ NetworkGraph component test failed: {e}")

        return results

    def test_state_management(self) -> Dict[str, Any]:
        """Test dashboard state management and parameter watching."""
        logger.info("Testing state management...")
        results = {
            "component_name": "StateManagement",
            "parameter_updates": False,
            "cross_component_communication": False,
            "data_synchronization": False,
            "errors": [],
        }

        try:
            # Test parameter updates
            original_file_id = self.state.selected_file_id
            self.state.selected_file_id = 1

            if self.state.selected_file_id == 1:
                results["parameter_updates"] = True
                logger.info("✓ Parameter updates working")
            else:
                results["errors"].append("Parameter updates failed")

            # Reset parameter
            self.state.selected_file_id = original_file_id

            # Test data synchronization
            try:
                self.state.refresh_system_stats()
                if self.state.system_stats is not None:
                    results["data_synchronization"] = True
                    logger.info("✓ Data synchronization working")
                else:
                    results["errors"].append("Data synchronization failed: no stats")
            except Exception as e:
                results["errors"].append(f"Data synchronization failed: {e}")

        except Exception as e:
            results["errors"].append(f"State management test failed: {e}")
            logger.error(f"✗ State management test failed: {e}")

        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        logger.info("Starting comprehensive dashboard component tests...")

        if not self.setup_test_environment():
            return {"error": "Failed to setup test environment"}

        # Run all component tests
        test_results = {
            "file_explorer": self.test_file_explorer_component(),
            "code_explorer": self.test_code_explorer_component(),
            "network_graph": self.test_network_graph_component(),
            "state_management": self.test_state_management(),
        }

        # Generate summary
        summary = {
            "total_components": len(test_results),
            "passing_components": 0,
            "failing_components": 0,
            "critical_issues": [],
        }

        for component_name, results in test_results.items():
            if isinstance(results, dict) and "errors" in results:
                if not results["errors"]:
                    summary["passing_components"] += 1
                else:
                    summary["failing_components"] += 1
                    summary["critical_issues"].extend(results["errors"])

        test_results["summary"] = summary

        logger.info("=" * 60)
        logger.info("DASHBOARD COMPONENT TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Components Tested: {summary['total_components']}")
        logger.info(f"Passing Components: {summary['passing_components']}")
        logger.info(f"Failing Components: {summary['failing_components']}")

        if summary["critical_issues"]:
            logger.info("\nCRITICAL ISSUES FOUND:")
            for issue in summary["critical_issues"]:
                logger.info(f"  - {issue}")
        else:
            logger.info("\n✓ All components passed basic functionality tests!")

        return test_results


def main():
    """Main test execution."""
    tester = DashboardComponentTester()
    results = tester.run_all_tests()

    # Save results to file
    import json

    with open("dashboard_component_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Test results saved to: dashboard_component_test_results.json")

    return results


if __name__ == "__main__":
    main()
