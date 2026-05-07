"""
Dependency Graph Data Structures

This module provides graph-based data structures for tracking dependencies
in SAS code, built on NetworkX for graph algorithms.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import networkx as nx
from collections import defaultdict


class NodeType(Enum):
    """Types of nodes in the dependency graph"""

    DATASET = "dataset"
    MACRO = "macro"
    MACRO_VARIABLE = "macro_variable"
    FILE_REF = "file_ref"
    LIBRARY = "library"
    PROC = "proc"
    DATA_STEP = "data_step"


class EdgeType(Enum):
    """Types of edges (dependencies) in the graph"""

    READS_FROM = "reads_from"  # DATA step reads from dataset
    WRITES_TO = "writes_to"  # DATA step creates dataset
    CALLS = "calls"  # Macro calls another macro
    USES_VARIABLE = "uses_variable"  # Uses macro variable
    DEFINES_VARIABLE = "defines_variable"  # Defines macro variable
    DEPENDS_ON_FILE = "depends_on_file"  # Depends on file/library
    PROC_INPUT = "proc_input"  # PROC reads from dataset
    PROC_OUTPUT = "proc_output"  # PROC creates dataset


@dataclass
class DependencyNode:
    """
    A node in the dependency graph representing a SAS code element

    Attributes:
        node_id: Unique identifier for the node
        node_type: Type of the node (DATASET, MACRO, etc.)
        name: Human-readable name
        source_code: Original SAS code for this element
        metadata: Additional metadata (options, parameters, etc.)
        line_start: Starting line number in source file
        line_end: Ending line number in source file
    """

    node_id: str
    node_type: NodeType
    name: str
    source_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        if isinstance(other, DependencyNode):
            return self.node_id == other.node_id
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "source_code": self.source_code,
            "metadata": self.metadata,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyNode":
        """Create node from dictionary"""
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            name=data["name"],
            source_code=data.get("source_code", ""),
            metadata=data.get("metadata", {}),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
        )


class DependencyGraph:
    """
    Dependency graph for SAS code elements using NetworkX backend

    Provides graph operations like topological sort, cycle detection,
    and dependency traversal.
    """

    def __init__(self):
        """Initialize an empty dependency graph"""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, DependencyNode] = {}
        self._node_type_index: Dict[NodeType, Set[str]] = defaultdict(set)

    def add_node(self, node: DependencyNode) -> None:
        """
        Add a node to the graph

        Args:
            node: DependencyNode to add
        """
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id, **node.to_dict())
        self._node_type_index[node.node_type].add(node.node_id)

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: EdgeType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an edge (dependency) between two nodes

        Args:
            from_id: Source node ID
            to_id: Target node ID
            edge_type: Type of dependency
            metadata: Additional edge metadata
        """
        if from_id not in self.nodes:
            raise ValueError(f"Source node {from_id} not found in graph")
        if to_id not in self.nodes:
            raise ValueError(f"Target node {to_id} not found in graph")

        edge_data = {"edge_type": edge_type.value}
        if metadata:
            edge_data.update(metadata)

        self.graph.add_edge(from_id, to_id, **edge_data)

    def get_node(self, node_id: str) -> Optional[DependencyNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> List[DependencyNode]:
        """Get all nodes of a specific type"""
        return [self.nodes[nid] for nid in self._node_type_index[node_type]]

    def get_dependencies(self, node_id: str, depth: int = 1) -> List[DependencyNode]:
        """
        Get all dependencies of a node (what it depends on)

        Args:
            node_id: Node to get dependencies for
            depth: Maximum depth to traverse (1 = direct dependencies only)

        Returns:
            List of nodes that this node depends on
        """
        if node_id not in self.nodes:
            return []

        if depth == 1:
            # Direct dependencies only
            predecessors = list(self.graph.predecessors(node_id))
            return [self.nodes[pred] for pred in predecessors]
        else:
            # Use BFS to find dependencies up to depth
            dependencies = []
            visited = set()
            queue = [(node_id, 0)]

            while queue:
                current, curr_depth = queue.pop(0)
                if curr_depth >= depth:
                    continue

                for pred in self.graph.predecessors(current):
                    if pred not in visited:
                        visited.add(pred)
                        dependencies.append(self.nodes[pred])
                        queue.append((pred, curr_depth + 1))

            return dependencies

    def get_dependents(self, node_id: str, depth: int = 1) -> List[DependencyNode]:
        """
        Get all dependents of a node (what depends on it)

        Args:
            node_id: Node to get dependents for
            depth: Maximum depth to traverse

        Returns:
            List of nodes that depend on this node
        """
        if node_id not in self.nodes:
            return []

        if depth == 1:
            successors = list(self.graph.successors(node_id))
            return [self.nodes[succ] for succ in successors]
        else:
            dependents = []
            visited = set()
            queue = [(node_id, 0)]

            while queue:
                current, curr_depth = queue.pop(0)
                if curr_depth >= depth:
                    continue

                for succ in self.graph.successors(current):
                    if succ not in visited:
                        visited.add(succ)
                        dependents.append(self.nodes[succ])
                        queue.append((succ, curr_depth + 1))

            return dependents

    def topological_sort(self) -> List[DependencyNode]:
        """
        Return nodes in topological order (dependencies before dependents)

        Returns:
            List of nodes in execution order

        Raises:
            nx.NetworkXError: If graph has cycles
        """
        try:
            sorted_ids = list(nx.topological_sort(self.graph))
            return [self.nodes[nid] for nid in sorted_ids]
        except (nx.NetworkXError, nx.NetworkXUnfeasible) as e:
            raise ValueError(f"Cannot sort graph with cycles: {e}")

    def find_cycles(self) -> List[List[str]]:
        """
        Find all cycles in the graph

        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def get_execution_layers(self) -> List[List[DependencyNode]]:
        """
        Group nodes into execution layers where nodes in the same layer
        can be executed in parallel (no dependencies between them)

        Returns:
            List of layers, where each layer is a list of nodes
        """
        if self.has_cycles():
            raise ValueError("Cannot create execution layers for graph with cycles")

        # Use topological generations (layers)
        layers = []
        for generation in nx.topological_generations(self.graph):
            layer_nodes = [self.nodes[nid] for nid in generation]
            layers.append(layer_nodes)

        return layers

    def has_cycles(self) -> bool:
        """Check if the graph has any cycles"""
        return not nx.is_directed_acyclic_graph(self.graph)

    def break_cycles(self) -> List[Tuple[str, str, EdgeType]]:
        """
        Break cycles in the graph by removing strategic edges

        Strategy:
        1. Prioritize breaking self-referential edges (in-place updates)
        2. For complex cycles, remove edges with lowest priority
        3. Track which edges were removed for reporting

        Returns:
            List of removed edges (from_id, to_id, edge_type)
        """
        removed_edges = []

        # Keep breaking cycles until graph is acyclic
        while not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            if not cycles:
                break

            # Get the first cycle
            cycle = cycles[0]

            # Strategy 1: Look for self-referential edges (A -> A)
            self_ref_edge = None
            for i, node_id in enumerate(cycle):
                next_node_id = cycle[(i + 1) % len(cycle)]
                if node_id == next_node_id:
                    self_ref_edge = (node_id, next_node_id)
                    break

            if self_ref_edge:
                # Remove self-referential edge
                edge_data = self.graph.get_edge_data(self_ref_edge[0], self_ref_edge[1])
                edge_type = EdgeType(edge_data["edge_type"])
                self.graph.remove_edge(self_ref_edge[0], self_ref_edge[1])
                removed_edges.append((self_ref_edge[0], self_ref_edge[1], edge_type))
                continue

            # Strategy 2: Look for in-place update pattern (DATA step reading and writing same dataset)
            # Pattern: data_step -> dataset (WRITES_TO) and dataset -> data_step (READS_FROM)
            in_place_edge = None
            for i, node_id in enumerate(cycle):
                next_node_id = cycle[(i + 1) % len(cycle)]

                # Check if this is an in-place update pattern
                node = self.nodes.get(node_id)
                next_node = self.nodes.get(next_node_id)

                if node and next_node:
                    # If dataset -> data_step edge and data_step writes to that dataset
                    if (
                        node.node_type == NodeType.DATASET
                        and next_node.node_type == NodeType.DATA_STEP
                        and self.graph.has_edge(next_node_id, node_id)
                    ):
                        # Break the READS_FROM edge (dataset -> data_step)
                        in_place_edge = (node_id, next_node_id)
                        break

            if in_place_edge:
                edge_data = self.graph.get_edge_data(in_place_edge[0], in_place_edge[1])
                edge_type = EdgeType(edge_data["edge_type"])
                self.graph.remove_edge(in_place_edge[0], in_place_edge[1])
                removed_edges.append((in_place_edge[0], in_place_edge[1], edge_type))

                # Mark the data step node as in-place update
                data_step_node = self.nodes.get(in_place_edge[1])
                if data_step_node and data_step_node.metadata:
                    data_step_node.metadata["in_place_update"] = True
                continue

            # Strategy 3: Break the weakest edge (last resort)
            # Choose edge with lowest priority based on edge type
            edge_priority = {
                EdgeType.READS_FROM: 1,
                EdgeType.WRITES_TO: 3,
                EdgeType.PROC_INPUT: 2,
                EdgeType.PROC_OUTPUT: 3,
                EdgeType.CALLS: 4,
                EdgeType.USES_VARIABLE: 1,
                EdgeType.DEFINES_VARIABLE: 2,
            }

            weakest_edge = None
            weakest_priority = float("inf")

            for i, node_id in enumerate(cycle):
                next_node_id = cycle[(i + 1) % len(cycle)]
                if self.graph.has_edge(node_id, next_node_id):
                    edge_data = self.graph.get_edge_data(node_id, next_node_id)
                    edge_type = EdgeType(edge_data["edge_type"])
                    priority = edge_priority.get(edge_type, 5)

                    if priority < weakest_priority:
                        weakest_priority = priority
                        weakest_edge = (node_id, next_node_id, edge_type)

            if weakest_edge:
                self.graph.remove_edge(weakest_edge[0], weakest_edge[1])
                removed_edges.append(weakest_edge)

        return removed_edges

    def get_subgraph(self, node_ids: List[str]) -> "DependencyGraph":
        """
        Create a subgraph containing only specified nodes and their relationships

        Args:
            node_ids: List of node IDs to include

        Returns:
            New DependencyGraph containing only specified nodes
        """
        subgraph = DependencyGraph()

        # Add nodes
        for nid in node_ids:
            if nid in self.nodes:
                subgraph.add_node(self.nodes[nid])

        # Add edges between included nodes
        for from_id in node_ids:
            for to_id in node_ids:
                if self.graph.has_edge(from_id, to_id):
                    edge_data = self.graph.get_edge_data(from_id, to_id)
                    edge_type = EdgeType(edge_data["edge_type"])
                    metadata = {k: v for k, v in edge_data.items() if k != "edge_type"}
                    subgraph.add_edge(from_id, to_id, edge_type, metadata)

        return subgraph

    def get_root_nodes(self) -> List[DependencyNode]:
        """
        Get all root nodes (nodes with no dependencies)

        Returns:
            List of nodes that don't depend on anything
        """
        roots = []
        for node_id in self.nodes:
            if self.graph.in_degree(node_id) == 0:
                roots.append(self.nodes[node_id])
        return roots

    def get_leaf_nodes(self) -> List[DependencyNode]:
        """
        Get all leaf nodes (nodes that nothing depends on)

        Returns:
            List of nodes that nothing depends on
        """
        leaves = []
        for node_id in self.nodes:
            if self.graph.out_degree(node_id) == 0:
                leaves.append(self.nodes[node_id])
        return leaves

    def get_edge_type(self, from_id: str, to_id: str) -> Optional[EdgeType]:
        """Get the type of edge between two nodes"""
        if self.graph.has_edge(from_id, to_id):
            edge_data = self.graph.get_edge_data(from_id, to_id)
            return EdgeType(edge_data["edge_type"])
        return None

    def get_all_edges(self) -> List[Tuple[str, str, EdgeType]]:
        """Get all edges in the graph"""
        edges = []
        for from_id, to_id, data in self.graph.edges(data=True):
            edge_type = EdgeType(data["edge_type"])
            edges.append((from_id, to_id, edge_type))
        return edges

    def node_count(self) -> int:
        """Get total number of nodes"""
        return len(self.nodes)

    def edge_count(self) -> int:
        """Get total number of edges"""
        return self.graph.number_of_edges()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert graph to dictionary for serialization

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [
                {
                    "from": from_id,
                    "to": to_id,
                    "type": data["edge_type"],
                    "metadata": {k: v for k, v in data.items() if k != "edge_type"},
                }
                for from_id, to_id, data in self.graph.edges(data=True)
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyGraph":
        """
        Create graph from dictionary

        Args:
            data: Dictionary representation (from to_dict())

        Returns:
            DependencyGraph instance
        """
        graph = cls()

        # Add nodes
        for node_data in data["nodes"]:
            node = DependencyNode.from_dict(node_data)
            graph.add_node(node)

        # Add edges
        for edge_data in data["edges"]:
            edge_type = EdgeType(edge_data["type"])
            graph.add_edge(
                edge_data["from"], edge_data["to"], edge_type, edge_data.get("metadata")
            )

        return graph

    def __str__(self) -> str:
        """String representation of the graph"""
        return (
            f"DependencyGraph(nodes={self.node_count()}, "
            f"edges={self.edge_count()}, "
            f"has_cycles={self.has_cycles()})"
        )

    def __repr__(self) -> str:
        return self.__str__()
