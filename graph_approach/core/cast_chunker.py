"""
cAST Chunker - Chunking via Abstract Syntax Trees

Implements the cAST algorithm adapted for SAS AST. Recursively walks AST nodes,
greedily merging small nodes and recursively splitting oversized ones at
syntactic boundaries.

Based on the cAST research (CMU/Augment Code) which improves Recall@5 by +4.3
and Pass@1 by +2.67 over fixed-size chunking.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from graph_approach.ast.sas_ast import (
    SASASTParser,
    ASTNode,
    ProgramNode,
    DataStepNode,
    ProcNode,
    MacroNode,
    IfStatementNode,
    DoLoopNode,
    ProcStatementNode,
    ProcSQLStatementNode,
)


@dataclass
class CASTConfig:
    """Configuration for cAST chunking"""
    max_chunk_size: int = 4500   # Non-whitespace chars (~1500 tokens)
    min_chunk_size: int = 300    # Non-whitespace chars (~100 tokens)


@dataclass
class SASTChunk:
    """A chunk produced by the cAST algorithm"""
    source_code: str
    ast_nodes: List[ASTNode] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    size: int = 0                # Non-whitespace character count
    node_types: List[str] = field(default_factory=list)
    context_header: str = ""     # Enclosing construct header for sub-chunks
    part_index: int = 0          # 0-based index within parent split
    total_parts: int = 1         # Total parts from parent split
    parent_node_type: str = ""   # Type of the node that was split

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_code": self.source_code,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "size": self.size,
            "node_types": self.node_types,
            "context_header": self.context_header,
            "part_index": self.part_index,
            "total_parts": self.total_parts,
            "parent_node_type": self.parent_node_type,
        }


class CASTChunker:
    """
    cAST algorithm adapted for SAS code.

    The algorithm:
    1. Parse SAS code into an AST
    2. Walk the AST recursively
    3. At each level, greedily merge small sibling nodes into chunks
    4. If a node exceeds max_chunk_size, recurse into its children
    5. If a leaf node exceeds max_chunk_size, return it as-is (can't split further)
    """

    def __init__(self, config: Optional[CASTConfig] = None):
        self.config = config or CASTConfig()

    def chunk_code(self, code: str) -> List[SASTChunk]:
        """
        Parse SAS code and produce cAST-based chunks.

        Args:
            code: SAS source code

        Returns:
            List of SASTChunk objects
        """
        source_lines = code.split('\n')

        try:
            parser = SASASTParser(code)
            program = parser.parse()
        except Exception:
            # If parsing fails, return entire code as a single chunk
            return [SASTChunk(
                source_code=code,
                line_start=1,
                line_end=len(source_lines),
                size=self._get_size(code),
                node_types=["UNPARSEABLE"],
            )]

        children = self._get_children(program)
        if not children:
            return [SASTChunk(
                source_code=code,
                line_start=1,
                line_end=len(source_lines),
                size=self._get_size(code),
                node_types=["PROGRAM"],
            )]

        return self._chunk_nodes(children, source_lines, depth=0)

    def chunk_node(self, node: ASTNode, source_lines: List[str]) -> List[SASTChunk]:
        """
        Chunk a single AST node (used by ChunkOptimizer for single-node splitting).

        Args:
            node: AST node to chunk
            source_lines: Full source lines for extraction

        Returns:
            List of SASTChunk objects
        """
        children = self._get_children(node)
        node_source = self._extract_source(node, source_lines)
        node_size = self._get_size(node_source)

        if node_size <= self.config.max_chunk_size or not children:
            # Fits or can't split further
            return [SASTChunk(
                source_code=node_source,
                ast_nodes=[node],
                line_start=node.line_start,
                line_end=node.line_end,
                size=node_size,
                node_types=[node.node_type.name],
            )]

        # Build context header from the node's opening line(s)
        context_header = self._build_context_header(node, source_lines)

        # Recurse into children
        sub_chunks = self._chunk_nodes(children, source_lines, depth=1, context_header=context_header)

        # Tag sub-chunks with parent info
        parent_type = node.node_type.name
        for i, chunk in enumerate(sub_chunks):
            chunk.context_header = context_header
            chunk.part_index = i
            chunk.total_parts = len(sub_chunks)
            chunk.parent_node_type = parent_type

        return sub_chunks

    def _chunk_nodes(
        self,
        nodes: List[ASTNode],
        source_lines: List[str],
        depth: int,
        context_header: str = ""
    ) -> List[SASTChunk]:
        """
        Core cAST recursive algorithm.

        Greedy merge: accumulate consecutive small nodes into one chunk.
        Recursive split: if a single node is too large, recurse into its children.
        """
        chunks: List[SASTChunk] = []
        accumulator_nodes: List[ASTNode] = []
        accumulator_size: int = 0

        for node in nodes:
            node_source = self._extract_source(node, source_lines)
            node_size = self._get_size(node_source)

            if node_size > self.config.max_chunk_size:
                # Flush accumulator first
                if accumulator_nodes:
                    chunks.append(self._merge_nodes_to_chunk(
                        accumulator_nodes, source_lines, context_header
                    ))
                    accumulator_nodes = []
                    accumulator_size = 0

                # Try to split this oversized node by recursing into children
                children = self._get_children(node)
                if children:
                    node_header = self._build_context_header(node, source_lines)
                    combined_header = context_header
                    if node_header:
                        combined_header = f"{context_header}\n{node_header}" if context_header else node_header

                    sub_chunks = self._chunk_nodes(children, source_lines, depth + 1, combined_header)
                    chunks.extend(sub_chunks)
                else:
                    # Leaf node that's too big - can't split further, return as-is
                    chunks.append(SASTChunk(
                        source_code=node_source,
                        ast_nodes=[node],
                        line_start=node.line_start,
                        line_end=node.line_end,
                        size=node_size,
                        node_types=[node.node_type.name],
                        context_header=context_header,
                    ))
            elif accumulator_size + node_size > self.config.max_chunk_size:
                # Adding this node would exceed limit - flush accumulator
                if accumulator_nodes:
                    chunks.append(self._merge_nodes_to_chunk(
                        accumulator_nodes, source_lines, context_header
                    ))
                # Start new accumulator with this node
                accumulator_nodes = [node]
                accumulator_size = node_size
            else:
                # Greedily merge: add to accumulator
                accumulator_nodes.append(node)
                accumulator_size += node_size

        # Flush remaining accumulator
        if accumulator_nodes:
            chunks.append(self._merge_nodes_to_chunk(
                accumulator_nodes, source_lines, context_header
            ))

        # Post-pass: merge trailing tiny chunks into predecessor
        chunks = self._merge_tiny_trailing(chunks)

        return chunks

    def _merge_nodes_to_chunk(
        self,
        nodes: List[ASTNode],
        source_lines: List[str],
        context_header: str = ""
    ) -> SASTChunk:
        """Merge a list of AST nodes into a single SASTChunk."""
        if not nodes:
            return SASTChunk(source_code="", size=0)

        line_start = min(n.line_start for n in nodes)
        line_end = max(n.line_end for n in nodes)

        # Extract source spanning all nodes (inclusive line range)
        source = self._extract_lines(source_lines, line_start, line_end)

        return SASTChunk(
            source_code=source,
            ast_nodes=list(nodes),
            line_start=line_start,
            line_end=line_end,
            size=self._get_size(source),
            node_types=[n.node_type.name for n in nodes],
            context_header=context_header,
        )

    def _merge_tiny_trailing(self, chunks: List[SASTChunk]) -> List[SASTChunk]:
        """Merge chunks that are below min_chunk_size into adjacent chunks."""
        if len(chunks) <= 1:
            return chunks

        merged: List[SASTChunk] = []

        for chunk in chunks:
            if (merged and chunk.size < self.config.min_chunk_size
                    and merged[-1].size + chunk.size <= self.config.max_chunk_size):
                # Merge into previous chunk
                prev = merged[-1]
                combined_source = prev.source_code + "\n" + chunk.source_code
                merged[-1] = SASTChunk(
                    source_code=combined_source,
                    ast_nodes=prev.ast_nodes + chunk.ast_nodes,
                    line_start=prev.line_start,
                    line_end=max(prev.line_end, chunk.line_end),
                    size=self._get_size(combined_source),
                    node_types=prev.node_types + chunk.node_types,
                    context_header=prev.context_header or chunk.context_header,
                )
            else:
                merged.append(chunk)

        return merged

    def _get_children(self, node: ASTNode) -> List[ASTNode]:
        """
        SAS-specific child accessor mapping.

        Each node type has its own way of storing children.
        """
        if isinstance(node, ProgramNode):
            return list(node.children)  # DATA steps, PROCs, macros, globals
        elif isinstance(node, DataStepNode):
            return list(node.statements)
        elif isinstance(node, ProcNode):
            return list(node.statements)
        elif isinstance(node, MacroNode):
            return list(node.body)
        elif isinstance(node, IfStatementNode):
            return list(node.then_branch) + list(node.else_branch)
        elif isinstance(node, DoLoopNode):
            return list(node.body)
        elif hasattr(node, 'children') and node.children:
            return list(node.children)
        return []

    @staticmethod
    def _get_size(code: str) -> int:
        """
        Non-whitespace character count (per cAST paper).

        This metric is more stable than raw char count since indentation
        differences don't affect the size.
        """
        return sum(1 for c in code if not c.isspace())

    @staticmethod
    def _extract_source(node: ASTNode, source_lines: List[str]) -> str:
        """Extract source code using line_start/line_end."""
        if node.line_start <= 0 or node.line_end <= 0:
            return ""

        start = max(0, node.line_start - 1)  # Convert to 0-based
        end = min(len(source_lines), node.line_end)
        return '\n'.join(source_lines[start:end])

    @staticmethod
    def _extract_lines(source_lines: List[str], line_start: int, line_end: int) -> str:
        """Extract a range of lines (1-based, inclusive)."""
        start = max(0, line_start - 1)
        end = min(len(source_lines), line_end)
        return '\n'.join(source_lines[start:end])

    @staticmethod
    def _build_context_header(node: ASTNode, source_lines: List[str]) -> str:
        """
        Build a context header for sub-chunks of a split node.

        Captures the opening statement(s) of the enclosing construct so the
        LLM knows what context the sub-chunk belongs to.
        """
        if isinstance(node, DataStepNode):
            datasets = ', '.join(node.output_datasets) if node.output_datasets else 'unknown'
            header = f"DATA {datasets};"
            # Add SET/MERGE statement if present
            for stmt in node.statements[:3]:
                if hasattr(stmt, 'node_type'):
                    from graph_approach.ast.sas_ast import NodeType as ASTNodeType
                    if stmt.node_type == ASTNodeType.SET_STATEMENT:
                        if hasattr(stmt, 'datasets'):
                            header += f" SET {', '.join(stmt.datasets)};"
                        break
                    elif stmt.node_type == ASTNodeType.MERGE_STATEMENT:
                        if hasattr(stmt, 'datasets'):
                            header += f" MERGE {', '.join(stmt.datasets)};"
                        break
            return header
        elif isinstance(node, ProcNode):
            return f"PROC {node.proc_name.upper()};"
        elif isinstance(node, MacroNode):
            params = ', '.join(node.parameters) if node.parameters else ''
            if params:
                return f"%MACRO {node.name}({params});"
            return f"%MACRO {node.name};"
        elif isinstance(node, DoLoopNode):
            if node.loop_var:
                return f"DO {node.loop_var} = ...;"
            return "DO;"
        elif isinstance(node, IfStatementNode):
            return "IF ... THEN DO;"

        # Fallback: first source line
        if node.line_start > 0:
            idx = node.line_start - 1
            if idx < len(source_lines):
                return source_lines[idx].strip()
        return ""
