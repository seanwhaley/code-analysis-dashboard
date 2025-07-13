"""
Dashboard Pydantic models for the code intelligence dashboard submodule.

This module contains all Pydantic models used throughout the dashboard for
data validation, serialization, and type safety. All models include comprehensive
field validation and clear documentation.

**Last Updated:** 2025-01-27 15:30:00
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator


class EdgeFilterOptionsModel(BaseModel):
    """
    Model for edge filter options in network graphs.

    Provides validation for relationship types that can be filtered
    in dependency and relationship visualizations.

    Attributes:
        options: List of available edge filter options for graph relationships.
    """

    options: List[str] = Field(
        default_factory=lambda: [
            "all",
            "imports",
            "inherits",
            "calls",
            "uses",
            "contains",
            "depends_on",
        ],
        description="Available edge filter options for graph relationships",
    )

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        """
        Validate that edge filter options are not empty and contain valid types.

        Args:
            v: List of edge filter options.
        Returns:
            List of validated edge filter options.
        Raises:
            ValueError: If options are empty or contain invalid types.
        """
        if not v:
            raise ValueError("Edge filter options cannot be empty")
        valid_options = {
            "all",
            "imports",
            "inherits",
            "calls",
            "uses",
            "contains",
            "depends_on",
        }
        for option in v:
            if option not in valid_options:
                raise ValueError(f"Invalid edge filter option: {option}")
        return v

    def __str__(self) -> str:
        return f"EdgeFilterOptions({len(self.options)} options)"

    def __repr__(self) -> str:
        return f"EdgeFilterOptionsModel(options={self.options})"


class HoverTooltipsModel(BaseModel):
    """
    Model for hover tooltip configuration in visualizations.

    Defines the information displayed when hovering over nodes
    in network graphs and other interactive visualizations.

    Attributes:
        tooltips: List of (label, field) tuples for hover tooltips.
    """

    tooltips: List[Tuple[str, str]] = Field(
        default_factory=lambda: [
            ("File", "@name"),
            ("Path", "@path"),
            ("Domain", "@domain"),
            ("Complexity", "@complexity"),
            ("Lines of Code", "@lines_of_code"),
            ("Classes", "@classes_count"),
            ("Functions", "@functions_count"),
            ("Degree", "@degree"),
            ("Degree Centrality", "@degree_centrality{0.000}"),
            ("Betweenness Centrality", "@betweenness_centrality{0.000}"),
        ],
        description="List of (label, field) tuples for hover tooltips",
    )

    @field_validator("tooltips")
    @classmethod
    def validate_tooltips(cls, v: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        Validate tooltip configuration.

        Args:
            v: List of (label, field) tuples.
        Returns:
            List of validated tooltips.
        Raises:
            ValueError: If tooltips are empty or invalid.
        """
        if not v:
            raise ValueError("Tooltips cannot be empty")
        for label, field in v:
            if not label or not label.strip():
                raise ValueError("Tooltip label cannot be empty")
            if not field or not field.strip():
                raise ValueError("Tooltip field cannot be empty")
            if not field.startswith("@"):
                raise ValueError(f"Tooltip field must start with @: {field}")
        return v

    def get_tooltip_labels(self) -> List[str]:
        """
        Get list of tooltip labels.
        Returns:
            List of tooltip labels.
        """
        return [label for label, _ in self.tooltips]

    def get_tooltip_fields(self) -> List[str]:
        """
        Get list of tooltip fields.
        Returns:
            List of tooltip fields.
        """
        return [field for _, field in self.tooltips]

    def __str__(self) -> str:
        return f"HoverTooltips({len(self.tooltips)} items)"


