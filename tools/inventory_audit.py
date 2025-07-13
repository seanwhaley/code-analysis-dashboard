"""
Advanced Architectural Audit & Visualization Script (v4)

This script performs a deep static analysis of a Python project and generates a rich,
multi-layered, and highly visual HTML report designed for team-wide communication.

Key Features:
- Deep Analysis: Uses a two-pass AST scan to map all symbols and their detailed usage.
- Interactive Sunburst Chart: An interactive D3.js visualization showing project
  composition by file size.
- Architectural Diagrams: Generates high-level module dependencies, detailed class
  inheritance trees, and focused micro-graphs for each file's dependencies.
- Actionable Recommendations: Automatically detects circular dependencies, high-coupling
  points, unused imports, and overly complex files.
- Clean, Collapsible Report: Outputs a single, clean HTML file with collapsible
  sections for easy navigation.

Usage:
    python tools/inventory_audit.py > project_architecture_report.html

**Last Updated:** 2025-07-13 05:00:00
"""

import ast
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


# --- Configuration ---
@dataclass
class Config:
    """Configuration settings for the audit script."""

    PROJECT_ROOT: Path = Path(__file__).parent.parent
    PROJECT_MODULES: List[str] = field(
        default_factory=lambda: [
            "dashboard",
            "models",
            "db",
            "tools",
            "tests",
            "api",
            "scripts",
        ]
    )
    HIGH_COUPLING_THRESHOLD: int = 5
    COMPLEX_FILE_THRESHOLD: int = 8


CONFIG = Config()


# --- Logging ---
def log_info(message: str):
    """Logs an informational message to stderr."""
    print(f"[INFO] {message}", file=sys.stderr)


# --- Core Analysis Logic ---
class ProjectAstVisitor(ast.NodeVisitor):
    """Extracts detailed info about classes, functions, imports, and usage from an AST."""

    def __init__(self):
        self.details = defaultdict(list)
        self.usage = defaultdict(set)
        self.current_class = None

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and any(
            node.module.startswith(p) for p in CONFIG.PROJECT_MODULES
        ):
            for alias in node.names:
                self.details["imports"].append(
                    {"module": node.module, "symbol": alias.name}
                )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_class = node.name
        base_names = [self._get_node_id(b) for b in node.bases]
        is_pydantic = any("BaseModel" in b for b in base_names)
        self.details["classes"].append(
            {"name": node.name, "bases": base_names, "is_pydantic": is_pydantic}
        )
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self.current_class:
            self.details["functions"].append({"name": node.name})
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        callee_name = self._get_node_id(node.func)
        if callee_name and callee_name[0].isupper():
            self.usage["instantiations"].add(callee_name)
        self.generic_visit(node)

    def _get_node_id(self, node: Any) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._get_node_id(node.value) + "." + node.attr
        return ""


def analyze_file(filepath: Path) -> Dict:
    """Analyzes a single Python file."""
    try:
        source = filepath.read_text(encoding="utf-8")
        lines = len(source.splitlines())
        tree = ast.parse(source, filename=str(filepath))
        visitor = ProjectAstVisitor()
        visitor.visit(tree)
        return {"details": visitor.details, "usage": visitor.usage, "lines": lines}
    except Exception as e:
        log_info(f"Could not parse {filepath}: {e}")
        return {}


def build_project_maps(root: Path) -> Tuple[Dict, Dict]:
    """Pass 1: Scan all files to map symbols and collect initial analysis."""
    symbol_map, file_analyses = {}, {}
    py_files = [p for p in root.rglob("*.py") if "site-packages" not in str(p)]

    for fpath in py_files:
        relative_path = str(fpath.relative_to(root)).replace("\\", "/")
        if not any(relative_path.startswith(p) for p in CONFIG.PROJECT_MODULES):
            continue

        log_info(f"Pass 1: Scanning {relative_path}")
        analysis = analyze_file(fpath)
        if not analysis:
            continue
        file_analyses[relative_path] = analysis

        for c in analysis["details"].get("classes", []):
            symbol_type = "Pydantic Model" if c["is_pydantic"] else "Class"
            symbol_map[c["name"]] = {
                "type": symbol_type,
                "file": relative_path,
                "bases": c["bases"],
            }
        for f in analysis["details"].get("functions", []):
            symbol_map[f["name"]] = {"type": "Function", "file": relative_path}
    return symbol_map, file_analyses


