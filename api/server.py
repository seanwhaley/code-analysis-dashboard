#!/usr/bin/env python3
"""
FastAPI Server for USASpending v4 Code Intelligence Dashboard

**Last Updated:** 2025-07-05 12:00:00

This module provides a lightweight REST API server that connects the interactive
code intelligence dashboard to the SQLite backend, enabling real-time data queries
and enhanced search functionality.

Features:
- RESTful API endpoints for files, classes, functions, and search
- Real-time data filtering and pagination
- CORS support for development
- Static file serving for dashboard assets
- Health monitoring and metrics
"""

import logging
import os

# Import the SQLite backend (local copy)
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(__file__))

try:
    from sqlite_backend import DocumentationDatabase
except ImportError as e:
    print(f"❌ Failed to import sqlite_backend: {e}")
    print(f"   Make sure sqlite_backend.py is in the api directory")
    sys.exit(1)
    raise


# Pydantic Response Models
class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    success: bool = Field(..., description="Whether the request was successful")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Response timestamp",
    )

    class Config:
        from_attributes = True


from typing import Generic, TypeVar

T = TypeVar("T")


# Generic base class for paginated responses
class PaginatedResponse(BaseResponse, Generic[T]):
    data: List[T]
    pagination: "PaginationInfo"


# Generic base class for single-record responses
class SingleRecordResponse(BaseResponse, Generic[T]):
    data: T


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: str = Field(..., description="Health status")
    database: str = Field(..., description="Database connection status")
    files_count: int = Field(..., description="Number of files in database")
    models_count: int = Field(..., description="Number of models in database")


class StatsResponse(BaseResponse):
    """System statistics response model."""

    data: Dict[str, Any] = Field(..., description="System statistics data")


class PaginationInfo(BaseModel):
    """Pagination information model."""

    total: int = Field(..., description="Total number of items")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more items")
    has_prev: bool = Field(..., description="Whether there are previous items")


class FileRecord(BaseModel):
    """File record model."""

    id: int = Field(..., description="File ID")
    name: str = Field(..., description="File name", min_length=1)
    path: str = Field(..., description="File path", min_length=1)
    domain: str = Field(..., description="Domain classification", min_length=1)
    complexity: int = Field(..., description="Complexity score")
    classes: int = Field(..., description="Number of classes")
    functions: int = Field(..., description="Number of functions")
    lines: int = Field(..., description="Number of lines")
    file_type: str = Field(default="file", description="File type", min_length=1)

    class Config:
        from_attributes = True


class FilesResponse(PaginatedResponse[FileRecord]):
    """Files list response model."""

    pass


class FileRecordResponse(SingleRecordResponse[FileRecord]):
    """Single file response model."""

    pass


class DetailedFileResponse(BaseResponse):
    """Detailed file response model with AST data."""

    data: Dict[str, Any] = Field(
        ..., description="Detailed file data with AST information"
    )


class ClassRecord(BaseModel):
    """Class record model."""

    id: int = Field(..., description="Class ID")
    name: str = Field(..., description="Class name", min_length=1)
    file_id: int = Field(..., description="File ID containing the class")
    file_path: str = Field(..., description="File path", min_length=1)
    domain: str = Field(..., description="Domain classification", min_length=1)
    class_type: str = Field(..., description="Type of class", min_length=1)
    methods_count: int = Field(..., description="Number of methods")
    line_number: int = Field(..., description="Starting line number")

    class Config:
        from_attributes = True


class ClassesResponse(PaginatedResponse[ClassRecord]):
    """Classes list response model."""

    pass


class ClassRecordResponse(SingleRecordResponse[ClassRecord]):
    """Single class record response model."""

    pass


class FunctionRecord(BaseModel):
    """Function record model."""

    id: int = Field(..., description="Function ID")
    name: str = Field(..., description="Function name", min_length=1)
    file_id: int = Field(..., description="File ID containing the function")
    class_id: Optional[int] = Field(None, description="Class ID if method")
    file_path: str = Field(..., description="File path", min_length=1)
    function_type: str = Field(..., description="Type of function", min_length=1)
    parameters_count: int = Field(..., description="Number of parameters")
    parameters: Optional[str] = Field(None, description="Function parameters")
    line_number: int = Field(..., description="Starting line number")
    is_async: bool = Field(..., description="Whether function is async")

    class Config:
        from_attributes = True