class NodeDataModel(BaseModel):
    """
    Model for node data in network graph visualizations.

    Represents aggregated node information for Bokeh/plotting libraries
    where each field is a list containing values for all nodes.

    Attributes:
        id: List of node IDs
        x, y: Coordinates for node positions
        name: Node names
        path: Full paths to files
        domain: Domain classifications
        complexity: Complexity scores
        lines_of_code: Lines of code counts
        classes_count: Number of classes
        functions_count: Number of functions
        file_type: File type classifications
        degree: Node degrees
        degree_centrality: Degree centrality scores
        betweenness_centrality: Betweenness centrality scores
        closeness_centrality: Closeness centrality scores
        size: Visual sizes for node rendering
        color: Colors for node rendering
    """

    id: List[int] = Field(default_factory=list, description="List of node IDs")
    x: List[float] = Field(
        default_factory=list, description="X coordinates for node positions"
    )
    y: List[float] = Field(
        default_factory=list, description="Y coordinates for node positions"
    )
    name: List[str] = Field(
        default_factory=list, description="Node names (typically file names)"
    )
    path: List[str] = Field(default_factory=list, description="Full paths to files")
    domain: List[str] = Field(
        default_factory=list, description="Domain classifications for files"
    )
    complexity: List[float] = Field(
        default_factory=list, description="Complexity scores for files"
    )
    lines_of_code: List[int] = Field(
        default_factory=list, description="Lines of code counts"
    )
    classes_count: List[int] = Field(
        default_factory=list, description="Number of classes in each file"
    )
    functions_count: List[int] = Field(
        default_factory=list, description="Number of functions in each file"
    )
    file_type: List[str] = Field(
        default_factory=list, description="File type classifications"
    )
    degree: List[int] = Field(
        default_factory=list, description="Node degrees in the graph"
    )
    degree_centrality: List[float] = Field(
        default_factory=list, description="Degree centrality scores"
    )
    betweenness_centrality: List[float] = Field(
        default_factory=list, description="Betweenness centrality scores"
    )
    closeness_centrality: List[float] = Field(
        default_factory=list, description="Closeness centrality scores"
    )
    size: List[int] = Field(
        default_factory=list, description="Visual sizes for node rendering"
    )
    color: List[str] = Field(
        default_factory=list, description="Colors for node rendering"
    )

    @model_validator(mode="after")
    def validate_consistent_lengths(self) -> "NodeDataModel":
        """
        Ensure all lists have the same length.

        Returns:
            NodeDataModel instance if valid.
        Raises:
            ValueError: If any field lists have inconsistent lengths.
        """
        lengths = [
            len(self.id),
            len(self.x),
            len(self.y),
            len(self.name),
            len(self.path),
            len(self.domain),
            len(self.complexity),
            len(self.lines_of_code),
            len(self.classes_count),
            len(self.functions_count),
            len(self.file_type),
            len(self.degree),
            len(self.degree_centrality),
            len(self.betweenness_centrality),
            len(self.closeness_centrality),
            len(self.size),
            len(self.color),
        ]
        if len(set(lengths)) > 1:
            field_names = [
                "id",
                "x",
                "y",
                "name",
                "path",
                "domain",
                "complexity",
                "lines_of_code",
                "classes_count",
                "functions_count",
                "file_type",
                "degree",
                "degree_centrality",
                "betweenness_centrality",
                "closeness_centrality",
                "size",
                "color",
            ]
            raise ValueError(
                f"All node data lists must have the same length. "
                f"Found lengths: {dict(zip(field_names, lengths))}"
            )
        return self

    def get_node_count(self) -> int:
        """
        Get the number of nodes represented by this data.
        Returns:
            Number of nodes.
        """
        return len(self.id)

    def is_empty(self) -> bool:
        """
        Check if this node data is empty.
        Returns:
            True if empty, False otherwise.
        """
        return len(self.id) == 0


# --- EdgeDataModel ---
class EdgeDataModel(BaseModel):
    xs: List[List[float]] = Field(default_factory=list)
    ys: List[List[float]] = Field(default_factory=list)
    source: List[int] = Field(default_factory=list)
    target: List[int] = Field(default_factory=list)
    relationship_type: List[str] = Field(default_factory=list)
    alpha: List[float] = Field(default_factory=list)


# --- DomainColorsModel ---
class DomainColorsModel(BaseModel):
    presentation: str = "#FF6B6B"
    application: str = "#4ECDC4"
    domain: str = "#45B7D1"
    infrastructure: str = "#96CEB4"
    services: str = "#FFEAA7"
    models: str = "#DDA0DD"
    utils: str = "#98D8C8"
    tests: str = "#F7DC6F"
    config: str = "#BB8FCE"
    docs: str = "#85C1E9"
    unknown: str = "#BDC3C7"

    def as_dict(self) -> Dict[str, str]:
        return self.model_dump()


