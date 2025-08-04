# Visualization System Specification

## Overview

The Visualization System provides comprehensive visual representation and analysis of dependency graphs. It generates interactive and static visualizations to help users understand code relationships, identify architectural patterns, and spot potential issues like circular dependencies.

### Dependencies and Requirements

The visualization system requires several external dependencies:

**Required Dependencies:**
- `networkx` - For graph data structures and algorithms
- `pathlib` - For file path handling (built-in)

**Optional Dependencies:**
- `graphviz` - For static image generation (requires system installation)
- `vis-network` - Loaded via CDN for interactive visualizations

**System Requirements:**
- `graphviz` system package must be installed for static image generation
- Modern web browser with JavaScript enabled for interactive visualizations
- Internet connection for CDN-based libraries (or local bundling)

## Core Capabilities

1. **Static Graph Visualization**: Generate high-quality static images of dependency graphs
2. **Interactive HTML Visualization**: Create interactive web-based dependency explorers
3. **Dependency Analysis Reports**: Generate comprehensive textual reports with visual elements
4. **Architectural Diagrams**: Create higher-level architectural views
5. **Circular Dependency Visualization**: Highlight and explain circular dependencies

## Architecture

### 1. Visualization System Components

```python
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from pathlib import Path

class VisualizationType(Enum):
    """Types of visualizations supported."""
    STATIC_IMAGE = "static_image"
    INTERACTIVE_HTML = "interactive_html"
    ANALYSIS_REPORT = "analysis_report"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    CIRCULAR_DEPENDENCY_FOCUS = "circular_dependency_focus"

class VisualizationSystem:
    """
    Main visualization system for dependency graphs.
    """

    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.renderers = {
            VisualizationType.STATIC_IMAGE: StaticImageRenderer(config),
            VisualizationType.INTERACTIVE_HTML: InteractiveHTMLRenderer(config),
            VisualizationType.ANALYSIS_REPORT: AnalysisReportRenderer(config),
            VisualizationType.ARCHITECTURE_DIAGRAM: ArchitectureRenderer(config),
            VisualizationType.CIRCULAR_DEPENDENCY_FOCUS: CircularDependencyRenderer(config)
        }

    def visualize_dependency_graph(self, dependency_graph: DependencyGraph,
                                 visualization_type: VisualizationType,
                                 output_path: str) -> VisualizationResult:
        """Generate visualization of the dependency graph."""

    def create_comprehensive_report(self, dependency_graph: DependencyGraph,
                                  output_dir: str) -> str:
        """Create a comprehensive report with multiple visualization types."""

    def analyze_graph_metrics(self, dependency_graph: DependencyGraph) -> GraphMetrics:
        """Analyze and compute various graph metrics."""

    def generate_architecture_summary(self, dependency_graph: DependencyGraph) -> str:
        """Generate high-level architectural summary."""

@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""

    # Output formats and quality
    image_format: str = "png"  # png, svg, pdf
    image_dpi: int = 300
    image_size: Tuple[int, int] = (1200, 800)

    # Graph layout and styling
    layout_algorithm: str = "hierarchical"  # hierarchical, force_directed, circular
    node_size_factor: float = 1.0
    edge_thickness_factor: float = 1.0
    font_size: int = 10

    # Color schemes
    color_scheme: str = "default"  # default, colorblind, high_contrast
    highlight_cycles: bool = True
    highlight_leaves: bool = True

    # Content filtering
    max_nodes_display: int = 100
    min_node_importance: float = 0.1
    hide_external_dependencies: bool = True
    group_packages: bool = True

    # Interactive features
    enable_tooltips: bool = True
    enable_search: bool = True
    enable_filtering: bool = True

    # Library source configuration
    vis_network_source: str = "cdn"  # "cdn", "local", "bundled"
    local_assets_path: Optional[str] = None

    # Report generation
    include_metrics: bool = True
    include_recommendations: bool = True
    include_code_examples: bool = False

@dataclass
class VisualizationResult:
    """Result of a visualization generation."""

    success: bool
    output_path: str
    visualization_type: VisualizationType
    metrics: Optional[GraphMetrics]
    errors: List[str]
    warnings: List[str]
    generation_time: float

@dataclass
class GraphMetrics:
    """Computed metrics for a dependency graph."""

    # Basic metrics
    total_nodes: int
    total_edges: int
    average_degree: float
    max_depth: int

    # Complexity metrics
    cyclomatic_complexity: float
    coupling_metrics: Dict[str, float]
    cohesion_metrics: Dict[str, float]

    # Structural metrics
    strongly_connected_components: int
    longest_path: int
    leaf_nodes: List[str]
    root_nodes: List[str]

    # Circular dependency analysis
    circular_dependencies: List[List[str]]
    cycle_complexity: Dict[str, int]
```