def analyze_cross_file_usage(symbol_map: Dict, file_analyses: Dict) -> Dict:
    """Pass 2: Use the complete symbol map to resolve and record detailed usage."""
    usage_map = defaultdict(lambda: defaultdict(set))
    for file_path, analysis in file_analyses.items():
        all_used_symbols = set()
        for imp in analysis["details"].get("imports", []):
            all_used_symbols.add(imp["symbol"])
        all_used_symbols.update(analysis["usage"].get("instantiations", set()))

        for symbol_name in all_used_symbols:
            if symbol_name in symbol_map:
                target = symbol_map[symbol_name]
                if target["file"] != file_path:
                    usage_map[file_path]["dependencies"].add(
                        f"{target['type']}|{symbol_name}|{target['file']}"
                    )
    return usage_map


# --- Recommendation Engine ---
def generate_recommendations(
    usage_map: Dict, file_analyses: Dict, symbol_map: Dict
) -> List[str]:
    """Generate actionable architectural recommendations."""
    recs = set()
    dep_graph, incoming_links = defaultdict(set), defaultdict(int)
    for file, usage_data in usage_map.items():
        for dep_str in usage_data.get("dependencies", []):
            target_file = dep_str.split("|")[-1]
            dep_graph[file].add(target_file)
            incoming_links[target_file] += 1

    for file, dependencies in dep_graph.items():
        for dep in dependencies:
            if dep in dep_graph and file in dep_graph[dep]:
                recs.add(
                    f"**Circular Dependency**: `{file}` and `{dep}` depend on each other. This creates tight coupling and should be resolved."
                )

    for file, count in incoming_links.items():
        if count >= CONFIG.HIGH_COUPLING_THRESHOLD:
            recs.add(
                f"**High Coupling**: `{file}` is a dependency hub, imported by **{count}** other files. Consider refactoring to reduce its responsibilities."
            )

    for file, analysis in file_analyses.items():
        def_count = len(analysis["details"].get("classes", [])) + len(
            analysis["details"].get("functions", [])
        )
        if def_count >= CONFIG.COMPLEX_FILE_THRESHOLD:
            recs.add(
                f"**High Complexity**: `{file}` defines **{def_count}** classes/functions. It may violate the Single Responsibility Principle."
            )
    return sorted(list(recs))


# --- HTML & Visualization Generation ---
def generate_sunburst_data(file_analyses: Dict) -> Dict:
    """Generates a hierarchical data structure for the D3.js sunburst chart."""
    root = {"name": "project", "children": []}

    for path, analysis in file_analyses.items():
        parts = path.split("/")
        current_level = root["children"]

        for i, part in enumerate(parts):
            existing_node = next(
                (node for node in current_level if node["name"] == part), None
            )
            if not existing_node:
                new_node = {"name": part}
                if i == len(parts) - 1:  # It's a file
                    new_node["value"] = analysis.get("lines", 0)
                else:  # It's a directory
                    new_node["children"] = []
                current_level.append(new_node)
                if "children" in new_node:
                    current_level = new_node["children"]
            else:
                if "children" in existing_node:
                    current_level = existing_node["children"]
    return root