# --- RelationshipTypeAlphaModel ---
class RelationshipTypeAlphaModel(BaseModel):
    imports: float = 0.8
    inherits: float = 0.9
    calls: float = 0.6
    uses: float = 0.5
    contains: float = 0.7
    depends_on: float = 0.6

    def as_dict(self) -> Dict[str, float]:
        return self.model_dump()


from typing import Optional

from pydantic import BaseModel, Field


class NodeModel(BaseModel):
    """
    Pydantic model for a code file node in the network graph.
    """

    id: int
    name: str
    path: str
    domain: str
    complexity: float
    lines_of_code: int
    classes_count: int
    functions_count: int
    file_type: str


class EdgeModel(BaseModel):
    """
    Pydantic model for an edge between two file nodes.
    """

    source: int
    target: int
    relationship_type: str
    alpha: float


class FileFilterModel(BaseModel):
    """
    Pydantic model for file filtering parameters.

    Attributes:
        domain: Optional domain filter
        file_type: Optional file type filter
        complexity_level: Optional complexity filter
        min_lines: Minimum lines of code
        max_lines: Maximum lines of code
        search_term: Search term for filtering
    """

    domain: Optional[str] = Field(default=None, description="Domain filter")
    file_type: Optional[str] = Field(default=None, description="File type filter")
    complexity_level: Optional[str] = Field(
        default=None, description="Complexity filter"
    )
    min_lines: Optional[int] = Field(default=None, description="Minimum lines of code")
    max_lines: Optional[int] = Field(default=None, description="Maximum lines of code")
    search_term: Optional[str] = Field(default="", description="Search term")


class SystemStatsModel(BaseModel):
    """
    Pydantic model for system statistics.

    Attributes:
        total_files: Total number of files
        total_classes: Total number of classes
        total_functions: Total number of functions
        total_lines: Total lines of code
        domain_stats: Stats per domain
    """

    total_files: int = Field(default=0, description="Total number of files")
    total_classes: int = Field(default=0, description="Total number of classes")
    total_functions: int = Field(default=0, description="Total number of functions")
    total_lines: int = Field(default=0, description="Total lines of code")
    domain_stats: Dict[str, int] = Field(
        default_factory=dict, description="Stats per domain"
    )


class SearchResultsModel(BaseModel):
    """
    Pydantic model for search results.

    Attributes:
        files: List of file search results
        classes: List of class search results
        functions: List of function search results
        total_count: Total number of results
    """

    files: List[Dict[str, Any]] = Field(
        default_factory=list, description="File search results"
    )
    classes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Class search results"
    )
    functions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Function search results"
    )
    total_count: int = Field(default=0, description="Total number of results")


class ClassNodeModel(BaseModel):
    """
    Pydantic model for class node data in diagrams.

    Attributes:
        id: Unique class node ID
        name: Class name
        file_id: File ID
        file_path: Path to file
        base_classes: List of base classes
        is_pydantic_model: Is this a Pydantic model?
        methods: List of methods
        method_count: Number of methods
        complexity: Cyclomatic complexity
        is_abstract: Is this an abstract class?
        docstring: Class docstring
        x, y: Diagram coordinates
        width, height: Node dimensions
        color: Node color
    """

    id: int = Field(..., description="Unique class node ID")
    name: str = Field(..., description="Class name")
    file_id: int = Field(..., description="File ID")
    file_path: str = Field(..., description="Path to file")
    base_classes: List[str] = Field(default_factory=list, description="Base classes")
    is_pydantic_model: bool = Field(..., description="Is Pydantic model")
    methods: List[Any] = Field(default_factory=list, description="Methods")
    method_count: int = Field(..., description="Number of methods")
    complexity: int = Field(..., description="Cyclomatic complexity")
    is_abstract: bool = Field(..., description="Is abstract class")
    docstring: str = Field(default="", description="Class docstring")
    x: float = Field(default=0.0, description="Diagram X coordinate")
    y: float = Field(default=0.0, description="Diagram Y coordinate")
    width: int = Field(default=80, description="Node width")
    height: int = Field(default=40, description="Node height")
    color: str = Field(default="#45B7D1", description="Node color")

    @field_validator("base_classes", mode="before")
    @classmethod
    def default_base_classes(cls, v: Any) -> List[str]:
        return v or []


