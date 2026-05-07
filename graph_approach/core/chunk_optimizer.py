"""
Chunk Optimizer

Generates optimal code chunks from dependency graph for migration.
Groups related code, respects dependencies, and optimizes chunk sizes.
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from graph_approach.core.dependency_graph import DependencyGraph, DependencyNode, NodeType
from graph_approach.core.cast_chunker import CASTChunker, CASTConfig, SASTChunk


@dataclass
class Chunk:
    """
    A chunk of SAS code to be migrated

    Attributes:
        chunk_id: Unique identifier
        nodes: List of graph nodes in this chunk
        dependencies: IDs of chunks this depends on
        source_code: Combined source code
        context: Context information for LLM
        estimated_tokens: Estimated token count
        layer: Execution layer (for parallel processing)
    """
    chunk_id: str
    nodes: List[DependencyNode] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Chunk IDs
    source_code: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 0
    layer: int = 0

    def add_node(self, node: DependencyNode) -> None:
        """Add a node to this chunk"""
        self.nodes.append(node)
        if node.source_code:
            if self.source_code:
                self.source_code += "\n\n"
            self.source_code += node.source_code
        # Token estimation using non-whitespace chars / 3 (more accurate)
        non_ws = sum(1 for c in self.source_code if not c.isspace())
        self.estimated_tokens = non_ws // 3

    def get_node_ids(self) -> List[str]:
        """Get all node IDs in this chunk"""
        return [n.node_id for n in self.nodes]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "dependencies": self.dependencies,
            "source_code": self.source_code,
            "estimated_tokens": self.estimated_tokens,
            "layer": self.layer,
            "context": self.context
        }


class ChunkOptimizer:
    """
    Generate optimal chunks from dependency graph

    Strategies:
    1. Respect dependency order (via execution layers)
    2. Group related nodes (macro + calls, data step + datasets)
    3. Optimize chunk sizes (merge small, split large)
    4. Balance token usage
    """

    def __init__(
        self,
        graph: DependencyGraph,
        min_chunk_tokens: int = 100,
        max_chunk_tokens: int = 2000,
        target_chunk_tokens: int = 1000
    ):
        """
        Initialize chunk optimizer

        Args:
            graph: Dependency graph to chunk
            min_chunk_tokens: Minimum chunk size (will merge smaller)
            max_chunk_tokens: Maximum chunk size (will split larger)
            target_chunk_tokens: Target chunk size for optimization
        """
        self.graph = graph
        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.target_chunk_tokens = target_chunk_tokens
        self._chunk_counter = 0
        self._cast_split_count = 0
        self._cast_subchunk_count = 0

        # Initialize cAST chunker with matching token limits
        # Convert token limits to non-whitespace char estimates (~3 chars/token)
        self.cast_chunker = CASTChunker(CASTConfig(
            max_chunk_size=max_chunk_tokens * 3,
            min_chunk_size=min_chunk_tokens * 3,
        ))

    def generate_chunks(self) -> List[Chunk]:
        """
        Generate optimized chunks from graph

        Returns:
            List of chunks in dependency order
        """
        # Handle cycles by breaking them intelligently
        if self.graph.has_cycles():
            print("  ⚠ Warning: Cycles detected in dependency graph")
            print("  Breaking cycles intelligently...")
            broken_edges = self.graph.break_cycles()

            if broken_edges:
                print(f"  Broke {len(broken_edges)} edge(s) to resolve cycles:")
                for from_id, to_id, edge_type in broken_edges:
                    from_node = self.graph.nodes.get(from_id)
                    to_node = self.graph.nodes.get(to_id)
                    from_name = from_node.name if from_node else from_id
                    to_name = to_node.name if to_node else to_id
                    print(f"    - {from_name} --[{edge_type.value}]--> {to_name}")

        # Get execution layers
        layers = self.graph.get_execution_layers()

        # Create initial chunks from layers
        chunks = self._create_chunks_from_layers(layers)

        # Optimize chunk sizes
        chunks = self._optimize_chunk_sizes(chunks)

        # Add dependencies between chunks
        self._add_chunk_dependencies(chunks)

        # Add context information
        self._enrich_chunk_context(chunks)

        return chunks

    def _create_chunks_from_layers(self, layers: List[List[DependencyNode]]) -> List[Chunk]:
        """
        Create initial chunks from execution layers

        Args:
            layers: Execution layers from graph

        Returns:
            List of chunks
        """
        chunks = []

        for layer_idx, layer_nodes in enumerate(layers):
            # Group nodes by type and relationships
            node_groups = self._group_related_nodes(layer_nodes)

            for group in node_groups:
                chunk = Chunk(
                    chunk_id=self._generate_chunk_id(),
                    layer=layer_idx
                )
                for node in group:
                    chunk.add_node(node)
                if chunk.source_code.strip():
                    chunks.append(chunk)

        return chunks

    def _group_related_nodes(self, nodes: List[DependencyNode]) -> List[List[DependencyNode]]:
        """
        Group related nodes together

        Strategies:
        - Macro definitions with macro variables they define
        - DATA steps with their output datasets
        - PROCs with their output datasets
        - Keep small groups together

        Args:
            nodes: List of nodes to group

        Returns:
            List of node groups
        """
        groups = []
        processed = set()
        layer_node_ids = {node.node_id for node in nodes}

        for node in nodes:
            if node.node_id in processed:
                continue

            group = [node]
            processed.add(node.node_id)

            # Add closely related nodes
            if node.node_type == NodeType.MACRO:
                # Group macro with variables it defines
                dependents = self.graph.get_dependents(node.node_id, depth=1)
                for dep in dependents:
                    if (
                        dep.node_type == NodeType.MACRO_VARIABLE
                        and dep.node_id in layer_node_ids
                        and dep.node_id not in processed
                    ):
                        group.append(dep)
                        processed.add(dep.node_id)

            elif node.node_type == NodeType.DATA_STEP:
                # Group DATA step with output datasets (if small)
                dependents = self.graph.get_dependents(node.node_id, depth=1)
                for dep in dependents:
                    if (
                        dep.node_type == NodeType.DATASET
                        and dep.node_id in layer_node_ids
                        and dep.node_id not in processed
                    ):
                        group.append(dep)
                        processed.add(dep.node_id)

            elif node.node_type == NodeType.PROC:
                # Group PROC with output datasets
                dependents = self.graph.get_dependents(node.node_id, depth=1)
                for dep in dependents:
                    if (
                        dep.node_type == NodeType.DATASET
                        and dep.node_id in layer_node_ids
                        and dep.node_id not in processed
                    ):
                        group.append(dep)
                        processed.add(dep.node_id)

            groups.append(group)

        return groups

    def _optimize_chunk_sizes(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Optimize chunk sizes by merging small chunks and splitting large ones

        Args:
            chunks: Initial chunks

        Returns:
            Optimized chunks
        """
        optimized = []

        # First pass: merge small chunks in same layer
        chunks_by_layer = {}
        for chunk in chunks:
            if chunk.layer not in chunks_by_layer:
                chunks_by_layer[chunk.layer] = []
            chunks_by_layer[chunk.layer].append(chunk)

        for layer_idx in sorted(chunks_by_layer.keys()):
            layer_chunks = chunks_by_layer[layer_idx]
            merged = self._merge_small_chunks(layer_chunks)
            optimized.extend(merged)

        # Second pass: split large chunks
        final_chunks = []
        for chunk in optimized:
            if chunk.estimated_tokens > self.max_chunk_tokens:
                split_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(split_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Merge small chunks in the same layer

        Args:
            chunks: Chunks in the same layer

        Returns:
            Merged chunks
        """
        if not chunks:
            return []

        merged = []
        current_chunk = None

        for chunk in sorted(chunks, key=lambda c: c.estimated_tokens):
            if current_chunk is None:
                current_chunk = chunk
            elif (current_chunk.estimated_tokens < self.min_chunk_tokens and
                  current_chunk.estimated_tokens + chunk.estimated_tokens <= self.target_chunk_tokens):
                # Merge into current chunk
                for node in chunk.nodes:
                    current_chunk.add_node(node)
                current_chunk.layer = chunk.layer
            else:
                merged.append(current_chunk)
                current_chunk = chunk

        if current_chunk:
            merged.append(current_chunk)

        return merged

    def _split_large_chunk(self, chunk: Chunk) -> List[Chunk]:
        """
        Split a large chunk into smaller ones using cAST for single-node chunks.

        Multi-node chunks: split at node boundaries (improved from original).
        Single-node chunks: delegate to CASTChunker for AST-aware splitting.

        Args:
            chunk: Large chunk to split

        Returns:
            List of smaller chunks
        """
        if len(chunk.nodes) > 1:
            # Multi-node: split at node boundaries, respecting target size
            split_chunks = []
            current = Chunk(chunk_id=self._generate_chunk_id(), layer=chunk.layer)
            for node in chunk.nodes:
                current.add_node(node)
                if current.estimated_tokens >= self.target_chunk_tokens:
                    split_chunks.append(current)
                    current = Chunk(chunk_id=self._generate_chunk_id(), layer=chunk.layer)
            if current.nodes:
                split_chunks.append(current)
            return split_chunks if split_chunks else [chunk]

        # Single-node: use cAST to split at syntactic boundaries
        node = chunk.nodes[0]
        if not node.source_code:
            return [chunk]

        cast_chunks = self.cast_chunker.chunk_code(node.source_code)

        if len(cast_chunks) <= 1:
            # cAST couldn't split further, return as-is
            return [chunk]

        # Track cAST splitting stats
        self._cast_split_count += 1
        self._cast_subchunk_count += len(cast_chunks)

        # Create new DependencyNode + Chunk for each cAST sub-chunk
        split_chunks = []
        parent_node_id = node.node_id

        for i, cast_chunk in enumerate(cast_chunks):
            sub_node = DependencyNode(
                node_id=f"{parent_node_id}_cast_{i}",
                node_type=node.node_type,
                name=f"{node.name}_part{i+1}",
                source_code=cast_chunk.source_code,
                metadata={
                    **node.metadata,
                    'cast_split': True,
                    'parent_node_id': parent_node_id,
                    'part_index': i,
                    'total_parts': len(cast_chunks),
                    'context_header': cast_chunk.context_header,
                    'cast_node_types': cast_chunk.node_types,
                },
                line_start=cast_chunk.line_start + node.line_start - 1,
                line_end=cast_chunk.line_end + node.line_start - 1,
            )

            new_chunk = Chunk(
                chunk_id=self._generate_chunk_id(),
                layer=chunk.layer
            )
            new_chunk.add_node(sub_node)
            split_chunks.append(new_chunk)

        return split_chunks

    def get_cast_stats(self) -> Dict[str, int]:
        """Get cAST splitting statistics"""
        return {
            "nodes_split_by_cast": self._cast_split_count,
            "subchunks_created": self._cast_subchunk_count,
        }

    def _add_chunk_dependencies(self, chunks: List[Chunk]) -> None:
        """
        Add dependencies between chunks

        Args:
            chunks: List of chunks
        """
        # Build map of node_id -> chunk_id
        node_to_chunk = {}
        for chunk in chunks:
            for node in chunk.nodes:
                node_to_chunk[node.node_id] = chunk.chunk_id

        # For each chunk, find which other chunks it depends on
        for chunk in chunks:
            chunk_deps = set()

            for node in chunk.nodes:
                # Get node dependencies
                node_deps = self.graph.get_dependencies(node.node_id, depth=1)

                for dep_node in node_deps:
                    dep_chunk_id = node_to_chunk.get(dep_node.node_id)
                    if dep_chunk_id and dep_chunk_id != chunk.chunk_id:
                        chunk_deps.add(dep_chunk_id)

            chunk.dependencies = list(chunk_deps)

    def _enrich_chunk_context(self, chunks: List[Chunk]) -> None:
        """
        Add context information to each chunk

        Args:
            chunks: List of chunks
        """
        for chunk in chunks:
            context = {
                "layer": chunk.layer,
                "node_types": [n.node_type.value for n in chunk.nodes],
                "node_names": [n.name for n in chunk.nodes],
                "has_macros": any(n.node_type == NodeType.MACRO for n in chunk.nodes),
                "has_data_steps": any(n.node_type == NodeType.DATA_STEP for n in chunk.nodes),
                "has_procs": any(n.node_type == NodeType.PROC for n in chunk.nodes),
                "dependency_count": len(chunk.dependencies)
            }

            # Add metadata from nodes
            for node in chunk.nodes:
                if node.metadata:
                    context[f"{node.node_type.value}_{node.name}_metadata"] = node.metadata

            chunk.context = context

    def _generate_chunk_id(self) -> str:
        """Generate unique chunk ID"""
        self._chunk_counter += 1
        return f"chunk_{self._chunk_counter:03d}"

    def get_chunk_summary(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Get summary statistics about chunks

        Args:
            chunks: List of chunks

        Returns:
            Summary dictionary
        """
        total_tokens = sum(c.estimated_tokens for c in chunks)
        avg_tokens = total_tokens / len(chunks) if chunks else 0

        return {
            "total_chunks": len(chunks),
            "total_tokens": total_tokens,
            "avg_tokens_per_chunk": avg_tokens,
            "min_tokens": min((c.estimated_tokens for c in chunks), default=0),
            "max_tokens": max((c.estimated_tokens for c in chunks), default=0),
            "chunks_by_layer": self._count_chunks_by_layer(chunks),
            "chunks_with_dependencies": sum(1 for c in chunks if c.dependencies)
        }

    def _count_chunks_by_layer(self, chunks: List[Chunk]) -> Dict[int, int]:
        """Count chunks per layer"""
        layer_counts = {}
        for chunk in chunks:
            layer = chunk.layer
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        return layer_counts