### 2. Static Image Renderer

```python
class StaticImageRenderer:
    """Renders dependency graphs as static images using Graphviz."""

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def render(self, dependency_graph: DependencyGraph, output_path: str) -> VisualizationResult:
        """Render dependency graph as static image."""

        try:
            # Create Graphviz graph
            dot_graph = self._create_graphviz_graph(dependency_graph)

            # Apply styling
            self._apply_styling(dot_graph, dependency_graph)

            # Generate image
            output_file = self._render_image(dot_graph, output_path)

            return VisualizationResult(
                success=True,
                output_path=output_file,
                visualization_type=VisualizationType.STATIC_IMAGE,
                metrics=self._compute_basic_metrics(dependency_graph),
                errors=[],
                warnings=[],
                generation_time=time.time() - start_time
            )

        except ImportError as e:
            return VisualizationResult(
                success=False,
                output_path="",
                visualization_type=VisualizationType.STATIC_IMAGE,
                metrics=None,
                errors=[f"Graphviz package not available: {e}. Install with 'pip install graphviz'"],
                warnings=["Consider using interactive HTML visualization as fallback"],
                generation_time=time.time() - start_time
            )
        except graphviz.backend.ExecutableNotFound as e:
            return VisualizationResult(
                success=False,
                output_path="",
                visualization_type=VisualizationType.STATIC_IMAGE,
                metrics=None,
                errors=[f"Graphviz system executable not found: {e}. Install system package: 'apt install graphviz' or 'brew install graphviz'"],
                warnings=["Static image generation requires both Python package and system installation"],
                generation_time=time.time() - start_time
            )
        except OSError as e:
            return VisualizationResult(
                success=False,
                output_path="",
                visualization_type=VisualizationType.STATIC_IMAGE,
                metrics=None,
                errors=[f"File system error during image generation: {e}"],
                warnings=["Check output directory permissions and available disk space"],
                generation_time=time.time() - start_time
            )
        except Exception as e:
            return VisualizationResult(
                success=False,
                output_path="",
                visualization_type=VisualizationType.STATIC_IMAGE,
                metrics=None,
                errors=[f"Unexpected error during visualization generation: {e}"],
                warnings=["Consider using interactive HTML visualization as fallback"],
                generation_time=time.time() - start_time
            )

    def _create_graphviz_graph(self, dependency_graph: DependencyGraph) -> graphviz.Digraph:
        """Create Graphviz representation of dependency graph."""

        # Choose layout engine based on graph characteristics
        if len(dependency_graph.graph.nodes()) > 50:
            engine = 'fdp'  # Force-directed for large graphs
        else:
            engine = 'dot'  # Hierarchical for smaller graphs

        dot = graphviz.Digraph(
            comment='Python Dependency Graph',
            format=self.config.image_format,
            engine=engine
        )

        # Set global graph attributes
        dot.attr(
            rankdir='TB',  # Top to bottom
            splines='ortho',  # Orthogonal edges
            overlap='false',
            fontname='Arial',
            fontsize=str(self.config.font_size)
        )

        return dot

    def _apply_styling(self, dot_graph: graphviz.Digraph,
                      dependency_graph: DependencyGraph) -> None:
        """Apply visual styling to the graph."""

        # Color schemes
        colors = self._get_color_scheme()

        # Add nodes with styling
        for node in dependency_graph.graph.nodes(data=True):
            module_node = node[0]
            node_data = node[1]

            # Determine node style based on characteristics
            node_color = self._get_node_color(module_node, dependency_graph, colors)
            node_shape = self._get_node_shape(module_node)
            node_size = self._get_node_size(module_node, dependency_graph)

            # Create label with module information
            label = self._create_node_label(module_node)

            dot_graph.node(
                module_node.name,
                label=label,
                color=node_color,
                shape=node_shape,
                style='filled',
                fillcolor=node_color,
                fontcolor='white' if self._is_dark_color(node_color) else 'black'
            )

        # Add edges with styling
        for edge in dependency_graph.graph.edges(data=True):
            source, target, edge_data = edge

            edge_color = self._get_edge_color(source, target, dependency_graph, colors)
            edge_style = self._get_edge_style(source, target, dependency_graph)
            edge_weight = self._get_edge_weight(source, target, dependency_graph)

            dot_graph.edge(
                source.name,
                target.name,
                color=edge_color,
                style=edge_style,
                penwidth=str(edge_weight)
            )

    def _get_node_color(self, node: ModuleNode, graph: DependencyGraph,
                       colors: Dict[str, str]) -> str:
        """Determine color for a node based on its characteristics."""

        # Check if node is in a circular dependency
        for cycle in graph.detect_cycles():
            if node in cycle:
                return colors['cycle']

        # Check if node is a leaf (no dependencies)
        if graph.graph.out_degree(node) == 0:
            return colors['leaf']

        # Check if node is a root (no dependents)
        if graph.graph.in_degree(node) == 0:
            return colors['root']

        # Check if node is a package vs module
        if node.is_package:
            return colors['package']
        else:
            return colors['module']

    def _create_node_label(self, node: ModuleNode) -> str:
        """Create informative label for a node."""

        label_parts = [node.name]

        # Add type indicator
        if node.is_package:
            label_parts.append("(package)")

        # Add metrics if available
        if hasattr(node, 'metrics'):
            if node.metrics.get('lines_of_code'):
                label_parts.append(f"LOC: {node.metrics['lines_of_code']}")

        return "\\n".join(label_parts)

    def _get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme based on configuration."""

        schemes = {
            'default': {
                'module': '#4CAF50',     # Green
                'package': '#2196F3',    # Blue
                'leaf': '#FF9800',       # Orange
                'root': '#9C27B0',       # Purple
                'cycle': '#F44336',      # Red
                'edge': '#757575',       # Gray
                'cycle_edge': '#FF5722'  # Deep Orange
            },
            'colorblind': {
                'module': '#1f77b4',     # Blue
                'package': '#ff7f0e',    # Orange
                'leaf': '#2ca02c',       # Green
                'root': '#d62728',       # Red
                'cycle': '#9467bd',      # Purple
                'edge': '#7f7f7f',       # Gray
                'cycle_edge': '#8c564b'  # Brown
            },
            'high_contrast': {
                'module': '#000000',     # Black
                'package': '#FFFFFF',    # White
                'leaf': '#FF0000',       # Red
                'root': '#0000FF',       # Blue
                'cycle': '#FFFF00',      # Yellow
                'edge': '#808080',       # Gray
                'cycle_edge': '#FF00FF'  # Magenta
            }
        }

        return schemes.get(self.config.color_scheme, schemes['default'])

    def _get_vis_network_source(self) -> str:
        """Get the vis-network library source based on configuration."""

        if self.config.vis_network_source == "local" and self.config.local_assets_path:
            # Use local file
            local_path = Path(self.config.local_assets_path) / "vis-network.min.js"
            return f'<script src="{local_path}"></script>'
        elif self.config.vis_network_source == "bundled":
            # Inline the library (requires bundling step)
            return '<script>/* vis-network library would be inlined here */</script>'
        else:
            # Default to CDN
            return '<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>'
```

