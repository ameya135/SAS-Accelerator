"""
Tests for GraphBuilder
"""

import pytest
import importlib
import sys
from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.core.dependency_graph import NodeType, EdgeType
from graph_approach.core.chunk_optimizer import ChunkOptimizer
from graph_approach.core.schema_tracker import ExecutionContext
from graph_approach.migration.context_enricher import ContextEnricher


def _edge_exists(graph, source, target, edge_type):
    data = graph.graph.get_edge_data(source.node_id, target.node_id)
    return bool(data and data.get("edge_type") == edge_type.value)


class TestGraphBuilder:
    """Test GraphBuilder functionality"""

    def test_build_simple_graph(self):
        """Test building graph from simple SAS code"""
        sas_code = """
        DATA output_data;
            SET input_data;
            new_var = old_var * 2;
        RUN;
        """

        builder = GraphBuilder(sas_code=sas_code)
        graph = builder.build_graph()

        assert graph.node_count() > 0

        # Should have DATA step node
        data_steps = graph.get_nodes_by_type(NodeType.DATA_STEP)
        assert len(data_steps) >= 1

        # Should have dataset nodes
        datasets = graph.get_nodes_by_type(NodeType.DATASET)
        assert len(datasets) >= 2  # input_data and output_data

    def test_dependencies_extracted(self):
        """Test that dependencies are correctly extracted"""
        sas_code = """
        DATA step1_output;
            SET raw_data;
        RUN;

        DATA final_output;
            SET step1_output;
            result = value * 2;
        RUN;
        """

        builder = GraphBuilder(sas_code=sas_code)
        graph = builder.build_graph()

        # Get execution order
        execution_order = builder.get_execution_order()
        names = [n.name for n in execution_order]

        # step1_output should be created before it's used
        datasets = graph.get_nodes_by_type(NodeType.DATASET)
        step1_dataset = next((d for d in datasets if 'step1_output' in d.name.lower()), None)

        if step1_dataset:
            # Check that something depends on step1_output
            dependents = graph.get_dependents(step1_dataset.node_id)
            assert len(dependents) > 0

    def test_macro_detection(self):
        """Test that macros are detected"""
        sas_code = """
        %MACRO test_macro(param1);
            DATA output;
                SET input;
            RUN;
        %MEND test_macro;

        %test_macro(value);
        """

        builder = GraphBuilder(sas_code=sas_code)
        graph = builder.build_graph()

        macros = graph.get_nodes_by_type(NodeType.MACRO)
        assert len(macros) >= 1

    def test_proc_detection(self):
        """Test that PROCs are detected"""
        sas_code = """
        DATA mydata;
            INPUT x y;
            DATALINES;
        1 2
        3 4
        ;
        RUN;

        PROC MEANS DATA=mydata;
            VAR x y;
        RUN;
        """

        builder = GraphBuilder(sas_code=sas_code)
        graph = builder.build_graph()

        procs = graph.get_nodes_by_type(NodeType.PROC)
        assert len(procs) >= 1

    def test_api_package_does_not_eagerly_import_realtime_migrator(self):
        """Graph-only API imports should not require runtime LLM modules."""
        sys.modules.pop("graph_approach.api", None)
        sys.modules.pop("graph_approach.api.realtime_migrator", None)

        api = importlib.import_module("graph_approach.api")

        assert api.GraphExporter is not None
        assert api.SchemaExporter is not None
        assert "graph_approach.api.realtime_migrator" not in sys.modules

    def test_builtin_parser_proc_means_data_keyword_option_creates_input_dependency(
        self, monkeypatch
    ):
        """Built-in parser should capture PROC DATA= even when DATA is a keyword."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        PROC MEANS DATA=mydata;
            VAR amount;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()

        proc = next(node for node in graph.get_nodes_by_type(NodeType.PROC))
        dataset = next(
            node
            for node in graph.get_nodes_by_type(NodeType.DATASET)
            if node.name == "mydata"
        )
        assert _edge_exists(graph, dataset, proc, EdgeType.PROC_INPUT)

    def test_builtin_parser_proc_sort_out_keyword_option_creates_dependencies(
        self, monkeypatch
    ):
        """Built-in parser should capture PROC SORT DATA= and OUT= keyword options."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        PROC SORT DATA=raw_sales OUT=sorted_sales;
            BY region;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()

        proc = next(node for node in graph.get_nodes_by_type(NodeType.PROC))
        datasets = {
            node.name: node for node in graph.get_nodes_by_type(NodeType.DATASET)
        }
        assert _edge_exists(graph, datasets["raw_sales"], proc, EdgeType.PROC_INPUT)
        assert _edge_exists(graph, proc, datasets["sorted_sales"], EdgeType.PROC_OUTPUT)

    def test_builtin_parser_preserves_full_data_step_source(self, monkeypatch):
        """Fallback parser should preserve full DATA step source for LLM prompts."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        DATA output_data;
            SET input_data;
            new_var = old_var * 2;
            IF new_var > 10 THEN flag = 1;
            ELSE flag = 0;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()
        data_step = next(node for node in graph.get_nodes_by_type(NodeType.DATA_STEP))

        assert "DATA output_data" in data_step.source_code
        assert "SET input_data" in data_step.source_code
        assert "new_var = old_var * 2" in data_step.source_code
        assert "IF new_var > 10 THEN flag = 1" in data_step.source_code
        assert "ELSE flag = 0" in data_step.source_code
        assert "RUN;" in data_step.source_code

    def test_builtin_parser_preserves_proc_header_options_and_terminator(
        self, monkeypatch
    ):
        """Fallback parser should preserve complete PROC source for LLM prompts."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        PROC SORT DATA=raw_sales OUT=sorted_sales;
            BY region;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()
        proc = next(node for node in graph.get_nodes_by_type(NodeType.PROC))

        assert "PROC SORT" in proc.source_code.upper()
        assert "DATA=raw_sales" in proc.source_code
        assert "OUT=sorted_sales" in proc.source_code
        assert "BY region" in proc.source_code
        assert "RUN;" in proc.source_code

    def test_builtin_parser_preserves_macro_definition_wrapper(self, monkeypatch):
        """Fallback parser should preserve macro wrappers and body source."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        %MACRO test_macro(param1);
            DATA output;
                SET input;
            RUN;
        %MEND test_macro;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()
        macro = next(node for node in graph.get_nodes_by_type(NodeType.MACRO))

        assert "%MACRO test_macro" in macro.source_code
        assert "DATA output" in macro.source_code
        assert "SET input" in macro.source_code
        assert "%MEND test_macro" in macro.source_code

    def test_chunks_are_non_empty_and_do_not_duplicate_nodes(self, monkeypatch):
        """Optimizer should not emit empty LLM chunks or duplicate graph nodes."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        DATA output_data;
            SET input_data;
            new_var = old_var * 2;
        RUN;

        PROC SORT DATA=output_data OUT=sorted_output;
            BY new_var;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()
        chunks = ChunkOptimizer(graph).generate_chunks()

        assert chunks
        assert all(chunk.source_code.strip() for chunk in chunks)

        node_ids = [node.node_id for chunk in chunks for node in chunk.nodes]
        assert len(node_ids) == len(set(node_ids))

    def test_prompt_contains_non_empty_full_sas_block(self, monkeypatch):
        """Context prompt should include complete SAS source for conversion chunks."""
        import graph_approach.core.graph_builder as graph_builder

        monkeypatch.setattr(graph_builder, "SAS_PARSER_AVAILABLE", False)
        monkeypatch.setattr(graph_builder, "SASParser", None)

        sas_code = """
        DATA output_data;
            SET input_data;
            new_var = old_var * 2;
        RUN;
        """

        graph = GraphBuilder(sas_code=sas_code).build_graph()
        chunk = ChunkOptimizer(graph).generate_chunks()[0]
        execution_context = ExecutionContext()
        enricher = ContextEnricher(graph, execution_context)
        prompt = enricher.build_llm_prompt(
            chunk, enricher.enrich_chunk_context(chunk)
        )

        assert "SAS CODE TO CONVERT:" in prompt
        assert "DATA output_data" in prompt
        assert "new_var = old_var * 2" in prompt
        assert "RUN;" in prompt

    def test_summary_statistics(self):
        """Test graph summary statistics"""
        sas_code = """
        DATA test;
            SET input;
        RUN;
        """

        builder = GraphBuilder(sas_code=sas_code)
        graph = builder.build_graph()

        summary = builder.get_summary()

        assert 'total_nodes' in summary
        assert 'total_edges' in summary
        assert 'has_cycles' in summary
        assert 'node_counts_by_type' in summary
        assert summary['total_nodes'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
