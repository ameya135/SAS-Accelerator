"""
Tests for dependency graph core functionality

Covers DependencyNode and DependencyGraph classes including:
- Node creation, serialization, equality, hashing
- Graph construction (add_node, add_edge)
- Dependency traversal (get_dependencies, get_dependents)
- Topological sort and cycle detection
- Execution layers, subgraphs, root/leaf nodes
- Serialization round-trips
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from graph_approach.core.dependency_graph import (
    DependencyGraph,
    DependencyNode,
    NodeType,
    EdgeType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_linear_chain(graph: DependencyGraph, n: int = 3):
    """Build a linear chain of n DATA_STEP nodes connected through DATASET nodes.

    Returns list of all node IDs: [d0, s0, d1, s1, d2, ...]
    """
    ids = []
    for i in range(n):
        d_id = f"d{i}"
        s_id = f"s{i}"
        graph.add_node(DependencyNode(d_id, NodeType.DATASET, f"dataset_{i}"))
        graph.add_node(DependencyNode(s_id, NodeType.DATA_STEP, f"step_{i}"))
        ids.extend([d_id, s_id])

        if i > 0:
            prev_d = f"d{i - 1}"
            prev_s = f"s{i - 1}"
            # previous step writes to previous dataset, which this step reads
            graph.add_edge(prev_s, prev_d, EdgeType.WRITES_TO)
            graph.add_edge(prev_d, s_id, EdgeType.READS_FROM)

    # Last step writes to last dataset
    last_s = f"s{n - 1}"
    last_d = f"d{n - 1}"
    graph.add_edge(last_s, last_d, EdgeType.WRITES_TO)

    return ids


# ===================================================================
# DependencyNode Tests
# ===================================================================


class TestDependencyNode:
    """Tests for the DependencyNode dataclass."""

    # --- Creation ---

    def test_node_creation_with_all_fields(self):
        node = DependencyNode(
            node_id="test_node",
            node_type=NodeType.DATASET,
            name="my_dataset",
            source_code="DATA my_dataset; SET input_data; RUN;",
            metadata={"key": "value"},
            line_start=1,
            line_end=3,
        )

        assert node.node_id == "test_node"
        assert node.node_type == NodeType.DATASET
        assert node.name == "my_dataset"
        assert node.source_code == "DATA my_dataset; SET input_data; RUN;"
        assert node.metadata["key"] == "value"
        assert node.line_start == 1
        assert node.line_end == 3

    def test_node_creation_defaults(self):
        """Verify default values for optional fields."""
        node = DependencyNode(node_id="n1", node_type=NodeType.PROC, name="proc1")

        assert node.source_code == ""
        assert node.metadata == {}
        assert node.line_start == 0
        assert node.line_end == 0

    # --- Equality & Hashing ---

    def test_node_equality_same_id(self):
        """Two nodes with the same node_id are equal."""
        n1 = DependencyNode("id1", NodeType.DATASET, "a")
        n2 = DependencyNode("id1", NodeType.MACRO, "b")
        assert n1 == n2

    def test_node_equality_different_id(self):
        n1 = DependencyNode("id1", NodeType.DATASET, "a")
        n2 = DependencyNode("id2", NodeType.DATASET, "a")
        assert n1 != n2

    def test_node_equality_with_non_node(self):
        node = DependencyNode("id1", NodeType.DATASET, "a")
        assert node != "id1"
        assert node != 42

    def test_node_hash_consistent_with_equality(self):
        n1 = DependencyNode("id1", NodeType.DATASET, "a")
        n2 = DependencyNode("id1", NodeType.MACRO, "b")
        assert hash(n1) == hash(n2)

        n3 = DependencyNode("id2", NodeType.DATASET, "a")
        # Different IDs may or may not hash the same; equality is what matters
        assert n1 != n3

    def test_node_usable_in_set(self):
        """Nodes with same ID collapse in a set."""
        n1 = DependencyNode("id1", NodeType.DATASET, "a")
        n2 = DependencyNode("id1", NodeType.MACRO, "b")
        assert len({n1, n2}) == 1

    # --- Serialization ---

    def test_node_to_dict_round_trip(self):
        node = DependencyNode(
            node_id="test",
            node_type=NodeType.MACRO,
            name="test_macro",
            source_code="%macro test;",
            metadata={"params": 2},
            line_start=10,
            line_end=20,
        )

        as_dict = node.to_dict()
        restored = DependencyNode.from_dict(as_dict)

        assert restored.node_id == node.node_id
        assert restored.node_type == node.node_type
        assert restored.name == node.name
        assert restored.source_code == node.source_code
        assert restored.metadata == node.metadata
        assert restored.line_start == node.line_start
        assert restored.line_end == node.line_end

    def test_node_to_dict_values(self):
        """Check that to_dict produces expected structure."""
        node = DependencyNode(
            node_id="n1",
            node_type=NodeType.LIBRARY,
            name="mylib",
        )
        d = node.to_dict()

        assert d["node_id"] == "n1"
        assert d["node_type"] == "library"
        assert d["name"] == "mylib"
        assert d["source_code"] == ""
        assert d["metadata"] == {}
        assert d["line_start"] == 0
        assert d["line_end"] == 0

    def test_node_from_dict_with_missing_optional_fields(self):
        """from_dict should handle missing optional keys gracefully."""
        data = {"node_id": "x", "node_type": "dataset", "name": "y"}
        node = DependencyNode.from_dict(data)

        assert node.node_id == "x"
        assert node.source_code == ""
        assert node.metadata == {}
        assert node.line_start == 0
        assert node.line_end == 0

    def test_node_from_dict_preserves_all_node_types(self):
        """Every NodeType enum value survives serialization."""
        for nt in NodeType:
            node = DependencyNode(node_id=f"n_{nt.value}", node_type=nt, name=nt.value)
            restored = DependencyNode.from_dict(node.to_dict())
            assert restored.node_type == nt


# ===================================================================
# DependencyGraph Tests
# ===================================================================


class TestDependencyGraphConstruction:
    """Tests for building graphs (add_node, add_edge)."""

    def test_empty_graph(self):
        graph = DependencyGraph()
        assert graph.node_count() == 0
        assert graph.edge_count() == 0
        assert not graph.has_cycles()

    def test_add_single_node(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATASET, "data1"))
        assert graph.node_count() == 1
        assert graph.edge_count() == 0

    def test_add_multiple_nodes(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATASET, "data1"))
        graph.add_node(DependencyNode("n2", NodeType.DATASET, "data2"))
        graph.add_node(DependencyNode("n3", NodeType.MACRO, "macro1"))

        assert graph.node_count() == 3

    def test_add_edge_between_nodes(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATA_STEP, "step1"))
        graph.add_node(DependencyNode("n2", NodeType.DATASET, "dataset1"))
        graph.add_edge("n1", "n2", EdgeType.WRITES_TO)

        assert graph.edge_count() == 1
        assert graph.get_edge_type("n1", "n2") == EdgeType.WRITES_TO

    def test_add_edge_with_metadata(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATASET, "d1"))
        graph.add_node(DependencyNode("n2", NodeType.DATA_STEP, "s1"))
        graph.add_edge("n1", "n2", EdgeType.READS_FROM, metadata={"label": "test"})

        assert graph.edge_count() == 1

    def test_add_edge_missing_source_raises(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n2", NodeType.DATASET, "d2"))

        with pytest.raises(ValueError, match="Source node nonexistent not found"):
            graph.add_edge("nonexistent", "n2", EdgeType.READS_FROM)

    def test_add_edge_missing_target_raises(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATASET, "d1"))

        with pytest.raises(ValueError, match="Target node nonexistent not found"):
            graph.add_edge("n1", "nonexistent", EdgeType.WRITES_TO)

    def test_add_edge_both_missing_raises(self):
        graph = DependencyGraph()
        with pytest.raises(ValueError):
            graph.add_edge("a", "b", EdgeType.CALLS)

    def test_get_node_existing(self):
        graph = DependencyGraph()
        node = DependencyNode("n1", NodeType.DATASET, "data1")
        graph.add_node(node)
        assert graph.get_node("n1") is node

    def test_get_node_nonexistent_returns_none(self):
        graph = DependencyGraph()
        assert graph.get_node("missing") is None

    def test_overwrite_node_same_id(self):
        """Adding a node with an existing ID replaces it."""
        graph = DependencyGraph()
        graph.add_node(DependencyNode("n1", NodeType.DATASET, "original"))
        graph.add_node(DependencyNode("n1", NodeType.MACRO, "replacement"))

        assert graph.node_count() == 1
        assert graph.get_node("n1").name == "replacement"


class TestDependencyGraphTraversal:
    """Tests for dependency and dependent lookups."""

    def _build_simple_graph(self):
        """Build: d1 --READS_FROM--> s1 --WRITES_TO--> d2"""
        graph = DependencyGraph()
        d1 = DependencyNode("d1", NodeType.DATASET, "dataset1")
        s1 = DependencyNode("s1", NodeType.DATA_STEP, "step1")
        d2 = DependencyNode("d2", NodeType.DATASET, "dataset2")

        graph.add_node(d1)
        graph.add_node(s1)
        graph.add_node(d2)

        graph.add_edge("d1", "s1", EdgeType.READS_FROM)
        graph.add_edge("s1", "d2", EdgeType.WRITES_TO)
        return graph

    def test_get_dependencies_direct(self):
        graph = self._build_simple_graph()

        deps = graph.get_dependencies("s1")
        assert len(deps) == 1
        assert deps[0].node_id == "d1"

    def test_get_dependencies_leaf_node(self):
        """d2 has no predecessors (it's only written to)."""
        graph = self._build_simple_graph()
        deps = graph.get_dependencies("d2")
        assert len(deps) == 1  # s1 writes to d2
        assert deps[0].node_id == "s1"

    def test_get_dependencies_root_node(self):
        """d1 has no predecessors."""
        graph = self._build_simple_graph()
        deps = graph.get_dependencies("d1")
        assert len(deps) == 0

    def test_get_dependencies_nonexistent_node(self):
        graph = self._build_simple_graph()
        assert graph.get_dependencies("missing") == []

    def test_get_dependents_direct(self):
        graph = self._build_simple_graph()

        dependents = graph.get_dependents("d1")
        assert len(dependents) == 1
        assert dependents[0].node_id == "s1"

    def test_get_dependents_nonexistent_node(self):
        graph = self._build_simple_graph()
        assert graph.get_dependents("missing") == []

    def test_get_dependencies_multi_depth(self):
        """Depth > 1 traverses transitively."""
        graph = DependencyGraph()
        for nid, ntype, name in [
            ("a", NodeType.DATASET, "A"),
            ("b", NodeType.DATA_STEP, "B"),
            ("c", NodeType.DATASET, "C"),
            ("d", NodeType.DATA_STEP, "D"),
            ("e", NodeType.DATASET, "E"),
        ]:
            graph.add_node(DependencyNode(nid, ntype, name))

        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)
        graph.add_edge("c", "d", EdgeType.READS_FROM)
        graph.add_edge("d", "e", EdgeType.WRITES_TO)

        # Depth 1: d depends only on c
        deps_d1 = graph.get_dependencies("d", depth=1)
        assert len(deps_d1) == 1
        assert deps_d1[0].node_id == "c"

        # Depth 2: d depends on c, and c's predecessor b
        deps_d2 = graph.get_dependencies("d", depth=2)
        dep_ids = {n.node_id for n in deps_d2}
        assert "c" in dep_ids
        assert "b" in dep_ids

        # Depth 3: adds a
        deps_d3 = graph.get_dependencies("d", depth=3)
        dep_ids = {n.node_id for n in deps_d3}
        assert "a" in dep_ids

    def test_get_dependents_multi_depth(self):
        """Depth > 1 for dependents traversal."""
        graph = DependencyGraph()
        for nid, ntype, name in [
            ("a", NodeType.DATASET, "A"),
            ("b", NodeType.DATA_STEP, "B"),
            ("c", NodeType.DATASET, "C"),
            ("d", NodeType.DATA_STEP, "D"),
            ("e", NodeType.DATASET, "E"),
        ]:
            graph.add_node(DependencyNode(nid, ntype, name))

        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)
        graph.add_edge("c", "d", EdgeType.READS_FROM)
        graph.add_edge("d", "e", EdgeType.WRITES_TO)

        deps_depth2 = graph.get_dependents("a", depth=2)
        dep_ids = {n.node_id for n in deps_depth2}
        assert "b" in dep_ids
        assert "c" in dep_ids