### 3. Interactive HTML Renderer

```python
class InteractiveHTMLRenderer:
    """Renders interactive HTML-based dependency graph visualization."""

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def render(self, dependency_graph: DependencyGraph, output_path: str) -> VisualizationResult:
        """Render interactive HTML visualization."""

        # Convert NetworkX graph to format suitable for web visualization
        graph_data = self._prepare_graph_data(dependency_graph)

        # Generate HTML with embedded JavaScript
        html_content = self._generate_html_content(graph_data, dependency_graph)

        # Write to file
        html_file = Path(output_path) / "dependency_graph.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return VisualizationResult(
            success=True,
            output_path=str(html_file),
            visualization_type=VisualizationType.INTERACTIVE_HTML,
            metrics=self._compute_basic_metrics(dependency_graph),
            errors=[],
            warnings=[],
            generation_time=0  # Computed elsewhere
        )

    def _prepare_graph_data(self, dependency_graph: DependencyGraph) -> Dict:
        """Prepare graph data for JavaScript visualization."""

        nodes = []
        edges = []

        # Convert nodes
        for node in dependency_graph.graph.nodes():
            node_data = {
                'id': node.name,
                'label': node.name,
                'type': 'package' if node.is_package else 'module',
                'path': node.path,
                'dependencies_count': dependency_graph.graph.out_degree(node),
                'dependents_count': dependency_graph.graph.in_degree(node),
                'documentation': getattr(node, 'documentation', ''),
                'is_in_cycle': self._is_node_in_cycle(node, dependency_graph)
            }
            nodes.append(node_data)

        # Convert edges
        for source, target in dependency_graph.graph.edges():
            edge_data = {
                'from': source.name,
                'to': target.name,
                'type': 'dependency'
            }
            edges.append(edge_data)

        return {
            'nodes': nodes,
            'edges': edges,
            'metrics': self._compute_basic_metrics(dependency_graph).__dict__
        }

    def _generate_html_content(self, graph_data: Dict,
                              dependency_graph: DependencyGraph) -> str:
        """Generate complete HTML content with embedded visualization."""

        # Check configuration for library source
        vis_network_source = self._get_vis_network_source()

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Dependency Graph</title>
    {vis_network_source}
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div id="controls">
        <h1>Python Dependency Graph</h1>
        <div class="control-panel">
            <input type="text" id="search" placeholder="Search nodes...">
            <button id="reset-view">Reset View</button>
            <button id="toggle-cycles">Toggle Cycles</button>
            <select id="layout-select">
                <option value="hierarchical">Hierarchical</option>
                <option value="force">Force Directed</option>
                <option value="circle">Circular</option>
            </select>
        </div>
        <div id="metrics">
            {self._generate_metrics_html(graph_data['metrics'])}
        </div>
    </div>

    <div id="graph-container">
        <div id="network"></div>
    </div>

    <div id="info-panel">
        <h3>Node Information</h3>
        <div id="node-details"></div>
    </div>

    <script>
        {self._generate_javascript(graph_data)}
    </script>
</body>
</html>
"""

    def _generate_javascript(self, graph_data: Dict) -> str:
        """Generate JavaScript code for interactive visualization."""

        return f"""
// Graph data
const graphData = {json.dumps(graph_data, indent=2)};

// Initialize network
const container = document.getElementById('network');
const data = {{
    nodes: new vis.DataSet(graphData.nodes),
    edges: new vis.DataSet(graphData.edges)
}};

const options = {{
    layout: {{
        hierarchical: {{
            direction: 'UD',
            sortMethod: 'directed'
        }}
    }},
    physics: {{
        enabled: true,
        hierarchicalRepulsion: {{
            centralGravity: 0.0,
            springLength: 100,
            springConstant: 0.01,
            nodeDistance: 120,
            damping: 0.09
        }}
    }},
    nodes: {{
        shape: 'box',
        margin: 10,
        font: {{
            size: 14,
            color: '#333333'
        }},
        borderWidth: 2,
        shadow: true
    }},
    edges: {{
        arrows: {{
            to: {{enabled: true, scaleFactor: 1, type: 'arrow'}}
        }},
        color: {{inherit: 'from'}},
        width: 2,
        smooth: {{
            type: 'cubicBezier',
            forceDirection: 'vertical',
            roundness: 0.4
        }}
    }},
    interaction: {{
        selectConnectedEdges: false,
        hover: true
    }}
}};

const network = new vis.Network(container, data, options);

// Event handlers
network.on('selectNode', function(event) {{
    const nodeId = event.nodes[0];
    const node = data.nodes.get(nodeId);
    displayNodeInfo(node);
}});

network.on('hoverNode', function(event) {{
    const nodeId = event.node;
    const node = data.nodes.get(nodeId);
    showTooltip(event.pointer.DOM, node);
}});

// Search functionality
document.getElementById('search').addEventListener('input', function(e) {{
    const searchTerm = e.target.value.toLowerCase();
    if (searchTerm) {{
        const filteredNodeIds = graphData.nodes
            .filter(node => node.label.toLowerCase().includes(searchTerm))
            .map(node => node.id);
        network.selectNodes(filteredNodeIds);
        if (filteredNodeIds.length > 0) {{
            network.focus(filteredNodeIds[0], {{scale: 1.5}});
        }}
    }} else {{
        network.unselectAll();
    }}
}});

// Reset view
document.getElementById('reset-view').addEventListener('click', function() {{
    network.fit();
    network.unselectAll();
    document.getElementById('search').value = '';
}});

// Toggle cycle highlighting
document.getElementById('toggle-cycles').addEventListener('click', function() {{
    const cycleNodes = graphData.nodes.filter(node => node.is_in_cycle);
    const currentColor = data.nodes.get(cycleNodes[0]?.id)?.color;

    cycleNodes.forEach(node => {{
        data.nodes.update({{
            id: node.id,
            color: currentColor === '#F44336' ? '#4CAF50' : '#F44336'
        }});
    }});
}});

// Layout change
document.getElementById('layout-select').addEventListener('change', function(e) {{
    const layout = e.target.value;
    const newOptions = {{...options}};

    if (layout === 'hierarchical') {{
        newOptions.layout = {{hierarchical: {{direction: 'UD', sortMethod: 'directed'}}}};
        newOptions.physics = {{enabled: false}};
    }} else if (layout === 'force') {{
        newOptions.layout = {{randomSeed: 2}};
        newOptions.physics = {{enabled: true}};
    }} else if (layout === 'circle') {{
        newOptions.layout = {{randomSeed: 2}};
        newOptions.physics = {{enabled: false}};
    }}

    network.setOptions(newOptions);
}});

// Helper functions
function displayNodeInfo(node) {{
    const infoPanel = document.getElementById('node-details');
    infoPanel.innerHTML = `
        <h4>${{node.label}}</h4>
        <p><strong>Type:</strong> ${{node.type}}</p>
        <p><strong>Path:</strong> ${{node.path}}</p>
        <p><strong>Dependencies:</strong> ${{node.dependencies_count}}</p>
        <p><strong>Dependents:</strong> ${{node.dependents_count}}</p>
        ${{node.is_in_cycle ? '<p><strong>⚠️ Part of circular dependency</strong></p>' : ''}}
        ${{node.documentation ? `<p><strong>Documentation:</strong></p><div class="documentation">${{node.documentation.substring(0, 200)}}...</div>` : ''}}
    `;
}}

function showTooltip(position, node) {{
    // Simple tooltip implementation
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.innerHTML = `${{node.label}} (${{node.type}})`;
    tooltip.style.left = position.x + 'px';
    tooltip.style.top = position.y + 'px';
    document.body.appendChild(tooltip);

    setTimeout(() => {{
        document.body.removeChild(tooltip);
    }}, 2000);
}}
"""
```