class FunctionsResponse(PaginatedResponse[FunctionRecord]):
    """Functions list response model."""

    pass


class FunctionRecordResponse(SingleRecordResponse[FunctionRecord]):
    """Single function record response model."""

    pass


class SearchResult(BaseModel):
    """Search result item model."""

    id: int = Field(..., description="Item ID")
    name: str = Field(..., description="Item name", min_length=1)
    type: str = Field(
        ..., description="Item type (file, class, function)", min_length=1
    )
    file_path: Optional[str] = Field(None, description="File path")
    domain: Optional[str] = Field(None, description="Domain classification")

    class Config:
        from_attributes = True


class SearchResponse(BaseResponse):
    """Search results response model."""

    data: List[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Search query")
    search_type: str = Field(..., description="Type of search performed")
    total: int = Field(..., description="Total number of results")


class DomainStats(BaseModel):
    """Domain statistics model."""

    name: str = Field(..., description="Domain name", min_length=1)
    file_count: int = Field(..., description="Number of files in domain")
    model_count: int = Field(..., description="Number of models in domain")

    class Config:
        from_attributes = True


class DomainsResponse(BaseResponse):
    """Domains response model."""

    data: List[DomainStats] = Field(..., description="Domain statistics")


class ComplexityDistribution(BaseModel):
    """Complexity distribution model."""

    complexity_range: str = Field(..., description="Complexity range", min_length=1)
    count: int = Field(..., description="Number of files in range")

    class Config:
        from_attributes = True


class ComplexityResponse(BaseResponse):
    """Complexity distribution response model."""

    data: List[ComplexityDistribution] = Field(
        ..., description="Complexity distribution"
    )


class ServiceRecord(BaseModel):
    """Service record model."""

    id: int = Field(..., description="Service ID")
    name: str = Field(..., description="Service name", min_length=1)
    file_id: int = Field(..., description="File ID containing the service")
    file_path: str = Field(..., description="File path", min_length=1)
    domain: str = Field(..., description="Domain classification", min_length=1)
    class_type: str = Field(..., description="Type of service class", min_length=1)
    methods_count: int = Field(..., description="Number of methods")
    line_number: int = Field(..., description="Starting line number")

    class Config:
        from_attributes = True


class ServicesResponse(PaginatedResponse[ServiceRecord]):
    """Services list response model."""

    pass


class DebugResponse(BaseResponse):
    """Debug endpoint response model."""

    data: Dict[str, Any] = Field(..., description="Debug information")


class DecoratorRecord(BaseModel):
    """Decorator record model."""

    id: int = Field(..., description="Decorator ID")
    name: str = Field(..., description="Decorator name", min_length=1)
    file_id: int = Field(..., description="File ID containing the decorator")
    function_id: Optional[int] = Field(
        None, description="Function ID if decorator is on function"
    )
    class_id: Optional[int] = Field(
        None, description="Class ID if decorator is on class"
    )
    file_path: str = Field(..., description="File path", min_length=1)
    decorator_type: str = Field(..., description="Type of decorator", min_length=1)
    line_number: int = Field(..., description="Line number of decorator")

    class Config:
        from_attributes = True


class DecoratorsResponse(PaginatedResponse[DecoratorRecord]):
    """Decorators list response model."""

    pass


class RelationshipRecord(BaseModel):
    """Relationship record model."""

    id: int = Field(..., description="Relationship ID")
    source_type: str = Field(
        ..., description="Source type (class, function, file)", min_length=1
    )
    source_id: int = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name", min_length=1)
    target_type: str = Field(
        ..., description="Target type (class, function, file)", min_length=1
    )
    target_id: int = Field(..., description="Target ID")
    target_name: str = Field(..., description="Target name", min_length=1)
    relationship_type: str = Field(
        ..., description="Type of relationship (inherits, calls, imports)", min_length=1
    )
    file_path: str = Field(
        ..., description="File path where relationship is defined", min_length=1
    )

    class Config:
        from_attributes = True


class RelationshipsResponse(PaginatedResponse[RelationshipRecord]):
    """Relationships list response model."""

    pass


# Initialize FastAPI app
app = FastAPI(
    title="USASpending Code Intelligence API",
    description="REST API for code intelligence dashboard",
    version="1.0.0",
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger = logging.getLogger("api.server")


# Debug logging middleware
from typing import Awaitable, Callable


@app.middleware("http")
async def debug_logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add debug logging for requests and responses."""
    start_time = datetime.now()

    # Log request details if debug level
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"🔍 {request.method} {request.url}")
        if request.query_params:
            logger.debug(f"   Query params: {dict(request.query_params)}")

    # Process request
    response: Response = await call_next(request)

    # Log response details if debug level
    if logger.isEnabledFor(logging.DEBUG):
        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.debug(
            f"✅ {request.method} {request.url} -> {response.status_code} ({duration:.1f}ms)"
        )

    return response


# No-cache middleware for development
@app.middleware("http")
async def no_cache_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add no-cache headers for static files during development."""
    response: Response = await call_next(request)

    # Add no-cache headers for static files (JS, CSS, etc.)
    if (
        request.url.path.startswith("/components/")
        or request.url.path.startswith("/assets/")
        or request.url.path.endswith(".js")
        or request.url.path.endswith(".css")
    ):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# Initialize database - use local database file
db_path = Path(__file__).parent / "documentation.db"
db = DocumentationDatabase(str(db_path))

# Mount static files for dashboard assets
app.mount(
    "/assets",
    StaticFiles(directory=Path(__file__).parent.parent / "assets"),
    name="assets",
)
app.mount(
    "/components",
    StaticFiles(directory=Path(__file__).parent.parent / "components"),
    name="components",
)

# Global stats cache
_stats_cache = None
_cache_timestamp = None
CACHE_DURATION = 300  # 5 minutes


def get_cached_stats() -> Dict[str, Any]:
    """Get cached system statistics."""
    global _stats_cache, _cache_timestamp

    now = datetime.now()
    if (
        _stats_cache is None
        or _cache_timestamp is None
        or (now - _cache_timestamp).total_seconds() > CACHE_DURATION
    ):
        base_stats = db.get_system_stats()

        # Add counts for classes and functions
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM classes")
            total_classes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM functions")
            total_functions = cursor.fetchone()[0]

        _stats_cache = {
            **base_stats,
            "total_classes": total_classes,
            "total_functions": total_functions,
        }
        _cache_timestamp = now

    return _stats_cache


@app.get("/", response_model=None)
async def root() -> Response:
    """Root endpoint - serve ONLY the main dashboard (no update/test page)."""
    dashboard_path = Path(__file__).parent.parent / "dashboard.html"
    return FileResponse(dashboard_path)


@app.get("/dashboard", response_model=None)
async def dashboard() -> Response:
    """Main dashboard endpoint."""
    dashboard_path = Path(__file__).parent.parent / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    else:
        return JSONResponse(
            {"message": "Dashboard not found", "path": str(dashboard_path)},
            status_code=404,
        )


@app.get("/debug_dashboard.html", response_model=None)
async def debug_dashboard() -> Response:
    """Debug dashboard endpoint."""
    debug_path = Path(__file__).parent.parent / "debug_dashboard.html"
    if debug_path.exists():
        return FileResponse(debug_path)
    else:
        return JSONResponse(
            {"message": "Debug dashboard not found", "path": str(debug_path)},
            status_code=404,
        )


@app.get("/health", response_model=Union[HealthResponse, ErrorResponse])
async def health_check() -> Union[HealthResponse, ErrorResponse]:
    """Health check endpoint."""
    try:
        # Test database connectivity
        stats = db.get_system_stats()
        return HealthResponse(
            success=True,
            status="healthy",
            database="connected",
            files_count=stats.get("total_files", 0),
            models_count=stats.get("total_models", 0),
        )
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get system statistics."""
    try:
        stats = get_cached_stats()
        return StatsResponse(success=True, data=stats)
    except Exception as e:
        return ErrorResponse(success=False, error=f"Failed to get stats: {str(e)}")


@app.get("/api/files", response_model=Union[FilesResponse, ErrorResponse])
async def get_files(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    min_complexity: Optional[int] = Query(None),
    max_complexity: Optional[int] = Query(None),
) -> Union[FilesResponse, ErrorResponse]:
    """Get paginated files with optional filtering."""
    try:
        files = db.search_files(
            query=search,
            domain=domain,
            complexity_min=min_complexity,
            complexity_max=max_complexity,
            limit=limit,
            offset=offset,
        )

        # Get actual total count from database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            count_query = "SELECT COUNT(*) FROM files"
            count_params = []

            # Add filters if provided
            where_conditions: list[str] = []
            count_params: list[Any] = []
            if search:
                where_conditions.append("(name LIKE ? OR path LIKE ?)")
                count_params.extend([f"%{search}%", f"%{search}%"])
            if domain:
                where_conditions.append("domain = ?")
                count_params.append(domain)
            if min_complexity is not None:
                where_conditions.append("complexity >= ?")
                count_params.append(min_complexity)
            if max_complexity is not None:
                where_conditions.append("complexity <= ?")
                count_params.append(max_complexity)

            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

        return FilesResponse(
            success=True,
            data=[FileRecord(**file) for file in files],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get("/api/file/{file_id}", response_model=Union[FileRecordResponse, ErrorResponse])
async def get_file(file_id: int) -> Union[FileRecordResponse, ErrorResponse]:
    """Get specific file by ID."""
    try:
        # Use search_files but filter by exact file name/path match
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file_row = cursor.fetchone()

        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")

        file = dict(file_row)
        return FileRecordResponse(success=True, data=FileRecord(**file))
    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get(
    "/api/file/{file_id}/detailed",
    response_model=Union[DetailedFileResponse, ErrorResponse],
)
async def get_file_detailed(file_id: int) -> Union[DetailedFileResponse, ErrorResponse]:
    """Get detailed file content with AST data."""
    try:
        file_data = db.get_file_detailed_content(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")

        return DetailedFileResponse(success=True, data=file_data)
    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get("/api/classes", response_model=Union[ClassesResponse, ErrorResponse])
async def get_classes(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    file_id: Optional[int] = Query(None),
    class_type: Optional[str] = Query(None),
) -> Union[ClassesResponse, ErrorResponse]:
    """Get paginated classes with optional filtering."""
    try:
        classes = db.search_classes(
            query=search,
            class_type=class_type,
            limit=limit,
            offset=offset,
        )

        # Get actual total count from database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            count_query = "SELECT COUNT(*) FROM classes"
            count_params = []

            # Add filters if provided
            where_conditions: list[str] = []
            count_params: list[Any] = []
            if search:
                where_conditions.append("(name LIKE ? OR docstring LIKE ?)")
                count_params.extend([f"%{search}%", f"%{search}%"])
            if class_type:
                where_conditions.append("class_type = ?")
                count_params.append(class_type)

            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

        return ClassesResponse(
            success=True,
            data=[ClassRecord(**cls) for cls in classes],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get("/api/functions", response_model=Union[FunctionsResponse, ErrorResponse])
async def get_functions(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    file_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    function_type: Optional[str] = Query(None),
    is_async: Optional[bool] = Query(None),
) -> Union[FunctionsResponse, ErrorResponse]:
    """Get paginated functions with optional filtering."""
    try:
        functions = db.search_functions(
            query=search,
            function_type=function_type,
            class_id=class_id,
            limit=limit,
            offset=offset,
        )

        # Get actual total count from database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            count_query = "SELECT COUNT(*) FROM functions"
            count_params = []

            # Add filters if provided
            where_conditions: list[str] = []
            count_params: list[Any] = []
            if search:
                where_conditions.append("(name LIKE ? OR docstring LIKE ?)")
                count_params.extend([f"%{search}%", f"%{search}%"])
            if function_type:
                where_conditions.append("function_type = ?")
                count_params.append(function_type)
            if class_id:
                where_conditions.append("class_id = ?")
                count_params.append(class_id)
            if is_async is not None:
                where_conditions.append("is_async = ?")
                count_params.append(1 if is_async else 0)

            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

        # Ensure 'parameters' field is present in all function records
        for func in functions:
            if "parameters" not in func:
                func["parameters"] = None

        return FunctionsResponse(
            success=True,
            data=[FunctionRecord(**func) for func in functions],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return ErrorResponse(success=False, error=f"Failed to load functions: {str(e)}")


@app.get(
    "/api/files/{file_id}", response_model=Union[FileRecordResponse, ErrorResponse]
)
async def get_file_detail(file_id: int) -> Union[FileRecordResponse, ErrorResponse]:
    """Get detailed information about a specific file."""
    try:
        file_record = db.get_file_by_id(file_id)
        if not file_record:
            return ErrorResponse(
                success=False, error=f"File with ID {file_id} not found"
            )

        return FileRecordResponse(
            success=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=file_record,
        )
    except Exception as e:
        return ErrorResponse(
            success=False, error=f"Failed to load file details: {str(e)}"
        )


@app.get(
    "/api/classes/{class_id}", response_model=Union[ClassRecordResponse, ErrorResponse]
)
async def get_class_detail(class_id: int) -> Union[ClassRecordResponse, ErrorResponse]:
    """Get detailed information about a specific class."""
    try:
        class_record = db.get_class_by_id(class_id)
        if not class_record:
            return ErrorResponse(
                success=False, error=f"Class with ID {class_id} not found"
            )

        return ClassRecordResponse(
            success=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=class_record,
        )
    except Exception as e:
        return ErrorResponse(
            success=False, error=f"Failed to load class details: {str(e)}"
        )


@app.get(
    "/api/functions/{function_id}",
    response_model=Union[FunctionRecordResponse, ErrorResponse],
)
async def get_function_detail(
    function_id: int,
) -> Union[FunctionRecordResponse, ErrorResponse]:
    """Get detailed information about a specific function."""
    try:
        function_record = db.get_function_by_id(function_id)
        if not function_record:
            return ErrorResponse(
                success=False, error=f"Function with ID {function_id} not found"
            )

        return FunctionRecordResponse(
            success=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=function_record,
        )
    except Exception as e:
        return ErrorResponse(
            success=False, error=f"Failed to load function details: {str(e)}"
        )


@app.get("/api/services", response_model=Union[ServicesResponse, ErrorResponse])
async def get_services(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
) -> Response:
    """Get paginated services with optional filtering."""
    try:
        services = db.search_services(
            query=search,
            service_type=service_type,
            limit=limit,
            offset=offset,
        )

        # Get actual total count from database for service classes
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Service patterns to identify service classes
            service_patterns = [
                "Service",
                "Interface",
                "Validator",
                "Factory",
                "Manager",
                "Handler",
                "Provider",
                "Repository",
                "Controller",
                "Processor",
                "Engine",
                "Client",
            ]

            service_condition = " OR ".join(
                [f"name LIKE '%{pattern}%'" for pattern in service_patterns]
            )
            count_query = f"SELECT COUNT(*) FROM classes WHERE ({service_condition})"
            count_params = []

            # Add filters if provided
            where_conditions = [f"({service_condition})"]
            if search:
                where_conditions.append(
                    "(name LIKE ? OR file_path LIKE ? OR docstring LIKE ?)"
                )
                count_params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            if service_type:
                where_conditions.append("class_type = ?")
                count_params.append(service_type)

            if len(where_conditions) > 1:
                count_query = f"SELECT COUNT(*) FROM classes WHERE " + " AND ".join(
                    where_conditions
                )

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

        return ServicesResponse(
            success=True,
            data=[ServiceRecord(**service) for service in services],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False, error=f"Search failed: {str(e)}"
            ).model_dump(),
        )


@app.get("/api/search", response_model=Union[SearchResponse, ErrorResponse])
async def search_code(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    search_type: str = Query("all", pattern="^(all|files|classes|functions)$"),
) -> Union[SearchResponse, ErrorResponse]:
    """Search across code elements."""
    try:
        if len(q.strip()) < 2:
            return SearchResponse(
                success=True,
                data=[],
                query=q,
                search_type=search_type,
                total=0,
            )

        results = []

        # Search in different categories based on search_type
        if search_type in ("all", "files"):
            files = db.search_files(
                query=q, limit=limit // 3 if search_type == "all" else limit
            )
            for file in files:
                results.append(
                    SearchResult(
                        id=file.get("id", 0),
                        name=file.get("name", ""),
                        type="file",
                        file_path=file.get("file_path") or file.get("path"),
                        domain=file.get("domain"),
                    )
                )

        if search_type in ("all", "classes"):
            classes = db.search_classes(
                query=q, limit=limit // 3 if search_type == "all" else limit
            )
            for cls in classes:
                results.append(
                    SearchResult(
                        id=cls.get("id", 0),
                        name=cls.get("name", ""),
                        type="class",
                        file_path=cls.get("file_path") or cls.get("path"),
                        domain=cls.get("domain"),
                    )
                )

        if search_type in ("all", "functions"):
            functions = db.search_functions(
                query=q, limit=limit // 3 if search_type == "all" else limit
            )
            for func in functions:
                results.append(
                    SearchResult(
                        id=func.get("id", 0),
                        name=func.get("name", ""),
                        type="function",
                        file_path=func.get("file_path") or func.get("path"),
                        domain=func.get("domain"),
                    )
                )

        # Limit results to the requested limit
        search_results = results[:limit]

        return SearchResponse(
            success=True,
            data=search_results,
            query=q,
            search_type=search_type,
            total=len(results),
        )
    except Exception as e:
        return ErrorResponse(success=False, error=f"Search failed: {str(e)}")


@app.get("/api/domains", response_model=Union[DomainsResponse, ErrorResponse])
async def get_domains() -> Union[DomainsResponse, ErrorResponse]:
    """Get all domains with file counts."""
    try:
        domains = db.get_domain_statistics()
        domain_stats = [DomainStats(**domain) for domain in domains]
        return DomainsResponse(success=True, data=domain_stats)
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get(
    "/api/complexity/distribution",
    response_model=Union[ComplexityResponse, ErrorResponse],
)
async def get_complexity_distribution() -> Union[ComplexityResponse, ErrorResponse]:
    """Get complexity distribution across files."""
    try:
        distribution = db.get_complexity_distribution()
        complexity_data = [ComplexityDistribution(**item) for item in distribution]
        return ComplexityResponse(success=True, data=complexity_data)
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@app.get("/api/decorators", response_model=Union[DecoratorsResponse, ErrorResponse])
async def get_decorators(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    file_id: Optional[int] = Query(None),
) -> Union[DecoratorsResponse, ErrorResponse]:
    """Get paginated decorators with optional filtering."""
    try:
        decorators, total_count = db.get_decorators(
            limit=limit, offset=offset, search=search, file_id=file_id
        )

        return DecoratorsResponse(
            success=True,
            data=[DecoratorRecord(**decorator) for decorator in decorators],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return ErrorResponse(
            success=False, error=f"Failed to load decorators: {str(e)}"
        )


@app.get(
    "/api/relationships", response_model=Union[RelationshipsResponse, ErrorResponse]
)
async def get_relationships(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    relationship_type: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
) -> Union[RelationshipsResponse, ErrorResponse]:
    """Get paginated relationships with optional filtering."""
    try:
        relationships, total_count = db.get_relationships(
            limit=limit,
            offset=offset,
            search=search,
            relationship_type=relationship_type,
        )

        return RelationshipsResponse(
            success=True,
            data=[RelationshipRecord(**relationship) for relationship in relationships],
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
                has_prev=offset > 0,
            ),
        )
    except Exception as e:
        return ErrorResponse(
            success=False, error=f"Failed to load relationships: {str(e)}"
        )


# Debug endpoint for testing
@app.get("/api/debug/test", response_model=Union[DebugResponse, ErrorResponse])
async def debug_test() -> Union[DebugResponse, ErrorResponse]:
    """Debug endpoint for testing data."""
    try:
        # Test basic database connectivity
        stats = db.get_system_stats()

        # Test file queries
        sample_files = db.search_files(limit=3)

        # Test class queries
        sample_classes = db.search_classes(limit=3)

        # Test function queries
        sample_functions = db.search_functions(limit=3)

        return DebugResponse(
            success=True,
            data={
                "database_connected": True,
                "stats": stats,
                "sample_files": sample_files,
                "sample_classes": sample_classes,
                "sample_functions": sample_functions,
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


if __name__ == "__main__":
    port = 8001  # Use different port to avoid conflicts
    print("🚀 Starting USASpending Code Intelligence Dashboard Server...")
    print(f"📊 Dashboard available at: http://localhost:{port}")
    print(f"🔧 API documentation at: http://localhost:{port}/docs")
    print(f"❤️  Health check at: http://localhost:{port}/health")

    uvicorn.run(app, host="0.0.0.0", port=port)
