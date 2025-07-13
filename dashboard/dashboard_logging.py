"""
Core Logging System - Central logging setup and configuration for dashboard submodule.

This module contains the core logging infrastructure using Loguru,
including setup, configuration, and structured logging handlers.
All logging-related setup and configuration should be here.

**Last Updated:** 2025-07-11 00:00:00
"""

import asyncio
import sys
import threading
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, TypeVar, overload

from loguru import logger as _loguru_logger
from rich.logging import RichHandler

# Import settings only when needed to avoid circular imports

# --- Core Logger Setup ---
logger: Any = _loguru_logger

# Add custom SUCCESS level to loguru if it doesn't exist
try:
    logger.level("SUCCESS", no=25, color="<green>", icon="✅")
except ValueError:
    # SUCCESS level already exists, that's fine
    pass

# Add success method to logger if it doesn't exist
if not hasattr(logger, "success"):

    def _success(message: Any, *args: Any, **kwargs: Any) -> None:
        """Log a success message."""
        logger.log("SUCCESS", message, *args, **kwargs)

    logger.success = _success

F = TypeVar("F", bound=Callable[..., Any])


def setup_logging(settings: Any) -> Any:
    """
    Configure logging based on dashboard settings.
    - In non-verbose mode, only warnings/errors go to terminal; info/success go to file only.
    - In verbose mode, all logs go to terminal and file.
    """
    # Remove default logger
    logger.remove()

    # Determine verbosity
    verbosity = getattr(settings.output, "verbosity", "info").lower()
    log_config = settings.logging

    # Console logging: only warnings/errors in normal mode, all in verbose
    if verbosity in ("debug", "verbose"):
        logger.add(
            RichHandler(rich_tracebacks=True, markup=True),
            level=log_config.level,
            format=log_config.format,
        )
    else:
        # Only warnings/errors to terminal
        logger.add(
            sys.stderr,
            level="WARNING",
            format=log_config.format,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # File logging if configured
    if log_config.files:
        for log_name, log_path in log_config.files.items():
            log_file_path = Path(log_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_level = log_config.levels.get(log_name, log_config.level)
            logger.add(
                log_file_path,
                level=file_level,
                format=log_config.format,
                rotation=log_config.rotation.get(log_name, "1 week"),
                retention="1 month",
                compression="gz",
                backtrace=True,
                diagnose=True,
            )

    # Performance log
    logger.add(
        settings.log_file,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[operation]} | {extra[duration]:.3f}s | {message}",
        filter=lambda record: bool(record.get("extra", {}).get("performance", False)),
        rotation="1 day",
        retention="1 week",
    )

    logger.info("Dashboard logging configuration completed")
    return logger


def get_logger(name: str) -> Any:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance with custom methods
    """
    bound_logger = logger.bind(module=name)

    def _step_bound(step_num: int, title: str, description: str = "") -> None:
        """Log a structured step with number, title, and optional description."""
        message = f"Step {step_num}: {title}"
        if description:
            message += f" - {description}"
        bound_logger.log("SUCCESS", message)

    def _phase_bound(phase_name: str, description: str = "") -> None:
        """Log a phase or section header."""
        message = f"=== {phase_name.upper()} ==="
        if description:
            message += f" - {description}"
        bound_logger.info(message)

    def _metric_bound(name: str, value: Any, unit: str = "", **context: Any) -> None:
        """Log a performance or operational metric."""
        message = f"📊 {name}: {value}"
        if unit:
            message += f" {unit}"
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            message += f" ({context_str})"
        bound_logger.info(message)

    def _status_bound(
        operation: str, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log operation status with optional details."""
        status_icons = {
            "started": "🚀",
            "running": "⚙️",
            "completed": "✅",
            "success": "✅",
            "failed": "❌",
            "error": "❌",
            "warning": "⚠️",
            "skipped": "⏭️",
            "pending": "⏳",
        }

        icon = status_icons.get(status.lower(), "ℹ️")
        message = f"{icon} {operation}: {status}"
        if details:
            if isinstance(details, dict):
                formatted_details = ", ".join(
                    [f"{str(key)}={repr(value)}" for key, value in details.items()]
                )
                message += f" ({formatted_details})"
            else:
                message += f" ({repr(details)})"

        if status.lower() in ["failed", "error"]:
            bound_logger.error(message)
        elif status.lower() == "warning":
            bound_logger.warning(message)
        elif status.lower() in ["completed", "success"]:
            bound_logger.log("SUCCESS", message)
        else:
            bound_logger.info(message)

    bound_logger.step = _step_bound
    bound_logger.phase = _phase_bound
    bound_logger.metric = _metric_bound
    bound_logger.status = _status_bound

    return bound_logger


def configure_logging(level: str = "INFO") -> None:
    """
    Configure logging with a simple interface for CLI usage.

    This is a convenience function that provides backward compatibility
    with the legacy CLI interface while using the new Settings-based
    logging configuration.

    Args:
        level: Log level to set (DEBUG, INFO, WARNING, ERROR)
    """
    # Import here to avoid circular imports
    from dashboard.settings import DashboardSettings

    # Create minimal settings with the requested log level
    settings = DashboardSettings.from_yaml()
    settings.logging.level = level.upper()

    # Use the main setup_logging function
    setup_logging(settings)


@overload
def log_performance(func: Optional[F]) -> F: ...


@overload
def log_performance(
    *, operation: Optional[str] = None, level: str = "INFO"
) -> Callable[[F], F]: ...


def log_performance(
    func: Optional[F] = None, *, operation: Optional[str] = None, level: str = "INFO"
) -> Any:
    """
    Decorator to log function execution time and performance.

    Can be used as @log_performance or @log_performance(operation="Custom Name")

    Args:
        func: Function to wrap (when used without parameters)
        operation: Custom operation name for logging
        level: Log level to use (DEBUG, INFO, etc.)

    Returns:
        Decorated function or decorator
    """

    def decorator(f: F) -> F:
        @wraps(f)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation or f"async {f.__name__}"
            start_time = time.time()

            logger.debug(f"⚡ Starting {op_name}")

            try:
                result = await f(*args, **kwargs)
                duration = time.time() - start_time

                # Log with performance metadata for filtering
                logger.bind(performance=True).log(
                    level.upper(),
                    f"⚡ Completed {op_name}",
                    operation=op_name,
                    duration=duration,
                    success=True,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.bind(performance=True).error(
                    f"⚡ Failed {op_name}: {str(e)}",
                    operation=op_name,
                    duration=duration,
                    success=False,
                    error=str(e),
                )
                raise

        @wraps(f)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation or f.__name__
            start_time = time.time()

            logger.debug(f"⚡ Starting {op_name}")

            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time

                # Log with performance metadata for filtering
                logger.bind(performance=True).log(
                    level.upper(),
                    f"⚡ Completed {op_name}",
                    operation=op_name,
                    duration=duration,
                    success=True,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.bind(performance=True).error(
                    f"⚡ Failed {op_name}: {str(e)}",
                    operation=op_name,
                    duration=duration,
                    success=False,
                    error=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(f):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    if func is None:
        return decorator
    else:
        return decorator(func)


@contextmanager
def log_operation(operation_name: str) -> Generator[None, None, None]:
    """
    Context manager for logging operation start and completion with timing.

    Args:
        operation_name: Name of the operation being performed

    Usage:
        with log_operation("Data Processing"):
            process_data()
    """
    start_time = time.time()
    logger.info(f"🚀 Starting {operation_name}")

    try:
        yield
        duration = time.time() - start_time
        logger.success(f"✅ Completed {operation_name} in {duration:.2f}s")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Failed {operation_name} after {duration:.2f}s: {str(e)}")
        raise


@contextmanager
def log_batch_operation(
    operation_name: str, total_items: int, batch_size: int = 10
) -> Generator[Callable[[int], None], None, None]:
    """
    Context manager for batch operations with progress logging.

    Args:
        operation_name: Name of the batch operation
        total_items: Total number of items to process
        batch_size: How often to log progress

    Usage:
        with log_batch_operation("Processing Files", 100) as log_progress:
            for i, file in enumerate(files):
                process_file(file)
                log_progress(i + 1)
    """
    start_time = time.time()
    logger.info(f"🚀 Starting {operation_name} ({total_items} items)")

    def log_progress_func(current: int) -> None:
        if current % batch_size == 0 or current == total_items:
            percentage = (current / total_items) * 100 if total_items > 0 else 0
            elapsed = time.time() - start_time
            rate = current / elapsed if elapsed > 0 else 0
            logger.info(
                f"📊 {operation_name}: {current}/{total_items} ({percentage:.1f}%) - {rate:.1f} items/sec"
            )

    try:
        yield log_progress_func
        duration = time.time() - start_time
        rate = total_items / duration if duration > 0 else 0
        logger.success(
            f"✅ Completed {operation_name}: {total_items} items in {duration:.2f}s ({rate:.1f} items/sec)"
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Failed {operation_name} after {duration:.2f}s: {str(e)}")
        raise


# Specialized logging functions
def log_api_request(method: str, url: str, status_code: int, duration: float) -> None:
    """Log API request details"""
    logger.info(f"🌐 {method} {url} → {status_code} ({duration:.3f}s)")


def log_database_operation(
    operation: str, table: str, affected_rows: int, duration: float
) -> None:
    """Log database operation details"""
    logger.info(f"🗄️ {operation} {table}: {affected_rows} rows ({duration:.3f}s)")


def log_cache_operation(
    operation: str,
    key: str,
    hit: bool,
    size: Optional[int] = None,
    ttl: Optional[int] = None,
) -> None:
    """Log cache operation details"""
    hit_status = "HIT" if hit else "MISS"
    size_info = f", {size} bytes" if size else ""
    ttl_info = f", TTL: {ttl}s" if ttl else ""
    logger.info(f"💾 Cache {operation} {key}: {hit_status}{size_info}{ttl_info}")


def log_model_operation(
    operation: str, model_name: str, duration: float, tokens: int = 0
) -> None:
    """Log AI model operation details"""
    token_info = f", {tokens} tokens" if tokens > 0 else ""
    logger.info(f"🤖 {operation} {model_name}: {duration:.3f}s{token_info}")


def log_excel_operation(
    operation: str, filename: str, sheet_name: str, rows: int, cols: int
) -> None:
    """Log Excel file operation details"""
    logger.info(f"📊 {operation} {filename}[{sheet_name}]: {rows}x{cols}")


def log_system_health(
    component: str,
    status: str,
    details: Dict[str, Any],
    metrics: Optional[Dict[str, float]] = None,
) -> None:
    """Log system health check details"""
    status_icon = "✅" if status == "healthy" else "❌"
    details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
    metrics_str = ""
    if metrics:
        metrics_str = ", " + ", ".join([f"{k}={v:.2f}" for k, v in metrics.items()])
    logger.info(f"{status_icon} {component}: {status} ({details_str}{metrics_str})")


def log_configuration_change(
    component: str, setting: str, old_value: Any, new_value: Any
) -> None:
    """Log configuration changes for audit purposes"""
    logger.info(f"⚙️ Config changed: {component}.{setting} {old_value} → {new_value}")


def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "INFO",
    user: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Log security-related events"""
    user_info = f", user={user}" if user else ""
    ip_info = f", ip={ip_address}" if ip_address else ""
    details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
    logger.log(
        severity.upper(),
        f"🔒 Security event: {event_type} ({details_str}{user_info}{ip_info})",
    )


def log_resource_usage(
    resource_type: str, current: float, limit: float, unit: str, threshold: float = 0.8
) -> None:
    """Log resource usage with threshold warnings"""
    percentage = (current / limit) * 100 if limit > 0 else 0
    if percentage >= threshold * 100:
        logger.warning(
            f"⚠️ High {resource_type} usage: {current:.2f}/{limit:.2f} {unit} ({percentage:.1f}%)"
        )
    else:
        logger.info(
            f"📊 {resource_type} usage: {current:.2f}/{limit:.2f} {unit} ({percentage:.1f}%)"
        )