### 4. Analysis Report Renderer

```python
class AnalysisReportRenderer:
    """Generates comprehensive textual analysis reports."""

    def __init__(self, config: VisualizationConfig):
        self.config = config

    def render(self, dependency_graph: DependencyGraph, output_path: str) -> VisualizationResult:
        """Generate comprehensive dependency analysis report."""

        # Compute comprehensive metrics
        metrics = self._compute_comprehensive_metrics(dependency_graph)

        # Generate report sections
        report_sections = [
            self._generate_executive_summary(dependency_graph, metrics),
            self._generate_structural_analysis(dependency_graph, metrics),
            self._generate_complexity_analysis(dependency_graph, metrics),
            self._generate_circular_dependency_analysis(dependency_graph, metrics),
            self._generate_recommendations(dependency_graph, metrics),
            self._generate_detailed_node_analysis(dependency_graph, metrics)
        ]

        # Combine into final report
        full_report = "\n\n".join(report_sections)

        # Write report to file
        report_file = Path(output_path) / "dependency_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(full_report)

        return VisualizationResult(
            success=True,
            output_path=str(report_file),
            visualization_type=VisualizationType.ANALYSIS_REPORT,
            metrics=metrics,
            errors=[],
            warnings=[],
            generation_time=0
        )

    def _generate_executive_summary(self, graph: DependencyGraph, metrics: GraphMetrics) -> str:
        """Generate executive summary of the dependency analysis."""

        return f"""# Dependency Analysis Report

## Executive Summary

This report provides a comprehensive analysis of the Python project's dependency structure.

### Key Findings

- **Total Modules**: {metrics.total_nodes}
- **Total Dependencies**: {metrics.total_edges}
- **Circular Dependencies**: {len(metrics.circular_dependencies)}
- **Maximum Dependency Depth**: {metrics.max_depth}
- **Average Dependencies per Module**: {metrics.average_degree:.2f}

### Overall Assessment

{self._generate_assessment_text(metrics)}
"""

    def _generate_structural_analysis(self, graph: DependencyGraph, metrics: GraphMetrics) -> str:
        """Generate structural analysis section."""

        return f"""## Structural Analysis

### Dependency Distribution

- **Leaf Nodes** (no dependencies): {len(metrics.leaf_nodes)}
- **Root Nodes** (no dependents): {len(metrics.root_nodes)}
- **Intermediate Nodes**: {metrics.total_nodes - len(metrics.leaf_nodes) - len(metrics.root_nodes)}

### Architecture Patterns

{self._analyze_architecture_patterns(graph, metrics)}

### Module Categorization

{self._categorize_modules(graph, metrics)}
"""

    def _generate_circular_dependency_analysis(self, graph: DependencyGraph,
                                             metrics: GraphMetrics) -> str:
        """Generate analysis of circular dependencies."""

        if not metrics.circular_dependencies:
            return """## Circular Dependencies

✅ **No circular dependencies detected.** This indicates a well-structured, hierarchical architecture.
"""

        sections = ["## Circular Dependencies\n"]
        sections.append(f"⚠️ **{len(metrics.circular_dependencies)} circular dependency groups detected.**\n")

        for i, cycle in enumerate(metrics.circular_dependencies, 1):
            sections.append(f"### Cycle {i}: {' → '.join(cycle)} → {cycle[0]}")
            sections.append(self._analyze_cycle_impact(cycle, graph))
            sections.append("")

        sections.append("### Recommendations for Breaking Cycles")
        sections.append(self._generate_cycle_breaking_recommendations(metrics.circular_dependencies, graph))

        return "\n".join(sections)

    def _generate_recommendations(self, graph: DependencyGraph, metrics: GraphMetrics) -> str:
        """Generate actionable recommendations."""

        recommendations = ["## Recommendations\n"]

        # Architecture recommendations
        if len(metrics.circular_dependencies) > 0:
            recommendations.append("### 🔄 Circular Dependencies")
            recommendations.append("- Consider refactoring to break circular dependencies")
            recommendations.append("- Extract common functionality into separate modules")
            recommendations.append("- Use dependency injection patterns")
            recommendations.append("")

        # Complexity recommendations
        if metrics.average_degree > 5:
            recommendations.append("### 📊 High Coupling")
            recommendations.append("- Consider splitting highly coupled modules")
            recommendations.append("- Apply single responsibility principle")
            recommendations.append("- Reduce module interdependencies")
            recommendations.append("")

        # Performance recommendations
        if metrics.total_nodes > 100:
            recommendations.append("### ⚡ Performance")
            recommendations.append("- Consider lazy loading for large dependency chains")
            recommendations.append("- Optimize import statements")
            recommendations.append("- Consider package restructuring")
            recommendations.append("")

        return "\n".join(recommendations)
```