class TestTopologicalSort:
    """Tests for topological ordering."""

    def test_simple_chain_order(self):
        """Linear chain preserves dependency order."""
        graph = DependencyGraph()
        nodes = [
            DependencyNode("d1", NodeType.DATASET, "input"),
            DependencyNode("s1", NodeType.DATA_STEP, "step1"),
            DependencyNode("d2", NodeType.DATASET, "intermediate"),
            DependencyNode("s2", NodeType.DATA_STEP, "step2"),
            DependencyNode("d3", NodeType.DATASET, "output"),
        ]
        for n in nodes:
            graph.add_node(n)

        graph.add_edge("d1", "s1", EdgeType.READS_FROM)
        graph.add_edge("s1", "d2", EdgeType.WRITES_TO)
        graph.add_edge("d2", "s2", EdgeType.READS_FROM)
        graph.add_edge("s2", "d3", EdgeType.WRITES_TO)

        sorted_nodes = graph.topological_sort()
        names = [n.name for n in sorted_nodes]

        assert names.index("input") < names.index("step1")
        assert names.index("step1") < names.index("intermediate")
        assert names.index("intermediate") < names.index("step2")
        assert names.index("step2") < names.index("output")

    def test_diamond_dependency(self):
        """Diamond DAG: root before branches before sink."""
        graph = DependencyGraph()
        for nid, name in [
            ("r", "root"),
            ("a", "branch_a"),
            ("b", "branch_b"),
            ("s", "sink"),
        ]:
            graph.add_node(DependencyNode(nid, NodeType.DATASET, name))

        graph.add_edge("r", "a", EdgeType.READS_FROM)
        graph.add_edge("r", "b", EdgeType.READS_FROM)
        graph.add_edge("a", "s", EdgeType.WRITES_TO)
        graph.add_edge("b", "s", EdgeType.WRITES_TO)

        sorted_nodes = graph.topological_sort()
        names = [n.name for n in sorted_nodes]

        assert names.index("root") < names.index("branch_a")
        assert names.index("root") < names.index("branch_b")
        assert names.index("branch_a") < names.index("sink")
        assert names.index("branch_b") < names.index("sink")

    def test_single_node(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("only", NodeType.DATASET, "lonely"))
        sorted_nodes = graph.topological_sort()
        assert len(sorted_nodes) == 1
        assert sorted_nodes[0].node_id == "only"

    def test_disconnected_nodes(self):
        """Disconnected nodes all appear in sort."""
        graph = DependencyGraph()
        for i in range(5):
            graph.add_node(DependencyNode(f"n{i}", NodeType.DATASET, f"data{i}"))

        sorted_nodes = graph.topological_sort()
        assert len(sorted_nodes) == 5

    def test_topological_sort_with_cycle_raises(self):
        graph = DependencyGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(DependencyNode(nid, NodeType.DATASET, nid))

        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)
        graph.add_edge("c", "a", EdgeType.READS_FROM)

        with pytest.raises(ValueError, match="Cannot sort graph with cycles"):
            graph.topological_sort()