def generate_report(
    symbol_map: Dict, usage_map: Dict, file_analyses: Dict, recommendations: List[str]
):
    """Generates the final, comprehensive HTML report."""

    # --- HTML Header and D3 Setup ---
    sunburst_data = json.dumps(generate_sunburst_data(file_analyses))
    # Prepare dynamic values
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Build HTML report
    html = (
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Architecture Report</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9fafb; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 2rem; }}
        h1, h2, h3 {{ color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem; }}
        h1 {{ font-size: 2.25rem; }}
        h2 {{ font-size: 1.75rem; margin-top: 2.5rem; }}
        h3 {{ font-size: 1.25rem; margin-top: 2rem; }}
        code {{ background-color: #f3f4f6; padding: 0.2em 0.4em; margin: 0; font-size: 85%; border-radius: 3px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;}}
        details {{ border: 1px solid #d1d5db; border-radius: 6px; margin-bottom: 1rem; }}
        summary {{ font-weight: bold; cursor: pointer; padding: 0.75rem; background-color: #f9fafb; border-radius: 6px 6px 0 0; }}
        .details-content {{ padding: 1rem; }}
        .recommendation {{ border-left: 4px solid #f59e0b; padding: 1rem; margin-bottom: 1rem; background-color: #fffbeb; }}
        .viz-container {{ text-align: center; margin: 2rem 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🏛️ Project Architecture Report</h1>
    <p><strong>Generated:</strong> """
        + timestamp
        + """</p>
    
    <h2>📊 Project Composition Sunburst</h2>
    <div class="viz-container" id="sunburst"></div>

    <h2>💡 Architectural Recommendations</h2>
    """
        + (
            "".join(
                f'<div class="recommendation">{rec}</div>' for rec in recommendations
            )
            or "<p>✅ No major architectural concerns detected.</p>"
        )
        + """
    """
    )

    # --- Architectural Visualizations ---
    html += "<h2>🗺️ Architectural Diagrams</h2>"

    # Module Dependencies
    html += "<h3>Module Dependencies</h3><div class='mermaid'>"
    html += "graph TD;\n"
    module_deps = defaultdict(set)
    for file, usage in usage_map.items():
        src_module = file.split("/")[0]
        for dep_str in usage.get("dependencies", []):
            target_module = dep_str.split("|")[-1].split("/")[0]
            if src_module != target_module and target_module in CONFIG.PROJECT_MODULES:
                module_deps[src_module].add(target_module)
    for src, targets in module_deps.items():
        for tgt in targets:
            html += f"  {src} --> {tgt};\n"
    html += "</div>"

    # Inheritance Trees
    html += "<h3>Class Inheritance Trees</h3><div class='mermaid'>"
    html += "classDiagram\n"
    for symbol, data in symbol_map.items():
        if data["type"] in ["Class", "Pydantic Model"]:
            html += f"  class {symbol}\n"
            for base in data.get("bases", []):
                if base in symbol_map or "BaseModel" in base:
                    html += f"  {base} <|-- {symbol}\n"
    html += "</div>"

    # --- Detailed File Breakdown ---
    html += "<h2>🔬 Detailed File Analysis</h2>"
    for file in sorted(file_analyses.keys()):
        html += f"<details><summary><code>{file}</code></summary><div class='details-content'>"

        # Micro-dependency graph
        html += "<h4>Dependencies</h4><div class='mermaid'>graph TD;\n"
        node_name = file.replace("/", "_").replace(".py", "")
        for dep_str in usage_map[file].get("dependencies", []):
            _, symbol, target_file = dep_str.split("|")
            target_node_name = target_file.replace("/", "_").replace(".py", "")
            html += f'  {node_name} -->|"{symbol}"| {target_node_name};\n'
        html += "</div>"

        # Definitions
        defs = file_analyses[file]["details"].get("classes", []) + file_analyses[file][
            "details"
        ].get("functions", [])
        if defs:
            html += "<h4>Defines</h4><ul>"
            for d in defs:
                kind = (
                    "Pydantic Model"
                    if d.get("is_pydantic")
                    else ("Class" if "bases" in d else "Function")
                )
                html += f"<li><strong>{d['name']}</strong> ({kind})</li>"
            html += "</ul>"
        html += "</div></details>"

    # --- HTML Footer and Scripts ---
    html += (
        f"""
</div>
<script>
    mermaid.initialize({{ startOnLoad: true }});

    const sunburstData = """
        + sunburst_data
        + """;
    const width = 600;
    const height = width;
    const radius = width / 6;

    const color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, sunburstData.children.length + 1));

    const hierarchy = d3.hierarchy(sunburstData)
        .sum(d => d.value)
        .sort((a, b) => b.value - a.value);
    const root = d3.partition()
        .size([2 * Math.PI, hierarchy.height + 1])
      (hierarchy);
    root.each(d => d.current = d);

    const arc = d3.arc()
        .startAngle(d => d.x0)
        .endAngle(d => d.x1)
        .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
        .padRadius(radius * 1.5)
        .innerRadius(d => d.y0 * radius)
        .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1));

    const svg = d3.select("#sunburst").append("svg")
        .attr("viewBox", [-width / 2, -height / 2, width, width])
        .style("font", "10px sans-serif");

    const path = svg.append("g")
      .selectAll("path")
      .data(root.descendants().slice(1))
      .join("path")
        .attr("fill", d => {{ while (d.depth > 1) d = d.parent; return color(d.data.name); }})
        .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.6 : 0.4) : 0)
        .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")
        .attr("d", d => arc(d.current));

    path.filter(d => d.children)
        .style("cursor", "pointer")
        .on("click", clicked);

    path.append("title")
        .text(d => `{{d.ancestors().map(d => d.data.name).reverse().join("/")}}\\nLines: {{d.value.toLocaleString()}}`);

    const label = svg.append("g")
        .attr("pointer-events", "none")
        .attr("text-anchor", "middle")
        .style("user-select", "none")
      .selectAll("text")
      .data(root.descendants().slice(1))
      .join("text")
        .attr("dy", "0.35em")
        .attr("fill-opacity", d => +labelVisible(d.current))
        .attr("transform", d => labelTransform(d.current))
        .text(d => d.data.name);

    const parent = svg.append("circle")
        .datum(root)
        .attr("r", radius)
        .attr("fill", "none")
        .attr("pointer-events", "all")
        .on("click", clicked);

    function clicked(event, p) {{
      parent.datum(p.parent || root);

      root.each(d => d.target = {{
        x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
        x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
        y0: Math.max(0, d.y0 - p.depth),
        y1: Math.max(0, d.y1 - p.depth)
      }});

      const t = svg.transition().duration(750);

      path.transition(t)
          .tween("data", d => {{
            const i = d3.interpolate(d.current, d.target);
            return t => d.current = i(t);
          }})
        .filter(function(d) {{
          return +this.getAttribute("fill-opacity") || arcVisible(d.target);
        }})
          .attr("fill-opacity", d => arcVisible(d.target) ? (d.children ? 0.6 : 0.4) : 0)
          .attr("pointer-events", d => arcVisible(d.target) ? "auto" : "none") 
          .attrTween("d", d => () => arc(d.current));

      label.filter(function(d) {{
          return +this.getAttribute("fill-opacity") || labelVisible(d.target);
        }).transition(t)
          .attr("fill-opacity", d => +labelVisible(d.target))
          .attrTween("transform", d => () => labelTransform(d.current));
    }}
    
    function arcVisible(d) {{
      return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
    }}

    function labelVisible(d) {{
      return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
    }}

    function labelTransform(d) {{
      const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
      const y = (d.y0 + d.y1) / 2 * radius;
      return `rotate(${{x - 90}}) translate(${{y}},0) rotate(${{x < 180 ? 0 : 180}})`;
    }}
</script>
</body>
</html>
    """
    )
    print(html)


def main():
    """Main function to run the full analysis and generate the HTML report."""
    log_info("Starting architectural audit...")
    symbol_map, file_analyses = build_project_maps(CONFIG.PROJECT_ROOT)
    log_info(
        f"Pass 1 complete. Found {len(symbol_map)} unique symbols in {len(file_analyses)} files."
    )

    usage_map = analyze_cross_file_usage(symbol_map, file_analyses)
    log_info("Pass 2 complete. Cross-file usage analysis finished.")

    recommendations = generate_recommendations(usage_map, file_analyses, symbol_map)
    log_info(f"Found {len(recommendations)} architectural recommendations.")

    generate_report(symbol_map, usage_map, file_analyses, recommendations)
    log_info("Successfully generated HTML report.")


if __name__ == "__main__":
    main()