### 5. Circular Dependency Renderer

```python
class CircularDependencyRenderer:
    """Specialized renderer for circular dependency visualization."""

    def render(self, dependency_graph: DependencyGraph, output_path: str) -> VisualizationResult:
        """Render focused visualization of circular dependencies."""

        cycles = dependency_graph.detect_cycles()

        if not cycles:
            # Generate report indicating no cycles
            return self._generate_no_cycles_report(output_path)

        # Create focused visualizations for each cycle
        results = []

        for i, cycle in enumerate(cycles):
            cycle_graph = self._extract_cycle_subgraph(dependency_graph, cycle)
            cycle_output = Path(output_path) / f"cycle_{i+1}"
            cycle_output.mkdir(exist_ok=True)

            # Generate static visualization
            static_result = self._render_cycle_static(cycle_graph, cycle_output)

            # Generate analysis report
            analysis_result = self._render_cycle_analysis(cycle, dependency_graph, cycle_output)

            results.extend([static_result, analysis_result])

        # Generate summary
        summary_result = self._render_cycles_summary(cycles, dependency_graph, output_path)
        results.append(summary_result)

        return VisualizationResult(
            success=all(r.success for r in results),
            output_path=output_path,
            visualization_type=VisualizationType.CIRCULAR_DEPENDENCY_FOCUS,
            metrics=None,
            errors=[error for r in results for error in r.errors],
            warnings=[warning for r in results for warning in r.warnings],
            generation_time=sum(r.generation_time for r in results)
        )
```