class TestCycleDetection:
    """Tests for has_cycles and find_cycles."""

    def test_no_cycles_simple(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "a"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "b"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)

        assert graph.has_cycles() is False

    def test_has_cycles_true(self):
        graph = DependencyGraph()
        for nid in ["d1", "s1", "d2", "s2"]:
            graph.add_node(
                DependencyNode(
                    nid,
                    NodeType.DATASET if nid.startswith("d") else NodeType.DATA_STEP,
                    nid,
                )
            )

        graph.add_edge("d1", "s1", EdgeType.READS_FROM)
        graph.add_edge("s1", "d2", EdgeType.WRITES_TO)
        graph.add_edge("d2", "s2", EdgeType.READS_FROM)
        graph.add_edge("s2", "d1", EdgeType.WRITES_TO)

        assert graph.has_cycles() is True

    def test_find_cycles_returns_cycles(self):
        graph = DependencyGraph()
        for nid in ["a", "b", "c"]:
            graph.add_node(DependencyNode(nid, NodeType.DATASET, nid))

        graph.add_edge("a", "b", EdgeType.WRITES_TO)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)
        graph.add_edge("c", "a", EdgeType.WRITES_TO)

        cycles = graph.find_cycles()
        assert len(cycles) > 0

    def test_find_cycles_no_cycles(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "a"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "b"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)

        cycles = graph.find_cycles()
        assert len(cycles) == 0

    def test_self_loop_is_cycle(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "a"))
        graph.add_edge("a", "a", EdgeType.WRITES_TO)

        assert graph.has_cycles() is True

    def test_empty_graph_no_cycles(self):
        graph = DependencyGraph()
        assert graph.has_cycles() is False


