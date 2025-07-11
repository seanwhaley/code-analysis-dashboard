#!/usr/bin/env python3
"""
Migration Validation and Testing Script

This script validates the complete migration from FastAPI/JavaScript to Panel
and runs a comprehensive test of the new system.

Usage:
    python migrate_and_test.py [project_path]
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migration_test.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check that all required dependencies are installed."""
    logger.info("🔍 Checking dependencies...")

    required_packages = ["panel", "pydantic", "pandas", "bokeh", "param"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"  ❌ {package}")

    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        logger.error("Please install with: pip install -r requirements.txt")
        return False

    logger.info("✅ All dependencies are installed")
    return True


def validate_file_structure():
    """Validate the new file structure."""
    logger.info("🏗️ Validating file structure...")

    required_files = [
        "requirements.txt",
        "models/__init__.py",
        "models/types.py",
        "db/__init__.py",
        "db/populate_db.py",
        "db/queries.py",
        "dashboard/__init__.py",
        "dashboard/views.py",
        "dashboard/app.py",
        "tests/__init__.py",
        "tests/validation.py",
    ]

    missing_files = []

    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            logger.info(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            logger.error(f"  ❌ {file_path}")

    # Check that old files are removed
    old_files = [
        "api/server.py",
        "api/sqlite_backend.py",
        "dashboard.html",
        "components/dashboard-core.js",
        "assets/dashboard.css",
    ]

    remaining_old_files = []
    for file_path in old_files:
        full_path = Path(file_path)
        if full_path.exists():
            remaining_old_files.append(file_path)
            logger.warning(f"  ⚠️ Old file still exists: {file_path}")
        else:
            logger.info(f"  ✅ Old file removed: {file_path}")

    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False

    if remaining_old_files:
        logger.warning(f"Old files still present: {remaining_old_files}")
        logger.warning("These should be removed to complete the migration")

    logger.info("✅ File structure validation passed")
    return True


def test_models():
    """Test Pydantic models."""
    logger.info("📋 Testing Pydantic models...")

    try:
        from models.types import (
            AnalysisConfigForm,
            ClassRecord,
            ComplexityLevel,
            DomainType,
            FileFilterForm,
            FileRecord,
            FileType,
            FunctionRecord,
        )

        # Test FileRecord creation and validation
        file_record = FileRecord(
            name="test.py",
            path="src/test.py",
            domain=DomainType.TESTS,
            file_type=FileType.PYTHON,
            complexity=15,
            lines_of_code=200,
            classes_count=2,
            functions_count=5,
            imports_count=3,
            pydantic_models_count=1,
        )

        assert file_record.complexity_level == ComplexityLevel.MEDIUM
        logger.info("  ✅ FileRecord validation")

        # Test form validation
        filter_form = FileFilterForm(
            domain=DomainType.TESTS, min_lines=10, max_lines=1000
        )
        logger.info("  ✅ FileFilterForm validation")

        # Test config form with temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config_form = AnalysisConfigForm(
                project_root=temp_dir,
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__"],
            )
            logger.info("  ✅ AnalysisConfigForm validation")

        logger.info("✅ Pydantic models test passed")
        return True

    except Exception as e:
        logger.error(f"❌ Pydantic models test failed: {e}")
        return False


def test_database_operations():
    """Test database operations."""
    logger.info("🗄️ Testing database operations...")

    try:
        from db.populate_db import ASTAnalyzer, DatabasePopulator
        from db.queries import DatabaseQuerier

        from models.types import DomainType

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            db_path = temp_db.name

        try:
            # Test database creation
            populator = DatabasePopulator(db_path)
            populator.create_tables()
            logger.info("  ✅ Database table creation")

            # Test querier
            querier = DatabaseQuerier(db_path)
            files, count = querier.get_all_files()
            logger.info("  ✅ Database query operations")

            # Test AST analyzer
            analyzer = ASTAnalyzer()
            test_domain = analyzer._classify_domain(Path("src/models/user.py"))
            assert test_domain == DomainType.MODELS
            logger.info("  ✅ AST analyzer operations")

        finally:
            # Clean up references
            if "populator" in locals():
                del populator
            if "querier" in locals():
                del querier
            if "analyzer" in locals():
                del analyzer

            # Force garbage collection
            import gc

            gc.collect()

            # Try to remove the file with retry
            import time

            for attempt in range(3):
                try:
                    Path(db_path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.1)
                    else:
                        pass  # Skip cleanup if still locked

        logger.info("✅ Database operations test passed")
        return True

    except Exception as e:
        logger.error(f"❌ Database operations test failed: {e}")
        return False