### 6. Dependency Management and Fallbacks

```python
def handle_missing_dependencies(self) -> None:
    """Handle missing dependencies gracefully with appropriate fallbacks."""

    missing_deps = []
    warnings = []

    # Check for Graphviz
    try:
        import graphviz
        try:
            # Test if system graphviz is available
            graphviz.Digraph().render(format='png', engine='dot')
        except graphviz.backend.ExecutableNotFound:
            warnings.append("Graphviz system package not found. Static image generation disabled.")
            warnings.append("Install with: 'apt install graphviz' or 'brew install graphviz'")
    except ImportError:
        missing_deps.append("graphviz")
        warnings.append("Graphviz Python package not found. Install with: 'pip install graphviz'")

    # Check internet connectivity for CDN
    if self.config.vis_network_source == "cdn":
        if not self._check_internet_connectivity():
            warnings.append("No internet connectivity detected. Interactive visualizations may not work.")
            warnings.append("Consider using local_assets_path configuration for offline use.")

    if missing_deps:
        print(f"Missing optional dependencies: {', '.join(missing_deps)}")
        print("Some visualization features may be unavailable.")

    for warning in warnings:
        print(f"Warning: {warning}")

def _check_internet_connectivity(self) -> bool:
    """Check if internet connectivity is available for CDN resources."""
    try:
        import urllib.request
        urllib.request.urlopen('https://unpkg.com/', timeout=5)
        return True
    except:
        return False
```

