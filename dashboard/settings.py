"""
Dashboard submodule configuration and settings management using Pydantic for validation.

This module provides a comprehensive, type-safe configuration system for the Dashboard
submodule. It handles configuration loading from YAML files, environment
variable overrides, validation, and provides structured access to all system settings.

Key Features:
    * YAML-based configuration with environment variable overrides
    * Comprehensive validation using Pydantic models
    * Type-safe configuration access throughout the application
    * Support for development, staging, and production environments
    * Automatic credential loading from environment variables
    * Configuration export functionality for deployment

**Last Updated:** 2025-01-27 15:30:00
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

# Load environment variables from .env file if it exists
load_dotenv()

# Use a centralized config location within the submodule
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class SystemConfig(BaseModel):
    """System-level configuration with enhanced validation and documentation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
    )

    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development", description="Dashboard environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    timezone: str = Field(
        default="UTC", description="Timezone", pattern=r"^[A-Za-z_]+/[A-Za-z_]+$|^UTC$"
    )
    data_dir: str = Field(default="data", description="Data directory")
    temp_dir: str = Field(default="temp", description="Temp directory")
    cache_dir: str = Field(default="cache", description="Cache directory")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v == "UTC":
            return v
        try:
            import zoneinfo

            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(
                f"Invalid timezone: {v}. Must be a valid timezone identifier or 'UTC'"
            )

    @field_validator("data_dir", "temp_dir", "cache_dir")
    @classmethod
    def validate_directory_path(cls, v: str) -> str:
        if not v or v.isspace():
            raise ValueError("Directory path cannot be empty or whitespace")
        if ".." in v or v.startswith("/etc") or v.startswith("/sys"):
            raise ValueError(f"Invalid directory path: {v}")
        return v


