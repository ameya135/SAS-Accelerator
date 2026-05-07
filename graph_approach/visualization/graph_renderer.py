"""
Graph Renderer

Generates visualizations of dependency graphs using Graphviz.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import subprocess

try:
    import graphviz

    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print(
        "Warning: graphviz package not installed. Falling back to DOT file generation."
    )

from graph_approach.core.dependency_graph import DependencyGraph, NodeType, EdgeType


class GraphRenderer:
    """
    Render dependency graphs to various formats using Graphviz

    Supports DOT, PNG, SVG, PDF output formats.
    """

    # Color schemes for node types
    NODE_COLORS = {
        NodeType.DATASET: "#e1f5fe",  # Light blue
        NodeType.DATA_STEP: "#fff9c4",  # Light yellow
        NodeType.PROC: "#f3e5f5",  # Light purple
        NodeType.MACRO: "#c8e6c9",  # Light green
        NodeType.MACRO_VARIABLE: "#ffe0b2",  # Light orange
        NodeType.LIBRARY: "#ffccbc",  # Light deep orange
        NodeType.FILE_REF: "#d7ccc8",  # Light brown
    }

    # Shapes for node types
    NODE_SHAPES = {
        NodeType.DATASET: "cylinder",
        NodeType.DATA_STEP: "box",
        NodeType.PROC: "component",
        NodeType.MACRO: "hexagon",
        NodeType.MACRO_VARIABLE: "oval",
        NodeType.LIBRARY: "folder",
        NodeType.FILE_REF: "note",
    }

    # Edge styles
    EDGE_STYLES = {
        EdgeType.READS_FROM: {"style": "solid", "color": "blue"},
        EdgeType.WRITES_TO: {"style": "solid", "color": "green"},
        EdgeType.CALLS: {"style": "dashed", "color": "purple"},
        EdgeType.USES_VARIABLE: {"style": "dotted", "color": "orange"},
        EdgeType.DEFINES_VARIABLE: {"style": "dotted", "color": "darkorange"},
        EdgeType.PROC_INPUT: {"style": "solid", "color": "darkblue"},
        EdgeType.PROC_OUTPUT: {"style": "solid", "color": "darkgreen"},
    }

    def __init__(self):
        """Initialize graph renderer"""
        self.use_graphviz_lib = GRAPHVIZ_AVAILABLE

    def render_to_dot(
        self,
        graph: DependencyGraph,
        title: Optional[str] = None,
        show_layers: bool = True,
    ) -> str:
        """
        Generate DOT file content

        Args:
            graph: Dependency graph to render
            title: Graph title
            show_layers: Whether to group nodes by execution layer

        Returns:
            DOT file content as string
        """
        lines = []

        # Graph header
        lines.append("digraph SAS_Migration {")
        lines.append("  rankdir=TB;")  # Top to bottom layout
        lines.append('  node [fontname="Helvetica"];')
        lines.append('  edge [fontname="Helvetica"];')

        # Add title
        if title:
            lines.append(f'  labelloc="t";')
            lines.append(f'  label="{title}";')
            lines.append(f"  fontsize=20;")

        # Add nodes
        for node in graph.nodes.values():
            color = self.NODE_COLORS.get(node.node_type, "#ffffff")
            shape = self.NODE_SHAPES.get(node.node_type, "box")

            # Create label
            label = node.name
            if node.metadata:
                # Add some metadata to label
                if "proc_name" in node.metadata:
                    label = f"{node.metadata['proc_name']}\\n{node.name}"

            lines.append(
                f'  "{node.node_id}" [label="{label}", '
                f"shape={shape}, "
                f"style=filled, "
                f'fillcolor="{color}"];'
            )

        # Add edges
        for from_id, to_id, edge_type in graph.get_all_edges():
            style_info = self.EDGE_STYLES.get(
                edge_type, {"style": "solid", "color": "black"}
            )

            lines.append(
                f'  "{from_id}" -> "{to_id}" '
                f"[style={style_info['style']}, color={style_info['color']}, "
                f'label="{edge_type.value}"];'
            )

        # Group by layers if requested
        if show_layers and not graph.has_cycles():
            try:
                layers = graph.get_execution_layers()
                for layer_idx, layer_nodes in enumerate(layers):
                    node_ids = [n.node_id for n in layer_nodes]
                    if len(node_ids) > 1:
                        node_list = " ".join(f'"{nid}"' for nid in node_ids)
                        lines.append(f"  {{ rank=same; {node_list} }}")
            except Exception:
                pass  # Skip layer grouping if it fails

        lines.append("}")

        return "\n".join(lines)

    def render_to_file(
        self,
        graph: DependencyGraph,
        output_path: str,
        format: str = "png",
        title: Optional[str] = None,
    ) -> bool:
        """
        Render graph to file

        Args:
            graph: Dependency graph
            output_path: Output file path
            format: Output format (png, svg, pdf, dot)
            title: Graph title

        Returns:
            True if successful, False otherwise
        """
        try:
            dot_content = self.render_to_dot(graph, title=title)

            if format == "dot":
                # Just save DOT file
                with open(output_path, "w") as f:
                    f.write(dot_content)
                return True

            if self.use_graphviz_lib:
                # Use graphviz library
                return self._render_with_graphviz_lib(dot_content, output_path, format)
            else:
                # Use DOT command line
                return self._render_with_dot_command(dot_content, output_path, format)

        except Exception as e:
            print(f"Error rendering graph: {e}")
            return False

    def _render_with_graphviz_lib(
        self, dot_content: str, output_path: str, format: str
    ) -> bool:
        """Render using graphviz Python library"""
        try:
            src = graphviz.Source(dot_content)

            # Remove extension from output_path
            output_path_no_ext = str(Path(output_path).with_suffix(""))

            src.render(output_path_no_ext, format=format, cleanup=True)
            return True
        except Exception as e:
            print(f"Graphviz library rendering failed: {e}")
            return False

    def _render_with_dot_command(
        self, dot_content: str, output_path: str, format: str
    ) -> bool:
        """Render using dot command line tool"""
        try:
            # Write DOT to temporary file
            temp_dot = f"{output_path}.dot"
            with open(temp_dot, "w") as f:
                f.write(dot_content)

            # Run dot command
            subprocess.run(
                ["dot", f"-T{format}", temp_dot, "-o", output_path],
                check=True,
                capture_output=True,
            )

            # Clean up temp file
            Path(temp_dot).unlink()
            return True

        except subprocess.CalledProcessError as e:
            print(f"DOT command failed: {e}")
            return False
        except FileNotFoundError:
            print("DOT command not found. Please install Graphviz.")
            return False

    def render_execution_flow(
        self, graph: DependencyGraph, output_path: str, format: str = "png"
    ) -> bool:
        """
        Render execution flow diagram with layers highlighted

        Args:
            graph: Dependency graph
            output_path: Output file path
            format: Output format

        Returns:
            True if successful
        """
        return self.render_to_file(
            graph=graph, output_path=output_path, format=format, title="Execution Flow"
        )

    def create_legend(self) -> str:
        """Create legend for graph visualizations"""
        lines = []
        lines.append("digraph Legend {")
        lines.append("  rankdir=LR;")
        lines.append('  label="Legend";')
        lines.append('  node [fontname="Helvetica"];')

        # Add node type legend
        lines.append("  subgraph cluster_nodes {")
        lines.append('    label="Node Types";')
        for node_type in NodeType:
            color = self.NODE_COLORS.get(node_type, "#ffffff")
            shape = self.NODE_SHAPES.get(node_type, "box")
            lines.append(
                f'    "{node_type.value}" '
                f'[label="{node_type.value}", shape={shape}, '
                f'style=filled, fillcolor="{color}"];'
            )
        lines.append("  }")

        # Add edge type legend
        lines.append("  subgraph cluster_edges {")
        lines.append('    label="Edge Types";')
        lines.append("    node [shape=plaintext];")
        for i, edge_type in enumerate(EdgeType):
            style_info = self.EDGE_STYLES.get(
                edge_type, {"style": "solid", "color": "black"}
            )
            lines.append(
                f"    e{i}_from -> e{i}_to "
                f'[label="{edge_type.value}", '
                f"style={style_info['style']}, "
                f"color={style_info['color']}];"
            )
        lines.append("  }")

        lines.append("}")
        return "\n".join(lines)


def quick_render(
    graph: DependencyGraph, output_path: str, title: Optional[str] = None
) -> bool:
    """
    Quick helper function to render a graph

    Args:
        graph: Dependency graph
        output_path: Output path
        title: Optional title

    Returns:
        True if successful
    """
    renderer = GraphRenderer()
    format = Path(output_path).suffix[1:]  # Get extension without dot
    if not format:
        format = "png"

    return renderer.render_to_file(graph, output_path, format=format, title=title)