## Integration with Main System

### 1. Enhanced Main Function Integration

```python
def main():
    """Enhanced main function with visualization options."""

    # ... existing code ...

    # Ask user about visualization options
    generate_visualizations = input("\nGenerate dependency visualizations? (y/n, default: y): ").lower() != 'n'

    if generate_visualizations:
        viz_config = VisualizationConfig()
        viz_system = VisualizationSystem(viz_config)

        print("Generating dependency visualizations...")

        # Create output directory
        viz_output_dir = Path(repo_path) / "dependency_analysis"
        viz_output_dir.mkdir(exist_ok=True)

        # Generate comprehensive report
        comprehensive_report_path = viz_system.create_comprehensive_report(
            dependency_graph, str(viz_output_dir)
        )

        print(f"Visualizations saved to: {viz_output_dir}")
        print(f"Comprehensive report: {comprehensive_report_path}")
```

### 2. Configuration Integration

```python
# Add to OrchestratorConfig
@dataclass
class OrchestratorConfig:
    # ... existing fields ...

    # Visualization options
    generate_visualizations: bool = True
    visualization_types: List[VisualizationType] = field(
        default_factory=lambda: [
            VisualizationType.STATIC_IMAGE,
            VisualizationType.INTERACTIVE_HTML,
            VisualizationType.ANALYSIS_REPORT
        ]
    )
    visualization_config: VisualizationConfig = field(default_factory=VisualizationConfig)
```

## Testing Strategy

### Unit Tests

```python
def test_static_image_generation():
    """Test generation of static dependency graph images."""

def test_interactive_html_generation():
    """Test generation of interactive HTML visualizations."""

def test_analysis_report_generation():
    """Test generation of dependency analysis reports."""

def test_circular_dependency_visualization():
    """Test specialized circular dependency visualizations."""

def test_graph_metrics_computation():
    """Test computation of various graph metrics."""
```

### Integration Tests

```python
def test_visualization_with_real_projects():
    """Test visualization generation with real project structures."""

def test_large_graph_performance():
    """Test performance with large dependency graphs."""

def test_visualization_error_handling():
    """Test handling of errors during visualization generation."""
```

## Success Criteria

1. **Visual Quality**: Clear, informative visualizations that aid understanding
2. **Performance**: Generate visualizations for 1000+ node graphs in <60 seconds
3. **Usability**: Interactive features work smoothly in modern browsers
4. **Accuracy**: All graph relationships are correctly represented
5. **Flexibility**: Support various output formats and styling options

---

*This specification defines a comprehensive visualization system that transforms dependency graph data into actionable insights through multiple visualization types and analysis reports.*