class TestExecutionLayers:
    """Tests for get_execution_layers."""

    def test_diamond_layers(self):
        """Diamond DAG produces 3 layers: root, branches, sink."""
        graph = DependencyGraph()

        d1 = DependencyNode("d1", NodeType.DATASET, "input")
        s1 = DependencyNode("s1", NodeType.DATA_STEP, "step1")
        s2 = DependencyNode("s2", NodeType.DATA_STEP, "step2")
        d2 = DependencyNode("d2", NodeType.DATASET, "output")

        for n in [d1, s1, s2, d2]:
            graph.add_node(n)

        graph.add_edge("d1", "s1", EdgeType.READS_FROM)
        graph.add_edge("d1", "s2", EdgeType.READS_FROM)
        graph.add_edge("s1", "d2", EdgeType.WRITES_TO)
        graph.add_edge("s2", "d2", EdgeType.WRITES_TO)

        layers = graph.get_execution_layers()

        assert len(layers) == 3

        # Layer 0: d1
        layer0_names = {n.name for n in layers[0]}
        assert "input" in layer0_names

        # Layer 1: s1 and s2 (parallel)
        layer1_names = {n.name for n in layers[1]}
        assert "step1" in layer1_names
        assert "step2" in layer1_names

        # Layer 2: d2
        layer2_names = {n.name for n in layers[2]}
        assert "output" in layer2_names

    def test_linear_chain_layers(self):
        """Linear chain: each node in its own layer."""
        graph = DependencyGraph()

        for name in ["a", "b", "c"]:
            graph.add_node(DependencyNode(name, NodeType.DATASET, name))

        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)

        layers = graph.get_execution_layers()
        assert len(layers) == 3

    def test_execution_layers_with_cycles_raises(self):
        graph = DependencyGraph()
        for nid in ["a", "b"]:
            graph.add_node(DependencyNode(nid, NodeType.DATASET, nid))
        graph.add_edge("a", "b", EdgeType.WRITES_TO)
        graph.add_edge("b", "a", EdgeType.WRITES_TO)

        with pytest.raises(ValueError, match="Cannot create execution layers"):
            graph.get_execution_layers()

    def test_single_node_layers(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("only", NodeType.DATASET, "lonely"))

        layers = graph.get_execution_layers()
        assert len(layers) == 1
        assert len(layers[0]) == 1