class ProcessingConfig(BaseModel):
    """Data processing configuration with enhanced validation and constraints."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    batch_size: int = Field(
        default=1000,
        ge=1,
        le=50000,
        description="Number of records to process in each batch",
    )
    max_workers: int = Field(
        default=4, ge=1, le=32, description="Maximum number of worker threads"
    )
    memory_limit_gb: int = Field(
        default=8, ge=1, le=128, description="Maximum memory usage limit in gigabytes"
    )
    streaming_enabled: bool = Field(
        default=True, description="Enable streaming processing for large datasets"
    )
    parallel_processing: bool = Field(
        default=True, description="Enable parallel processing across multiple workers"
    )
    checkpoint_interval: int = Field(
        default=10000,
        ge=100,
        le=1000000,
        description="Number of records processed before creating a checkpoint",
    )
    error_tolerance: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Acceptable error rate as a decimal"
    )
    download_chunk_size: int = Field(
        default=8192,
        ge=1024,
        le=1048576,
        description="Chunk size in bytes for downloading files",
    )
    download_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Timeout for download operations in seconds",
    )
    download_progress_interval_bytes: int = Field(
        default=1048576,
        ge=1024,
        le=104857600,
        description="Byte interval for reporting download progress",
    )
    file_download_chunk_size: int = Field(
        default=1024, ge=512, le=65536, description="File download chunk size in bytes"
    )

    @field_validator("error_tolerance")
    @classmethod
    def validate_error_tolerance(cls, v: float) -> float:
        if v > 0.1:
            raise ValueError("Error tolerance should not exceed 10% (0.1)")
        return v


class GraphDatabaseConfig(BaseModel):
    """Graph database configuration with enhanced validation and security."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    uri: str = Field(
        default="bolt://localhost:7687", description="Neo4j database connection URI"
    )
    user: str = Field(
        default="neo4j",
        min_length=1,
        description="Database username for authentication",
    )
    password: str = Field(
        default="neo4j",
        min_length=1,
        description="Database password for authentication",
    )
    database: str = Field(
        default="dashboard",
        min_length=1,
        description="Target database name within Neo4j instance",
    )
    max_connection_pool_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of connections in the connection pool",
    )
    connection_timeout: int = Field(
        default=30, ge=5, le=300, description="Connection timeout in seconds"
    )
    max_transaction_retry_time: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Maximum time to retry failed transactions in seconds",
    )

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URI format: {v}")
        if parsed.scheme not in ["bolt", "neo4j", "bolt+s", "neo4j+s"]:
            raise ValueError(f"URI must use bolt:// or neo4j:// scheme: {v}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters long")
        return v

    @field_serializer("password")
    def serialize_password(self, value: str) -> str:
        return "***MASKED***" if value else ""

    @model_validator(mode="before")
    @classmethod
    def load_credentials_from_env(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        env_mappings = {
            "NEO4J_URI": "uri",
            "NEO4J_USER": "user",
            "NEO4J_PASSWORD": "password",
            "NEO4J_DATABASE": "database",
        }
        for env_var, field_name in env_mappings.items():
            if env_value := os.environ.get(env_var):
                values[field_name] = env_value
        return values


class RedisConfig(BaseModel):
    """Redis configuration"""

    url: str = "redis://localhost:6379"
    password: Optional[str] = None
    db: int = 0
    decode_responses: bool = True

    @model_validator(mode="after")
    def load_credentials_from_env(self) -> "RedisConfig":
        if env_url := os.environ.get("REDIS_URL"):
            self.url = env_url
        if env_password := os.environ.get("REDIS_PASSWORD"):
            self.password = env_password
        return self


class LoggingConfig(BaseModel):
    """Logging configuration with enhanced options"""

    level: str = "INFO"
    format: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    files: Dict[str, str] = Field(
        default_factory=lambda: {
            "populate_db": "populate_db.log",
            "dashboard": "dashboard.log",
        }
    )
    rotation: Dict[str, str] = Field(default_factory=dict)
    levels: Dict[str, str] = Field(default_factory=dict)
    handlers: List[str] = Field(default=["console", "file"])
    encoding: str = "utf-8"

    @model_validator(mode="after")
    def override_from_env(self) -> "LoggingConfig":
        if env_level := os.environ.get("LOG_LEVEL"):
            self.level = env_level
        return self


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""

    metrics_enabled: bool = True
    status_file: str = "data/status/system_status.json"
    history_file: str = "data/status/status_history.json"
    api_response_threshold_ms: float = 5000.0
    health_check_interval_seconds: int = 300
    metrics_collection_interval_seconds: int = 60
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    alerts_enabled: bool = False
    alert_channels: List[str] = Field(default_factory=list)


class CachingConfig(BaseModel):
    """Caching configuration"""

    enabled: bool = True
    cache_directory: str = "data/cache"
    agency_list_ttl_days: int = 30
    data_dictionary_ttl_days: int = 30
    query_cache_ttl_hours: int = 24
    max_cache_size_mb: int = 1024


class DirectoriesConfig(BaseModel):
    """Directory configuration"""

    data_root: str = "data"
    raw_data: str = "data/raw"
    processed_data: str = "data/processed"
    downloads: str = "data/downloads"
    cache: str = "data/cache"
    logs: str = "logs"
    temp: str = "temp"
    reports: str = "data/reports"
    backups: str = "data/backups"


class ValidationConfig(BaseModel):
    """Validation configuration"""

    schema_directory: str = "data/reference"
    error_log_directory: str = "logs/validation"
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    validation_timeout_seconds: int = 30


class DevelopmentConfig(BaseModel):
    """Development configuration"""

    debug_mode: bool = False
    sample_data_size: int = 1000
    mock_api_responses: bool = False

    @model_validator(mode="after")
    def override_from_env(self) -> "DevelopmentConfig":
        if env_debug := os.environ.get("DEBUG_MODE"):
            self.debug_mode = env_debug.lower() in ("true", "yes", "1")
        return self


class TestingConfig(BaseModel):
    """Testing configuration"""

    test_data_path: str = "tests/data"
    mock_downloads: bool = True
    skip_external_apis: bool = True


class OutputStyleConfig(BaseModel):
    """Output style configuration for a specific message type"""

    prefix: str = ""
    color: str = "white"
    style: str = "normal"


class OutputConfig(BaseModel):
    """Terminal output configuration"""

    verbosity: str = "info"
    styles: Dict[str, OutputStyleConfig] = Field(default_factory=dict)


class ProcessValidationConfig(BaseModel):
    """Process validation configuration"""

    checkpoint_type: str = "demo_verification"
    checkpoint_operation: str = "enhanced_demo"


# Dashboard-specific configurations
class UIConfig(BaseModel):
    """Dashboard UI configuration"""

    theme: str = Field(default="material", description="Panel theme")
    port: int = Field(default=5007, ge=1024, le=65535, description="Dashboard port")
    host: str = Field(default="localhost", description="Dashboard host")
    auto_reload: bool = Field(default=True, description="Enable auto reload")
    show_on_startup: bool = Field(default=True, description="Show dashboard on startup")
    sizing_mode: str = Field(default="stretch_width", description="Panel sizing mode")


class VisualizationConfig(BaseModel):
    """Visualization configuration"""

    default_plot_width: int = Field(
        default=800, ge=400, le=2000, description="Default plot width"
    )
    default_plot_height: int = Field(
        default=600, ge=300, le=1500, description="Default plot height"
    )
    color_palette: List[str] = Field(
        default_factory=lambda: ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
        description="Default color palette",
    )
    max_data_points: int = Field(
        default=10000, ge=100, le=100000, description="Max data points per plot"
    )
    enable_tooltips: bool = Field(default=True, description="Enable plot tooltips")
    enable_zoom: bool = Field(default=True, description="Enable plot zoom")


class NetworkGraphConfig(BaseModel):
    """Network graph configuration"""

    default_layout: str = Field(
        default="spring", description="Default graph layout algorithm"
    )
    node_size_range: List[int] = Field(
        default_factory=lambda: [10, 50], description="Node size range"
    )
    node_size_metric: str = Field(
        default="degree",
        description="Metric to use for node sizing (degree, complexity, lines_of_code)",
    )
    edge_filter: str = Field(
        default="all",
        description="Edge filter type (all, imports, inherits, calls, uses, contains, depends_on)",
    )
    edge_filter_options_model: Optional[Dict[str, Any]] = Field(
        default=None, description="Edge filter options model configuration"
    )
    show_labels: bool = Field(
        default=True, description="Whether to show node labels by default"
    )
    edge_width_range: List[int] = Field(
        default_factory=lambda: [1, 5], description="Edge width range"
    )
    max_nodes: int = Field(
        default=500, ge=10, le=2000, description="Max nodes to display"
    )
    clustering_enabled: bool = Field(default=True, description="Enable node clustering")


class AnalysisConfig(BaseModel):
    """Code analysis configuration"""

    exclude_dirs: List[str] = Field(
        default_factory=list, description="Directories to exclude from analysis"
    )
    max_query_limit: int = Field(
        default=1000, description="Max number of files/functions/classes to query"
    )
    complexity_threshold: int = Field(
        default=10, description="Complexity threshold for analysis"
    )
    enable_inheritance_analysis: bool = Field(
        default=True, description="Enable inheritance relationship analysis"
    )
    enable_dependency_analysis: bool = Field(
        default=True, description="Enable dependency analysis"
    )
    enable_metrics_calculation: bool = Field(
        default=True, description="Enable code metrics calculation"
    )
    max_file_size_mb: int = Field(
        default=10, ge=1, le=100, description="Maximum file size to analyze (MB)"
    )


class FileAnalysisConfig(BaseModel):
    """File analysis pattern configuration for code population"""

    include_patterns: List[str] = Field(
        default=[
            "*.py",
            "*.js",
            "*.html",
            "*.css",
            "*.md",
            "*.json",
            "*.yml",
            "*.yaml",
        ],
        description="File patterns to include in analysis",
    )
    exclude_patterns: List[str] = Field(
        default=[
            "__pycache__",
            "*.pyc",
            "node_modules",
            ".git",
            ".vscode",
            "*.egg-info",
            "logs",
            "temp",
            "cache",
            "data/processed",
            "data/test",
        ],
        description="File patterns to exclude from analysis",
    )
    default_encoding: str = Field(
        default="utf-8", description="Default text encoding for file reading"
    )
    encoding_fallbacks: List[str] = Field(
        default=["utf-8-sig", "latin1", "cp1252"],
        description="Fallback encodings to try if default fails",
    )
    max_file_size_mb: int = Field(
        default=10, ge=1, le=100, description="Maximum file size to analyze (MB)"
    )
    enable_caching: bool = Field(
        default=True, description="Enable caching of analysis results"
    )
    cache_ttl_hours: int = Field(
        default=24, ge=1, le=168, description="Cache time-to-live in hours"
    )


class ASTAnalysisConfig(BaseModel):
    """AST analysis configuration for Python code parsing"""

    complexity_base: int = Field(
        default=1, ge=1, description="Base complexity value for calculations"
    )
    complexity_increment: int = Field(
        default=1, ge=1, description="Complexity increment per control structure"
    )
    max_function_complexity: int = Field(
        default=50, ge=1, le=200, description="Maximum function complexity threshold"
    )
    max_file_complexity: int = Field(
        default=100, ge=1, le=500, description="Maximum file complexity threshold"
    )
    enable_relationship_extraction: bool = Field(
        default=True, description="Enable extraction of code relationships"
    )
    enable_pydantic_detection: bool = Field(
        default=True, description="Enable Pydantic model detection"
    )
    enable_decorator_analysis: bool = Field(
        default=True, description="Enable decorator analysis"
    )
    error_tolerance: bool = Field(
        default=True, description="Continue analysis on syntax errors"
    )
    skip_syntax_errors: bool = Field(
        default=True, description="Skip files with syntax errors"
    )
    progress_reporting_interval: int = Field(
        default=100, ge=1, description="Report progress every N files"
    )


class PopulationConfig(BaseModel):
    """Database population configuration with enhanced options"""

    default_db_path: str = Field(
        default="code_intelligence.db", description="Default SQLite database file path"
    )
    batch_processing: bool = Field(
        default=True, description="Enable batch processing for large datasets"
    )
    batch_size: int = Field(
        default=1000, ge=1, le=10000, description="Number of records per batch"
    )
    progress_reporting: bool = Field(
        default=True, description="Enable progress reporting during population"
    )
    progress_interval: int = Field(
        default=100, ge=1, description="Report progress every N files"
    )
    error_logging: bool = Field(
        default=True, description="Enable detailed error logging"
    )
    clear_existing_data: bool = Field(
        default=True, description="Clear existing data before population"
    )
    enable_relationship_resolution: bool = Field(
        default=True, description="Enable cross-reference relationship resolution"
    )
    enable_cross_file_analysis: bool = Field(
        default=True, description="Enable analysis across multiple files"
    )
    max_concurrent_files: int = Field(
        default=10, ge=1, le=50, description="Maximum files to process concurrently"
    )


class DashboardSettings(BaseModel):
    """Main dashboard settings class with full feature parity"""

    system: SystemConfig = Field(default_factory=SystemConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    graph_database: GraphDatabaseConfig = Field(default_factory=GraphDatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    caching: CachingConfig = Field(default_factory=CachingConfig)
    directories: DirectoriesConfig = Field(default_factory=DirectoriesConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    process_validation: ProcessValidationConfig = Field(
        default_factory=ProcessValidationConfig
    )

    # Dashboard-specific configs
    ui: UIConfig = Field(default_factory=UIConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    network_graph: NetworkGraphConfig = Field(default_factory=NetworkGraphConfig)

    # File analysis and population configs
    file_analysis: FileAnalysisConfig = Field(default_factory=FileAnalysisConfig)
    ast_analysis: ASTAnalysisConfig = Field(default_factory=ASTAnalysisConfig)
    population: PopulationConfig = Field(default_factory=PopulationConfig)

    # Legacy compatibility fields
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="dashboard.log", description="Log file path")
    db_path: str = Field(
        default="code_intelligence.db", description="Database file path"
    )

    @classmethod
    def from_yaml(cls, path: Path = CONFIG_PATH) -> "DashboardSettings":
        """Load settings from YAML file with environment variable overrides."""
        config_file = Path(path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    def to_yaml(self, output_path: str, exclude_sensitive: bool = True) -> None:
        """Export settings to YAML file for deployment or backup."""
        config_data = self.model_dump()

        if exclude_sensitive:
            if "graph_database" in config_data:
                config_data["graph_database"]["password"] = "********"
            if "redis" in config_data and config_data["redis"].get("password"):
                config_data["redis"]["password"] = "********"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.system.environment.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.system.environment.lower() == "production"

    def data_dir(self) -> Path:
        """Get the configured data directory as a Path object."""
        return Path(self.system.data_dir)

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        directories = [
            self.data_dir(),
            self.data_dir() / "raw",
            self.data_dir() / "processed",
            self.data_dir() / "exports",
            self.data_dir() / "logs",
            self.data_dir() / "cache",
            self.data_dir() / "temp",
            self.data_dir() / "reports",
            self.data_dir() / "backups",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    # Convenience properties for backward compatibility
    @property
    def exclude_dirs(self) -> List[str]:
        return self.analysis.exclude_dirs

    @property
    def max_query_limit(self) -> int:
        return self.analysis.max_query_limit

    @property
    def complexity_threshold(self) -> int:
        return self.analysis.complexity_threshold


# Note: Logging setup is handled in dashboard_logging.py to avoid circular imports
# Settings can be loaded independently for configuration access