def test_panel_components():
    """Test Panel components can be imported and created."""
    logger.info("🎛️ Testing Panel components...")

    try:
        import panel as pn

        # Test Panel extension
        pn.extension("bokeh", "tabulator")
        logger.info("  ✅ Panel extensions loaded")

        # Test dashboard components import
        from dashboard.views import create_dashboard

        logger.info("  ✅ Dashboard components imported")

        # Test basic widget creation
        text_input = pn.widgets.TextInput(name="Test", value="test")
        assert text_input.value == "test"
        logger.info("  ✅ Panel widgets creation")

        logger.info("✅ Panel components test passed")
        return True

    except Exception as e:
        logger.error(f"❌ Panel components test failed: {e}")
        return False


def run_comprehensive_tests():
    """Run the comprehensive test suite."""
    logger.info("🧪 Running comprehensive test suite...")

    try:
        from tests.validation import run_validation_suite

        success = run_validation_suite()

        if success:
            logger.info("✅ Comprehensive test suite passed")
            return True
        else:
            logger.error("❌ Comprehensive test suite failed")
            return False

    except Exception as e:
        logger.error(f"❌ Error running comprehensive tests: {e}")
        return False


def test_sample_analysis(project_path: Optional[str] = None):
    """Test analysis on a sample project."""
    if not project_path:
        project_path = str(Path.cwd())

    logger.info(f"📊 Testing sample analysis on: {project_path}")

    try:
        from db.populate_db import DatabasePopulator
        from db.queries import DatabaseQuerier

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            db_path = temp_db.name

        try:
            # Run analysis
            populator = DatabasePopulator(db_path)
            populator.create_tables()
            populator.populate_from_directory(
                Path(project_path),
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__", "*.pyc", ".git"],
            )

            # Query results
            querier = DatabaseQuerier(db_path)
            files, file_count = querier.get_all_files()
            classes, class_count = querier.get_all_classes()
            functions, func_count = querier.get_all_functions()
            stats = querier.get_system_stats()

            logger.info(f"  📁 Analyzed {file_count} files")
            logger.info(f"  🏗️ Found {class_count} classes")
            logger.info(f"  ⚙️ Found {func_count} functions")
            logger.info(f"  📊 Average complexity: {stats.avg_complexity}")

            if file_count > 0:
                logger.info("✅ Sample analysis test passed")
                return True
            else:
                logger.warning("⚠️ No files found in analysis")
                return False

        finally:
            Path(db_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"❌ Sample analysis test failed: {e}")
        return False


def main():
    """Main migration validation function."""
    logger.info("🚀 Starting Migration Validation")
    logger.info("=" * 60)

    project_path = sys.argv[1] if len(sys.argv) > 1 else None

    tests = [
        ("Dependencies", check_dependencies),
        ("File Structure", validate_file_structure),
        ("Pydantic Models", test_models),
        ("Database Operations", test_database_operations),
        ("Panel Components", test_panel_components),
        ("Comprehensive Tests", run_comprehensive_tests),
    ]

    # Add sample analysis if project path provided
    if project_path:
        tests.append(("Sample Analysis", lambda: test_sample_analysis(project_path)))

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} Test...")
        try:
            if test_func():
                passed_tests += 1
            else:
                logger.error(f"❌ {test_name} test failed")
        except Exception as e:
            logger.error(f"❌ {test_name} test error: {e}")

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 MIGRATION VALIDATION SUMMARY")
    logger.info("=" * 60)

    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Migration from FastAPI/JavaScript to Panel is COMPLETE")
        logger.info("✅ Dashboard is ready for production use")
        logger.info("\n🚀 To start the dashboard:")
        logger.info("   panel serve dashboard/app.py --show --autoreload")
        return True
    else:
        logger.error(
            f"❌ {total_tests - passed_tests} out of {total_tests} tests failed"
        )
        logger.error("❌ Migration validation incomplete")
        logger.error("Please check the logs and fix the issues above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