class TestGetNodesByType:
    """Tests for get_nodes_by_type filtering."""

    def test_filters_by_dataset(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("d1", NodeType.DATASET, "data1"))
        graph.add_node(DependencyNode("d2", NodeType.DATASET, "data2"))
        graph.add_node(DependencyNode("m1", NodeType.MACRO, "macro1"))

        datasets = graph.get_nodes_by_type(NodeType.DATASET)
        assert len(datasets) == 2
        assert all(n.node_type == NodeType.DATASET for n in datasets)

    def test_filters_by_macro(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("d1", NodeType.DATASET, "data1"))
        graph.add_node(DependencyNode("m1", NodeType.MACRO, "macro1"))

        macros = graph.get_nodes_by_type(NodeType.MACRO)
        assert len(macros) == 1
        assert macros[0].name == "macro1"

    def test_empty_result_for_missing_type(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("d1", NodeType.DATASET, "data1"))

        macros = graph.get_nodes_by_type(NodeType.MACRO)
        assert len(macros) == 0

    def test_all_types_present(self):
        graph = DependencyGraph()
        for i, nt in enumerate(NodeType):
            graph.add_node(DependencyNode(f"n_{nt.value}", nt, nt.value))

        for nt in NodeType:
            found = graph.get_nodes_by_type(nt)
            assert len(found) == 1
            assert found[0].node_type == nt


class TestRootAndLeafNodes:
    """Tests for get_root_nodes and get_leaf_nodes."""

    def _build_chain(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))
        graph.add_node(DependencyNode("c", NodeType.DATASET, "C"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)
        return graph

    def test_root_nodes(self):
        graph = self._build_chain()
        roots = graph.get_root_nodes()
        root_ids = {n.node_id for n in roots}
        assert "a" in root_ids
        assert "b" not in root_ids

    def test_leaf_nodes(self):
        graph = self._build_chain()
        leaves = graph.get_leaf_nodes()
        leaf_ids = {n.node_id for n in leaves}
        assert "c" in leaf_ids
        assert "a" not in leaf_ids

    def test_disconnected_all_roots_and_leaves(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATASET, "B"))

        roots = graph.get_root_nodes()
        leaves = graph.get_leaf_nodes()
        assert len(roots) == 2
        assert len(leaves) == 2


