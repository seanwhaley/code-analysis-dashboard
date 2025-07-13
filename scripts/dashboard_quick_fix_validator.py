#!/usr/bin/env python3
"""
Dashboard Quick Fix Validator

This script provides rapid validation of dashboard fixes and changes,
allowing developers to quickly test specific components after modifications.
"""

import json
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
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dashboard_fix_validation.log"),
    ],
)
logger = logging.getLogger(__name__)


class QuickFixValidator:
    """Rapid validation of dashboard component fixes."""

    def __init__(
        self, db_path: str = "code-intelligence-dashboard/code_intelligence.db"
    ):
        self.db_path = db_path
        self.state = None
        self.validation_results = {}

    def setup(self) -> bool:
        """Quick setup for validation testing."""
        try:
            self.state = DashboardState(self.db_path)
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    def validate_file_selection_fix(self) -> Dict[str, Any]:
        """Validate file selection functionality after fixes."""
        logger.info("Validating file selection fix...")

        try:
            # Create file explorer
            file_explorer = FileExplorer(self.state)

            # Test 1: Table creation
            files_table = file_explorer.create_files_table()
            table_ok = files_table is not None

            # Test 2: Data loading
            files_result = self.state.db_service.safe_query_files(limit=3)
            data_ok = files_result.success and len(files_result.data) > 0

            # Test 3: Selection simulation
            selection_ok = False
            if data_ok:
                try:
                    # Simulate selection event
                    class MockEvent:
                        def __init__(self, selection):
                            self.new = selection

                    original_id = self.state.selected_file_id
                    file_explorer.on_file_selected(MockEvent([0]))

                    # Check if state was updated
                    selection_ok = self.state.selected_file_id != original_id

                except Exception as e:
                    logger.warning(f"Selection test failed: {e}")

            result = {
                "component": "file_selection",
                "table_creation": table_ok,
                "data_loading": data_ok,
                "selection_handling": selection_ok,
                "overall_status": table_ok and data_ok and selection_ok,
            }

            status = "✅ PASS" if result["overall_status"] else "❌ FAIL"
            logger.info(f"File Selection Validation: {status}")

            return result

        except Exception as e:
            logger.error(f"File selection validation failed: {e}")
            return {
                "component": "file_selection",
                "error": str(e),
                "overall_status": False,
            }

    def validate_code_explorer_fix(self) -> Dict[str, Any]:
        """Validate code explorer functionality after fixes."""
        logger.info("Validating code explorer fix...")

        try:
            # Create code explorer
            code_explorer = CodeExplorerComponent(self.state)

            # Get test file
            files_result = self.state.db_service.safe_query_files(limit=1)
            if not files_result.success or not files_result.data:
                return {
                    "component": "code_explorer",
                    "error": "No test files available",
                    "overall_status": False,
                }

            test_file = files_result.data[0]

            # Test 1: File loading
            code_explorer.load_file_details(test_file.id)
            file_loaded = code_explorer.current_file is not None

            # Test 2: View creation
            views_created = {}
            try:
                overview = code_explorer.create_file_overview()
                views_created["overview"] = overview is not None
            except Exception as e:
                views_created["overview"] = False
                logger.warning(f"Overview creation failed: {e}")

            try:
                classes_panel = code_explorer.create_classes_panel()
                views_created["classes"] = classes_panel is not None
            except Exception as e:
                views_created["classes"] = False
                logger.warning(f"Classes panel creation failed: {e}")

            try:
                functions_panel = code_explorer.create_functions_panel()
                views_created["functions"] = functions_panel is not None
            except Exception as e:
                views_created["functions"] = False
                logger.warning(f"Functions panel creation failed: {e}")

            # Test 3: Main view
            main_view_ok = False
            try:
                main_view = code_explorer.view()
                main_view_ok = main_view is not None
            except Exception as e:
                logger.warning(f"Main view creation failed: {e}")

            all_views_ok = all(views_created.values()) and main_view_ok

            result = {
                "component": "code_explorer",
                "file_loading": file_loaded,
                "view_creation": views_created,
                "main_view": main_view_ok,
                "overall_status": file_loaded and all_views_ok,
            }

            status = "✅ PASS" if result["overall_status"] else "❌ FAIL"
            logger.info(f"Code Explorer Validation: {status}")

            return result

        except Exception as e:
            logger.error(f"Code explorer validation failed: {e}")
            return {
                "component": "code_explorer",
                "error": str(e),
                "overall_status": False,
            }

    def validate_network_graph_fix(self) -> Dict[str, Any]:
        """Validate network graph functionality after fixes."""
        logger.info("Validating network graph fix...")

        try:
            # Create network graph
            network_graph = NetworkGraphComponent(self.state)

            # Test 1: Graph initialization
            graph_ok = (
                network_graph.graph is not None and len(network_graph.graph.nodes) > 0
            )

            # Test 2: Layout algorithms
            layout_tests = {}
            algorithms = ["spring", "circular", "kamada_kawai"]

            for algorithm in algorithms:
                try:
                    network_graph.layout_algorithm = algorithm

                    # Test if layout can be applied
                    if hasattr(network_graph, "calculate_layout"):
                        positions = network_graph.calculate_layout()
                        layout_tests[algorithm] = (
                            positions is not None and len(positions) > 0
                        )
                    else:
                        layout_tests[algorithm] = False

                except Exception as e:
                    layout_tests[algorithm] = False
                    logger.warning(f"Layout {algorithm} failed: {e}")

            # Test 3: View creation
            view_ok = False
            try:
                view = network_graph.view()
                view_ok = view is not None
            except Exception as e:
                logger.warning(f"Network graph view creation failed: {e}")

            # Check if multiple layouts work (not just circular)
            working_layouts = [alg for alg, works in layout_tests.items() if works]
            layout_diversity = len(working_layouts) > 1

            result = {
                "component": "network_graph",
                "graph_initialization": graph_ok,
                "layout_algorithms": layout_tests,
                "layout_diversity": layout_diversity,
                "view_creation": view_ok,
                "overall_status": graph_ok and layout_diversity and view_ok,
            }

            status = "✅ PASS" if result["overall_status"] else "❌ FAIL"
            logger.info(f"Network Graph Validation: {status}")

            return result

        except Exception as e:
            logger.error(f"Network graph validation failed: {e}")
            return {
                "component": "network_graph",
                "error": str(e),
                "overall_status": False,
            }

    def validate_integration(self) -> Dict[str, Any]:
        """Validate integration between components."""
        logger.info("Validating component integration...")

        try:
            # Create all components
            file_explorer = FileExplorer(self.state)
            code_explorer = CodeExplorerComponent(self.state)

            # Test file selection -> code explorer flow
            files_result = self.state.db_service.safe_query_files(limit=1)
            if not files_result.success or not files_result.data:
                return {
                    "component": "integration",
                    "error": "No test files available",
                    "overall_status": False,
                }

            test_file = files_result.data[0]

            # Simulate file selection
            original_id = self.state.selected_file_id
            self.state.selected_file_id = test_file.id

            # Check if code explorer responds
            code_explorer.load_file_details(test_file.id)

            integration_ok = (
                self.state.selected_file_id == test_file.id
                and code_explorer.current_file is not None
                and code_explorer.current_file.id == test_file.id
            )

            # Reset state
            self.state.selected_file_id = original_id

            result = {
                "component": "integration",
                "state_update": self.state.selected_file_id == original_id,
                "cross_component_communication": integration_ok,
                "overall_status": integration_ok,
            }

            status = "✅ PASS" if result["overall_status"] else "❌ FAIL"
            logger.info(f"Integration Validation: {status}")

            return result

        except Exception as e:
            logger.error(f"Integration validation failed: {e}")
            return {
                "component": "integration",
                "error": str(e),
                "overall_status": False,
            }

    def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation of all fixes."""
        logger.info("Starting quick fix validation...")

        if not self.setup():
            return {"error": "Setup failed"}

        start_time = time.time()

        validation_results = {
            "file_selection": self.validate_file_selection_fix(),
            "code_explorer": self.validate_code_explorer_fix(),
            "network_graph": self.validate_network_graph_fix(),
            "integration": self.validate_integration(),
        }

        # Generate summary
        passed_tests = sum(
            1
            for result in validation_results.values()
            if result.get("overall_status", False)
        )
        total_tests = len(validation_results)

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (
                (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            ),
            "execution_time": round(time.time() - start_time, 2),
        }

        validation_results["summary"] = summary

        logger.info("=" * 50)
        logger.info("QUICK FIX VALIDATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Tests Run: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Execution Time: {summary['execution_time']}s")

        if summary["failed_tests"] > 0:
            logger.info("\nFAILED COMPONENTS:")
            for component, result in validation_results.items():
                if not result.get("overall_status", False):
                    logger.info(f"  ❌ {component}")
        else:
            logger.info("\n🎉 All components passed validation!")

        return validation_results


def main():
    """Main validation execution."""
    validator = QuickFixValidator()
    results = validator.run_quick_validation()

    # Save results
    with open("dashboard_fix_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Validation results saved to: dashboard_fix_validation_results.json")

    # Return exit code based on results
    if results.get("summary", {}).get("failed_tests", 1) == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
