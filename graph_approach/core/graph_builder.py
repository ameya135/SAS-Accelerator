"""
Graph Builder

Builds a dependency graph from parsed SAS code by combining
the SAS parser output with dependency extraction.
"""

import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path

_repo_root = Path(__file__).parent.parent.parent


def _load_external_sas_parser():
    """Load optional external SASParser without mutating process import paths."""
    try:
        from parser.sas_code_parser import SASParser as parser_cls

        return parser_cls
    except ImportError:
        parser_path = _repo_root / "parser" / "sas_code_parser.py"
        if not parser_path.exists():
            return None

        spec = importlib.util.spec_from_file_location(
            "_sas_accelerator_external_parser", parser_path
        )
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except ImportError:
            return None
        return getattr(module, "SASParser", None)


SASParser = _load_external_sas_parser()

SAS_PARSER_AVAILABLE = SASParser is not None
from graph_approach.parsers.dependency_extractor import DependencyExtractor
from graph_approach.parsers.ast_parsed_sas_bridge import program_to_parsed_sas_dict
from graph_approach.core.dependency_graph import (
    DependencyGraph,
    DependencyNode,
    NodeType,
    EdgeType,
)


class GraphBuilder:
    """
    Build a dependency graph from SAS code

    This class orchestrates parsing SAS code, extracting dependencies,
    and constructing a complete dependency graph.
    """

    def __init__(
        self,
        sas_code: Optional[str] = None,
        parsed_sas: Optional[Dict] = None,
        parser: Optional[Any] = None,
        dep_extractor: Optional[Any] = None,
    ):
        """
        Initialize graph builder

        Args:
            sas_code: Raw SAS code to parse (optional if parsed_sas provided)
            parsed_sas: Pre-parsed SAS structure (optional if sas_code provided)
            parser: Optional SASParser instance (defaults to creating one)
            dep_extractor: Optional DependencyExtractor instance (defaults to creating one)
        """
        self.sas_code = sas_code
        if parser is not None:
            self.parser = parser
        elif SAS_PARSER_AVAILABLE:
            self.parser = SASParser()
        else:
            self.parser = None
        self.dep_extractor = dep_extractor or DependencyExtractor()

        if parsed_sas:
            self.parsed_sas = parsed_sas
        elif sas_code:
            if self.parser is not None:
                self.parsed_sas = self.parser.parse_content(sas_code)
            else:
                try:
                    self.parsed_sas = program_to_parsed_sas_dict(sas_code)
                except Exception as exc:
                    raise RuntimeError(
                        "SAS parsing failed: the external sas_code_parser package is not "
                        "installed, and the built-in AST parser could not parse this program. "
                        "Install/configure sas_code_parser, fix the SAS syntax for the "
                        "built-in parser, or pass parsed_sas= with a pre-parsed structure. "
                        f"Original error: {exc}"
                    ) from exc
        else:
            raise ValueError("Either sas_code or parsed_sas must be provided")

        self.graph = DependencyGraph()
        self._node_id_counter = 0

    def build_graph(self) -> DependencyGraph:
        """
        Build the complete dependency graph

        Returns:
            DependencyGraph with all nodes and edges
        """
        # Extract all dependencies
        dependencies = self.dep_extractor.extract_all_dependencies(self.parsed_sas)

        # Add library and file reference nodes first
        self._add_library_nodes()
        self._add_file_nodes()

        # Add macro nodes and dependencies
        self._add_macro_nodes(dependencies["macros"])

        # Add dataset nodes from DATA steps
        self._add_data_step_nodes(dependencies["data_steps"])

        # Add PROC nodes and dataset dependencies
        self._add_proc_nodes(dependencies["proc_steps"])

        # Add cross-references (macro calls, variable usage, etc.)
        self._add_cross_references(dependencies)

        return self.graph

    def _generate_node_id(self, prefix: str = "node") -> str:
        """Generate unique node ID"""
        self._node_id_counter += 1
        return f"{prefix}_{self._node_id_counter}"

    def _add_library_nodes(self) -> None:
        """Add library reference nodes from LIBNAME statements"""
        if not self.sas_code:
            return

        libraries = self.dep_extractor.extract_library_references(self.sas_code)
        for lib in libraries:
            node = DependencyNode(
                node_id=self._generate_node_id("lib"),
                node_type=NodeType.LIBRARY,
                name=lib["libref"],
                metadata={"path": lib["path"]},
            )
            self.graph.add_node(node)

    def _add_file_nodes(self) -> None:
        """Add file reference nodes from FILENAME statements"""
        if not self.sas_code:
            return

        file_refs = self.dep_extractor.extract_filename_references(self.sas_code)
        for fref in file_refs:
            node = DependencyNode(
                node_id=self._generate_node_id("file"),
                node_type=NodeType.FILE_REF,
                name=fref["fileref"],
                metadata={"path": fref["path"]},
            )
            self.graph.add_node(node)

    def _add_macro_nodes(self, macro_deps: List[Dict]) -> None:
        """
        Add macro definition nodes and their dependencies

        Args:
            macro_deps: List of macros with dependencies
        """
        # First pass: create macro nodes
        for item in macro_deps:
            macro = item["macro"]
            deps = item["dependencies"]

            node = DependencyNode(
                node_id=self._generate_node_id("macro"),
                node_type=NodeType.MACRO,
                name=deps.macro_name or macro.get("name", ""),
                source_code=macro.get("source_code") or macro.get("body", ""),
                metadata={
                    "parameters": macro.get("parameters", []),
                    "nesting_level": macro.get("nesting_level", 0),
                },
                line_start=macro.get("start_line", 0),
                line_end=macro.get("end_line", 0),
            )
            self.graph.add_node(node)

        # Second pass: add macro variable nodes and edges
        for item in macro_deps:
            macro = item["macro"]
            deps = item["dependencies"]
            macro_name = deps.macro_name or macro.get("name", "")

            # Find this macro's node
            macro_node = self._find_node_by_name(macro_name, NodeType.MACRO)
            if not macro_node:
                continue

            # Add macro variable definition nodes
            for var in deps.macro_vars_defined:
                var_node = self._find_or_create_macro_variable_node(var)
                # Macro defines this variable
                self.graph.add_edge(
                    macro_node.node_id, var_node.node_id, EdgeType.DEFINES_VARIABLE
                )

            # Add edges for macro variables used
            for var in deps.macro_vars_used:
                var_node = self._find_or_create_macro_variable_node(var)
                # Macro uses this variable
                self.graph.add_edge(
                    var_node.node_id, macro_node.node_id, EdgeType.USES_VARIABLE
                )

    def _add_data_step_nodes(self, data_step_deps: List[Dict]) -> None:
        """
        Add DATA step nodes and dataset dependencies

        Args:
            data_step_deps: List of DATA steps with dependencies
        """
        for item in data_step_deps:
            data_step = item["step"]
            deps = item["dependencies"]

            # Create DATA step node
            step_node = DependencyNode(
                node_id=self._generate_node_id("data_step"),
                node_type=NodeType.DATA_STEP,
                name=f"DATA_{data_step.get('start_line', 0)}",
                source_code=data_step.get("source_code") or data_step.get("body", ""),
                metadata={"outputs": deps.outputs, "inputs": deps.inputs},
                line_start=data_step.get("start_line", 0),
                line_end=data_step.get("end_line", 0),
            )
            self.graph.add_node(step_node)

            # Create or find output dataset nodes
            for dataset_name in deps.outputs:
                dataset_node = self._find_or_create_dataset_node(dataset_name)
                # DATA step writes to dataset
                self.graph.add_edge(
                    step_node.node_id, dataset_node.node_id, EdgeType.WRITES_TO
                )

            # Add edges for input datasets
            for dataset_name in deps.inputs:
                dataset_node = self._find_or_create_dataset_node(dataset_name)
                # DATA step reads from dataset
                self.graph.add_edge(
                    dataset_node.node_id, step_node.node_id, EdgeType.READS_FROM
                )

            # Add edges for macro variables used
            for var in deps.macro_vars_used:
                var_node = self._find_or_create_macro_variable_node(var)
                self.graph.add_edge(
                    var_node.node_id, step_node.node_id, EdgeType.USES_VARIABLE
                )

            # Add edges for macro variables defined
            for var in deps.macro_vars_defined:
                var_node = self._find_or_create_macro_variable_node(var)
                self.graph.add_edge(
                    step_node.node_id, var_node.node_id, EdgeType.DEFINES_VARIABLE
                )

            # Add edges for file references
            for file_ref in deps.file_refs:
                file_node = self._find_node_by_name(file_ref, NodeType.FILE_REF)
                if file_node:
                    self.graph.add_edge(
                        file_node.node_id, step_node.node_id, EdgeType.DEPENDS_ON_FILE
                    )

    def _add_proc_nodes(self, proc_deps: List[Dict]) -> None:
        """
        Add PROC nodes and their dependencies

        Args:
            proc_deps: List of PROCs with dependencies
        """
        for item in proc_deps:
            proc_step = item["step"]
            deps = item["dependencies"]

            # Create PROC node
            proc_node = DependencyNode(
                node_id=self._generate_node_id("proc"),
                node_type=NodeType.PROC,
                name=f"PROC_{deps.proc_name}_{proc_step.get('start_line', 0)}",
                source_code=proc_step.get("source_code") or proc_step.get("body", ""),
                metadata={
                    "proc_name": deps.proc_name,
                    "options": proc_step.get("options", ""),
                    "inputs": deps.inputs,
                    "outputs": deps.outputs,
                },
                line_start=proc_step.get("start_line", 0),
                line_end=proc_step.get("end_line", 0),
            )
            self.graph.add_node(proc_node)

            # Add edges for input datasets
            for dataset_name in deps.inputs:
                dataset_node = self._find_or_create_dataset_node(dataset_name)
                # PROC reads from dataset
                self.graph.add_edge(
                    dataset_node.node_id, proc_node.node_id, EdgeType.PROC_INPUT
                )

            # Add edges for output datasets
            for dataset_name in deps.outputs:
                dataset_node = self._find_or_create_dataset_node(dataset_name)
                # PROC creates dataset
                self.graph.add_edge(
                    proc_node.node_id, dataset_node.node_id, EdgeType.PROC_OUTPUT
                )

            # Add edges for macro variables used
            for var in deps.macro_vars_used:
                var_node = self._find_or_create_macro_variable_node(var)
                self.graph.add_edge(
                    var_node.node_id, proc_node.node_id, EdgeType.USES_VARIABLE
                )

            # Add edges for file references
            for file_ref in deps.file_refs:
                file_node = self._find_node_by_name(file_ref, NodeType.FILE_REF)
                if file_node:
                    self.graph.add_edge(
                        file_node.node_id, proc_node.node_id, EdgeType.DEPENDS_ON_FILE
                    )

    def _add_cross_references(self, dependencies: Dict[str, Any]) -> None:
        """
        Add cross-references like macro calls

        Args:
            dependencies: All extracted dependencies
        """
        # Add macro call edges
        for item in dependencies["macros"]:
            macro = item["macro"]
            deps = item["dependencies"]
            macro_name = deps.macro_name or macro.get("name", "")

            caller_node = self._find_node_by_name(macro_name, NodeType.MACRO)
            if not caller_node:
                continue

            # Add edges for called macros
            for called_macro in deps.calls:
                called_node = self._find_node_by_name(called_macro, NodeType.MACRO)
                if called_node:
                    self.graph.add_edge(
                        caller_node.node_id, called_node.node_id, EdgeType.CALLS
                    )

    def _find_node_by_name(
        self, name: str, node_type: NodeType
    ) -> Optional[DependencyNode]:
        """Find a node by name and type"""
        nodes = self.graph.get_nodes_by_type(node_type)
        for node in nodes:
            if node.name.lower() == name.lower():
                return node
        return None

    def _find_or_create_dataset_node(self, dataset_name: str) -> DependencyNode:
        """Find or create a dataset node"""
        # Check if dataset node already exists
        existing = self._find_node_by_name(dataset_name, NodeType.DATASET)
        if existing:
            return existing

        # Create new dataset node
        node = DependencyNode(
            node_id=self._generate_node_id("dataset"),
            node_type=NodeType.DATASET,
            name=dataset_name,
            metadata={"created_implicitly": True},
        )
        self.graph.add_node(node)
        return node

    def _find_or_create_macro_variable_node(self, var_name: str) -> DependencyNode:
        """Find or create a macro variable node"""
        # Check if variable node already exists
        existing = self._find_node_by_name(var_name, NodeType.MACRO_VARIABLE)
        if existing:
            return existing

        # Create new variable node
        node = DependencyNode(
            node_id=self._generate_node_id("var"),
            node_type=NodeType.MACRO_VARIABLE,
            name=var_name,
            metadata={"created_implicitly": True},
        )
        self.graph.add_node(node)
        return node

    @classmethod
    def from_file(cls, file_path: str) -> "GraphBuilder":
        """
        Create GraphBuilder from a SAS file

        Args:
            file_path: Path to SAS file

        Returns:
            GraphBuilder instance
        """
        with open(file_path, "r", encoding="utf-8") as f:
            sas_code = f.read()
        return cls(sas_code=sas_code)

    def get_execution_order(self) -> List[DependencyNode]:
        """
        Get nodes in execution order (topological sort)

        Returns:
            List of nodes in dependency order
        """
        try:
            return self.graph.topological_sort()
        except ValueError as e:
            # Handle cycles
            cycles = self.graph.find_cycles()
            raise ValueError(
                f"Cannot determine execution order due to cycles: {cycles}"
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the graph

        Returns:
            Dictionary with graph statistics
        """
        return {
            "total_nodes": self.graph.node_count(),
            "total_edges": self.graph.edge_count(),
            "has_cycles": self.graph.has_cycles(),
            "node_counts_by_type": {
                nt.value: len(self.graph.get_nodes_by_type(nt)) for nt in NodeType
            },
            "root_nodes": len(self.graph.get_root_nodes()),
            "leaf_nodes": len(self.graph.get_leaf_nodes()),
        }