class TestSubgraph:
    """Tests for get_subgraph."""

    def test_subgraph_preserves_nodes(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))
        graph.add_node(DependencyNode("c", NodeType.DATASET, "C"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)

        sub = graph.get_subgraph(["a", "b"])
        assert sub.node_count() == 2
        assert sub.edge_count() == 1

    def test_subgraph_excludes_nonexistent(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))

        sub = graph.get_subgraph(["a", "missing"])
        assert sub.node_count() == 1

    def test_subgraph_isolated(self):
        """Subgraph with no edges between selected nodes."""
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATASET, "B"))
        graph.add_node(DependencyNode("c", NodeType.DATASET, "C"))
        graph.add_edge("a", "c", EdgeType.WRITES_TO)

        sub = graph.get_subgraph(["a", "b"])
        assert sub.node_count() == 2
        assert sub.edge_count() == 0


class TestBreakCycles:
    """Tests for break_cycles."""

    def test_break_simple_cycle(self):
        graph = DependencyGraph()
        for nid in ["a", "b"]:
            graph.add_node(DependencyNode(nid, NodeType.DATASET, nid))
        graph.add_edge("a", "b", EdgeType.WRITES_TO)
        graph.add_edge("b", "a", EdgeType.WRITES_TO)

        assert graph.has_cycles()

        removed = graph.break_cycles()
        assert len(removed) > 0
        assert not graph.has_cycles()

    def test_break_cycles_returns_edge_info(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "a"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "b"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "a", EdgeType.WRITES_TO)

        removed = graph.break_cycles()
        assert len(removed) >= 1
        from_id, to_id, edge_type = removed[0]
        assert isinstance(edge_type, EdgeType)

    def test_no_cycles_to_break(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)

        removed = graph.break_cycles()
        assert len(removed) == 0


class TestGraphSerialization:
    """Tests for to_dict and from_dict round-trip."""

    def test_round_trip_simple(self):
        graph = DependencyGraph()
        node1 = DependencyNode("n1", NodeType.DATASET, "data1")
        node2 = DependencyNode("n2", NodeType.DATA_STEP, "step1")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge("n1", "n2", EdgeType.READS_FROM)

        as_dict = graph.to_dict()
        restored = DependencyGraph.from_dict(as_dict)

        assert restored.node_count() == 2
        assert restored.edge_count() == 1
        assert restored.get_edge_type("n1", "n2") == EdgeType.READS_FROM

    def test_round_trip_preserves_node_data(self):
        graph = DependencyGraph()
        node = DependencyNode(
            "n1",
            NodeType.PROC,
            "means",
            source_code="PROC MEANS;",
            metadata={"vars": ["x", "y"]},
            line_start=5,
            line_end=10,
        )
        graph.add_node(node)

        restored = DependencyGraph.from_dict(graph.to_dict())
        n = restored.get_node("n1")

        assert n.name == "means"
        assert n.source_code == "PROC MEANS;"
        assert n.metadata == {"vars": ["x", "y"]}
        assert n.line_start == 5
        assert n.line_end == 10

    def test_round_trip_empty_graph(self):
        graph = DependencyGraph()
        restored = DependencyGraph.from_dict(graph.to_dict())
        assert restored.node_count() == 0
        assert restored.edge_count() == 0

    def test_to_dict_structure(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATASET, "B"))
        graph.add_edge("a", "b", EdgeType.WRITES_TO)

        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert len(d["nodes"]) == 2
        assert len(d["edges"]) == 1
        assert d["edges"][0]["from"] == "a"
        assert d["edges"][0]["to"] == "b"
        assert d["edges"][0]["type"] == "writes_to"


class TestGraphEdgeHelpers:
    """Tests for edge-related helper methods."""

    def test_get_edge_type_existing(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)

        assert graph.get_edge_type("a", "b") == EdgeType.READS_FROM

    def test_get_edge_type_nonexistent(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))

        assert graph.get_edge_type("a", "b") is None

    def test_get_all_edges(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        graph.add_node(DependencyNode("b", NodeType.DATA_STEP, "B"))
        graph.add_node(DependencyNode("c", NodeType.DATASET, "C"))
        graph.add_edge("a", "b", EdgeType.READS_FROM)
        graph.add_edge("b", "c", EdgeType.WRITES_TO)

        edges = graph.get_all_edges()
        assert len(edges) == 2
        edge_types = {et for _, _, et in edges}
        assert EdgeType.READS_FROM in edge_types
        assert EdgeType.WRITES_TO in edge_types


class TestGraphStr:
    """Tests for string representation."""

    def test_str(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a", NodeType.DATASET, "A"))
        s = str(graph)
        assert "nodes=1" in s
        assert "edges=0" in s

    def test_repr_matches_str(self):
        graph = DependencyGraph()
        assert repr(graph) == str(graph)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
