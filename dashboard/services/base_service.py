"""
Base service classes for the dashboard submodule.

This module provides common patterns and base classes for all dashboard services.
It ensures consistent logging, error handling, and async patterns across services.

**Last Updated:** 2025-01-27 15:30:00
"""

import asyncio
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Generic, Optional, TypeVar

from ..dashboard_logging import get_logger

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def timing_decorator(func: F) -> F:
    """Decorator to log method execution time."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_logger(func.__module__)

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    "execution_time": execution_time,
                    "function": func.__name__,
                    "module": func.__module__,
                },
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.3f}s",
                extra={
                    "execution_time": execution_time,
                    "function": func.__name__,
                    "module": func.__module__,
                    "error": str(e),
                },
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_logger(func.__module__)

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    "execution_time": execution_time,
                    "function": func.__name__,
                    "module": func.__module__,
                },
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.3f}s",
                extra={
                    "execution_time": execution_time,
                    "function": func.__name__,
                    "module": func.__module__,
                    "error": str(e),
                },
            )
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class BaseService(ABC):
    """
    Abstract base class for all dashboard services.

    Provides common patterns for logging, error handling, and configuration.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize the base service.

        Args:
            name: Optional service name for logging context
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"{self.__module__}.{self.__class__.__name__}")
        self._initialized = False

        self.logger.debug(f"Initializing {self.name}")

    async def initialize(self) -> None:
        """
        Initialize the service asynchronously.

        Override this method to perform async initialization.
        """
        if self._initialized:
            self.logger.debug(f"{self.name} already initialized")
            return

        self.logger.info(f"Initializing {self.name}")
        await self._initialize_impl()
        self._initialized = True
        self.logger.info(f"{self.name} initialized successfully")

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """
        Implement service-specific initialization logic.

        This method should be overridden by concrete service classes.
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the service.

        Returns:
            Dictionary containing health status information
        """
        return {
            "service": self.name,
            "initialized": self._initialized,
            "status": "healthy" if self._initialized else "not_initialized",
        }

    def _log_operation(self, operation: str, **kwargs) -> None:
        """
        Log a service operation with structured logging.

        Args:
            operation: Name of the operation
            **kwargs: Additional context for logging
        """
        self.logger.info(
            f"{self.name}: {operation}",
            extra={"service": self.name, "operation": operation, **kwargs},
        )

    def _log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """
        Log a service error with structured logging.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            **kwargs: Additional context for logging
        """
        self.logger.error(
            f"{self.name}: {operation} failed - {str(error)}",
            extra={
                "service": self.name,
                "operation": operation,
                "error": str(error),
                "error_type": type(error).__name__,
                **kwargs,
            },
        )


class AsyncService(BaseService, Generic[T]):
    """
    Base class for async services with common async patterns.

    Provides connection management, retry logic, and async context management.
    """

    def __init__(self, name: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the async service.

        Args:
            name: Optional service name for logging context
            max_retries: Maximum number of retries for operations
        """
        super().__init__(name)
        self.max_retries = max_retries
        self._connection = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def cleanup(self) -> None:
        """
        Cleanup service resources.

        Override this method to perform service-specific cleanup.
        """
        self.logger.debug(f"Cleaning up {self.name}")
        await self._cleanup_impl()
        self._initialized = False
        self.logger.debug(f"{self.name} cleanup completed")

    async def _cleanup_impl(self) -> None:
        """
        Implement service-specific cleanup logic.

        This method should be overridden by concrete service classes.
        """
        pass

    async def retry_operation(self, operation, *args, **kwargs) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation: The async operation to retry
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            The last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.debug(
                        f"Retrying {operation.__name__} (attempt {attempt + 1}/{self.max_retries + 1}) after {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)

                return await operation(*args, **kwargs)

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"{operation.__name__} failed on attempt {attempt + 1}: {str(e)}"
                )

                if attempt == self.max_retries:
                    self._log_error(f"{operation.__name__}_retry_exhausted", e)
                    break

        raise last_exception