class DatabaseQueryResult(BaseModel):
    """
    Standard result wrapper for database queries.

    Attributes:
        data: Query result data
        total_count: Total number of results
        success: Query success flag
        error_message: Error message if any
    """

    data: List[Any] = Field(default_factory=list, description="Query result data")
    total_count: int = Field(default=0, description="Total number of results")
    success: bool = Field(default=True, description="Query success flag")
    error_message: Optional[str] = Field(default=None, description="Error message")


class UIComponentState(BaseModel):
    """
    State model for UI components.

    Attributes:
        is_initialized: Is component initialized?
        has_data: Does component have data?
        error_message: Error message if any
        last_updated: Last updated timestamp
    """

    is_initialized: bool = Field(default=False, description="Is initialized?")
    has_data: bool = Field(default=False, description="Has data?")
    error_message: Optional[str] = Field(default=None, description="Error message")
    last_updated: Optional[str] = Field(
        default=None, description="Last updated timestamp"
    )


class CouplingMetricsModel(BaseModel):
    """
    Pydantic model for coupling metrics of a file.
    """

    file_id: int
    name: str
    path: str
    domain: str
    afferent_coupling: int
    efferent_coupling: int
    instability: float
    abstractness: float
    distance_from_main: float
    total_coupling: int


class CircularDependencyModel(BaseModel):
    """
    Pydantic model for a circular dependency cycle.
    """

    nodes: List[int]
    cycle_path: List[Tuple[int, int]]
    file_names: List[str]
    file_paths: List[str]
    size: int


# --- GraphStatisticsManager (Utility Class) ---
class GraphStatisticsManager(object):
    """
    Utility class for rendering graph statistics HTML using Jinja2 templates.

    This class handles the generation of HTML for graph statistics displays
    in the dashboard's network visualization components.
    """

    @staticmethod
    def render_html_sync(
        num_nodes: int,
        num_edges: int,
        density: float,
        top_nodes_info: List[Dict[str, Any]],
        template_path: str,
    ) -> str:
        """
        Render graph statistics as HTML using a Jinja2 template (synchronous version).

        Args:
            num_nodes: Total number of nodes in the graph
            num_edges: Total number of edges in the graph
            density: Graph density (0.0 to 1.0)
            top_nodes_info: List of dicts with info about top nodes
            template_path: Path to the Jinja2 template file

        Returns:
            Rendered HTML string
        """
        try:
            from pathlib import Path

            from jinja2 import Template

            template_content = Path(template_path).read_text(encoding="utf-8")
            template = Template(template_content)
            html_content = template.render(
                num_nodes=num_nodes,
                num_edges=num_edges,
                density=density,
                top_nodes_info=top_nodes_info,
            )
            return html_content
        except Exception as e:
            return (
                f'<div class="graph-statistics">'
                f"<h3>Graph Statistics</h3>"
                f"<p><strong>Nodes:</strong> {num_nodes}</p>"
                f"<p><strong>Edges:</strong> {num_edges}</p>"
                f"<p><strong>Density:</strong> {density:.3f}</p>"
                f"<p><em>Template error: {str(e)}</em></p>"
                f"</div>"
            )

    @staticmethod
    async def render_html(
        num_nodes: int,
        num_edges: int,
        density: float,
        top_nodes_info: List[Dict[str, Any]],
        template_path: str,
    ) -> str:
        """
        Render graph statistics as HTML using a Jinja2 template.

        Args:
            num_nodes: Total number of nodes in the graph
            num_edges: Total number of edges in the graph
            density: Graph density (0.0 to 1.0)
            top_nodes_info: List of dicts with info about top nodes
            template_path: Path to the Jinja2 template file

        Returns:
            Rendered HTML string
        """
        try:
            import aiofiles
            from jinja2 import Template

            async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
                template_content = await f.read()
            template = Template(template_content)
            html_content = template.render(
                num_nodes=num_nodes,
                num_edges=num_edges,
                density=density,
                top_nodes_info=top_nodes_info,
            )
            return html_content
        except Exception as e:
            return (
                f'<div class="graph-statistics">'
                f"<h3>Graph Statistics</h3>"
                f"<p><strong>Nodes:</strong> {num_nodes}</p>"
                f"<p><strong>Edges:</strong> {num_edges}</p>"
                f"<p><strong>Density:</strong> {density:.3f}</p>"
                f"<p><em>Template error: {str(e)}</em></p>"
                f"</div>"
            )
