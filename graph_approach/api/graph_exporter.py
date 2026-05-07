"""
Graph Exporter

Exports NetworkX dependency graphs to JSON format for web visualization.
"""

from typing import Dict, List, Any, Optional
import json

from graph_approach.core.dependency_graph import DependencyGraph, NodeType, EdgeType


class GraphExporter:
    """
    Export dependency graphs to web-friendly JSON format

    Output format compatible with D3.js and React Flow
    """

    @staticmethod
    def to_json(graph: DependencyGraph, include_source: bool = False) -> Dict[str, Any]:
        """
        Export graph to JSON format

        Args:
            graph: DependencyGraph to export
            include_source: Whether to include source code in nodes

        Returns:
            Dictionary with nodes and edges suitable for visualization
        """
        # Export nodes
        nodes = []
        for node_id, node in graph.nodes.items():
            node_data = {
                "id": node_id,
                "label": node.name,
                "type": node.node_type.value,
                "metadata": {
                    "line_start": node.line_start,
                    "line_end": node.line_end,
                }
            }

            # Optionally include source code
            if include_source and node.source_code:
                node_data["source"] = node.source_code

            # Add custom metadata
            if node.metadata:
                for key, value in node.metadata.items():
                    if key not in node_data["metadata"]:
                        node_data["metadata"][key] = value

            nodes.append(node_data)

        # Export edges
        edges = []
        for from_id, to_id, edge_type in graph.get_all_edges():
            edge_data = {
                "source": from_id,
                "target": to_id,
                "type": edge_type.value,
                "label": edge_type.value.replace("_", " ").title()
            }
            edges.append(edge_data)

        # Get execution layers
        layers = []
        try:
            execution_layers = graph.get_execution_layers()
            for i, layer in enumerate(execution_layers):
                layer_data = {
                    "layer": i,
                    "nodes": [node.node_id for node in layer]
                }
                layers.append(layer_data)
        except Exception:
            # Graph might have cycles or other issues
            layers = []

        # Graph statistics
        stats = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(list(graph.get_all_edges())),
            "has_cycles": graph.has_cycles(),
            "node_types": GraphExporter._count_node_types(graph),
            "edge_types": GraphExporter._count_edge_types(graph),
            "total_layers": len(layers)
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "layers": layers,
            "stats": stats
        }

    @staticmethod
    def to_d3_format(graph: DependencyGraph) -> Dict[str, Any]:
        """
        Export graph in D3.js force-directed graph format

        Args:
            graph: DependencyGraph to export

        Returns:
            Dictionary with nodes and links arrays
        """
        json_data = GraphExporter.to_json(graph, include_source=False)

        # Convert edges to D3 "links" format
        links = []
        for edge in json_data["edges"]:
            links.append({
                "source": edge["source"],
                "target": edge["target"],
                "type": edge["type"]
            })

        return {
            "nodes": json_data["nodes"],
            "links": links,
            "layers": json_data["layers"],
            "stats": json_data["stats"]
        }

    @staticmethod
    def to_react_flow_format(graph: DependencyGraph) -> Dict[str, Any]:
        """
        Export graph in React Flow format

        Args:
            graph: DependencyGraph to export

        Returns:
            Dictionary with nodes and edges in React Flow format
        """
        json_data = GraphExporter.to_json(graph, include_source=False)

        # Get layers for positioning
        layers = json_data["layers"]

        # Convert nodes to React Flow format with positions
        nodes = []
        for i, node in enumerate(json_data["nodes"]):
            # Find layer for this node
            layer_index = 0
            for layer in layers:
                if node["id"] in layer["nodes"]:
                    layer_index = layer["layer"]
                    break

            # Position based on layer (vertical) and index within layer (horizontal)
            nodes_in_layer = [n for n in json_data["nodes"]
                            if any(node["id"] in layer["nodes"]
                                 for layer in layers
                                 if layer["layer"] == layer_index)]

            index_in_layer = nodes_in_layer.index(node) if node in nodes_in_layer else 0
            total_in_layer = len(nodes_in_layer)

            # Calculate position
            x = (index_in_layer + 1) * (1000 / (total_in_layer + 1))
            y = layer_index * 150 + 100

            react_node = {
                "id": node["id"],
                "type": "custom",  # Use custom node component
                "data": {
                    "label": node["label"],
                    "nodeType": node["type"],
                    "metadata": node.get("metadata", {})
                },
                "position": {"x": x, "y": y}
            }
            nodes.append(react_node)

        # Convert edges to React Flow format
        edges = []
        for i, edge in enumerate(json_data["edges"]):
            react_edge = {
                "id": f"e{i}",
                "source": edge["source"],
                "target": edge["target"],
                "type": "smoothstep",  # or 'default', 'straight', 'step'
                "animated": False,
                "label": edge["label"],
                "data": {
                    "edgeType": edge["type"]
                }
            }
            edges.append(react_edge)

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": json_data["stats"]
        }

    @staticmethod
    def _count_node_types(graph: DependencyGraph) -> Dict[str, int]:
        """Count nodes by type"""
        counts = {node_type.value: 0 for node_type in NodeType}
        for node in graph.nodes.values():
            counts[node.node_type.value] += 1
        return {k: v for k, v in counts.items() if v > 0}

    @staticmethod
    def _count_edge_types(graph: DependencyGraph) -> Dict[str, int]:
        """Count edges by type"""
        counts = {edge_type.value: 0 for edge_type in EdgeType}
        for _, _, edge_type in graph.get_all_edges():
            counts[edge_type.value] += 1
        return {k: v for k, v in counts.items() if v > 0}

    @staticmethod
    def export_to_file(
        graph: DependencyGraph,
        output_path: str,
        format: str = "json"
    ) -> bool:
        """
        Export graph to file

        Args:
            graph: DependencyGraph to export
            output_path: Output file path
            format: Export format ('json', 'd3', 'react-flow')

        Returns:
            True if successful
        """
        try:
            if format == "d3":
                data = GraphExporter.to_d3_format(graph)
            elif format == "react-flow":
                data = GraphExporter.to_react_flow_format(graph)
            else:
                data = GraphExporter.to_json(graph, include_source=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error exporting graph: {e}")
            return False
