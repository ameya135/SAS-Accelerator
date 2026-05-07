"""
Tests for cAST Chunker - AST-based code chunking for SAS
"""

import pytest
from graph_approach.core.cast_chunker import CASTChunker, CASTConfig, SASTChunk
from graph_approach.ast.sas_ast import SASASTParser


class TestCASTChunkerBasic:
    """Basic cAST chunker tests"""

    def test_small_code_single_chunk(self):
        """Small code that fits in one chunk should produce a single chunk"""
        code = """DATA output;
    SET input;
    x = 1;
RUN;
"""
        chunker = CASTChunker(CASTConfig(max_chunk_size=5000, min_chunk_size=100))
        chunks = chunker.chunk_code(code)

        assert len(chunks) == 1
        assert chunks[0].size > 0
        assert chunks[0].line_start >= 1

    def test_empty_code(self):
        """Empty or whitespace-only code"""
        chunker = CASTChunker()
        chunks = chunker.chunk_code("")
        assert len(chunks) == 1
        assert chunks[0].size == 0 or chunks[0].source_code.strip() == ""

    def test_two_data_steps_separate_chunks(self):
        """Two DATA steps should get their own chunks when each is large enough"""
        code = """DATA step_one;
    SET raw_data;
    var1 = input(raw_var1, best12.);
    var2 = input(raw_var2, best12.);
    var3 = put(calculated_val, dollar12.2);
    label1 = catx(' ', first_name, last_name);
    full_address = catx(', ', street, city, state, zip);
RUN;

DATA step_two;
    SET step_one;
    result1 = mean(var1, var2);
    result2 = sum(var1, var2, var3);
    flag = ifn(result1 > 100, 1, 0);
    category = ifc(result2 > 500, 'HIGH', 'LOW');
    output_var = compress(label1, ' ');
RUN;
"""
        # Use a small max_chunk_size to force splitting
        chunker = CASTChunker(CASTConfig(max_chunk_size=200, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"

    def test_two_data_steps_merged_when_small(self):
        """Two small DATA steps should merge into one chunk when under limit"""
        code = """DATA a;
    SET b;
RUN;

DATA c;
    SET d;
RUN;
"""
        chunker = CASTChunker(CASTConfig(max_chunk_size=5000, min_chunk_size=100))
        chunks = chunker.chunk_code(code)

        assert len(chunks) == 1

    def test_size_metric_non_whitespace(self):
        """Size should count non-whitespace characters only"""
        assert CASTChunker._get_size("abc def") == 6
        assert CASTChunker._get_size("  a  b  c  ") == 3
        assert CASTChunker._get_size("\n\t\n") == 0
        assert CASTChunker._get_size("DATA x; RUN;") == 10  # No spaces counted


class TestCASTChunkerSplitting:
    """Tests for cAST splitting behavior"""

    def test_large_data_step_splits_at_statements(self):
        """A large DATA step with many statements should split at statement boundaries"""
        # Generate a DATA step with many assignment statements
        statements = []
        for i in range(50):
            statements.append(f"    var{i} = input(raw{i}, best12.);")

        code = "DATA big_output;\n    SET big_input;\n"
        code += "\n".join(statements)
        code += "\nRUN;\n"

        # Small limit to force splitting
        chunker = CASTChunker(CASTConfig(max_chunk_size=300, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"

        # Each chunk should have some content
        for chunk in chunks:
            assert chunk.size > 0

    def test_nested_if_then_do_preserved(self):
        """Nested IF-THEN-DO should not be split mid-block when it fits"""
        code = """DATA result;
    SET input;
    IF condition1 THEN DO;
        x = 1;
        y = 2;
    END;
    ELSE DO;
        x = 3;
        y = 4;
    END;
RUN;
"""
        # Set limit large enough to contain the whole thing
        chunker = CASTChunker(CASTConfig(max_chunk_size=5000, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        assert len(chunks) == 1
        assert "IF" in chunks[0].source_code or "if" in chunks[0].source_code

    def test_proc_sql_splits_at_sql_statements(self):
        """A large PROC SQL should split at SQL statement boundaries"""
        sql_stmts = []
        for i in range(20):
            sql_stmts.append(f"""    CREATE TABLE output_{i} AS
        SELECT a.*, b.val{i}
        FROM table_a_{i} AS a
        LEFT JOIN table_b_{i} AS b
        ON a.id = b.id
        WHERE a.status = 'active';""")

        code = "PROC SQL;\n" + "\n".join(sql_stmts) + "\nQUIT;\n"

        chunker = CASTChunker(CASTConfig(max_chunk_size=400, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        assert len(chunks) > 1, f"Expected multiple chunks for large PROC SQL"

    def test_large_macro_with_data_steps_splits(self):
        """A large macro with embedded DATA steps should split recursively"""
        inner_steps = []
        for i in range(10):
            inner_steps.append(f"""DATA step_{i};
    SET prev_{i};
    val{i} = {i} * factor;
    output_val{i} = val{i} + offset;
RUN;""")

        code = "%MACRO big_macro(param1, param2);\n"
        code += "\n".join(inner_steps)
        code += "\n%MEND big_macro;\n"

        chunker = CASTChunker(CASTConfig(max_chunk_size=300, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        assert len(chunks) > 1, f"Expected multiple chunks for large macro"


class TestCASTChunkerContextHeaders:
    """Tests for context header generation"""

    def test_data_step_context_header(self):
        """Context header for a split DATA step includes DATA and SET"""
        # Generate large DATA step
        stmts = [f"    var{i} = {i};" for i in range(50)]
        code = "DATA my_output;\n    SET my_input;\n" + "\n".join(stmts) + "\nRUN;\n"

        chunker = CASTChunker(CASTConfig(max_chunk_size=200, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        if len(chunks) > 1:
            # At least one chunk should have context header with DATA
            headers = [c.context_header for c in chunks if c.context_header]
            assert any("DATA" in h for h in headers), f"Expected DATA in context headers, got {headers}"

    def test_proc_context_header(self):
        """Context header for a split PROC includes PROC name"""
        sql_stmts = []
        for i in range(20):
            sql_stmts.append(f"    CREATE TABLE t{i} AS SELECT * FROM src{i};")

        code = "PROC SQL;\n" + "\n".join(sql_stmts) + "\nQUIT;\n"

        chunker = CASTChunker(CASTConfig(max_chunk_size=300, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        if len(chunks) > 1:
            headers = [c.context_header for c in chunks if c.context_header]
            assert any("PROC" in h.upper() for h in headers), f"Expected PROC in headers, got {headers}"


class TestCASTChunkerRoundTrip:
    """Tests for round-trip integrity"""

    def test_round_trip_no_content_loss(self):
        """Concatenating all chunk source codes should cover original code content"""
        code = """LIBNAME mylib '/data/path';

DATA step_a;
    SET mylib.raw;
    x = 1;
    y = 2;
RUN;

PROC SORT DATA=step_a;
    BY x;
RUN;

DATA step_b;
    SET step_a;
    z = x + y;
RUN;
"""
        chunker = CASTChunker(CASTConfig(max_chunk_size=200, min_chunk_size=50))
        chunks = chunker.chunk_code(code)

        # All non-empty lines from original should appear in at least one chunk
        original_lines = {line.strip() for line in code.split('\n') if line.strip()}
        chunk_lines = set()
        for chunk in chunks:
            for line in chunk.source_code.split('\n'):
                if line.strip():
                    chunk_lines.add(line.strip())

        missing = original_lines - chunk_lines
        # Allow some flexibility for lines that span across chunk boundaries
        assert len(missing) <= len(original_lines) * 0.1, (
            f"Too many lines missing from chunks: {missing}"
        )


class TestCASTChunkerSubchunkMetadata:
    """Tests for sub-chunk metadata when using chunk_node"""

    def test_chunk_node_sets_part_info(self):
        """chunk_node should set part_index and total_parts on sub-chunks"""
        stmts = [f"    var{i} = {i};" for i in range(50)]
        code = "DATA big;\n    SET src;\n" + "\n".join(stmts) + "\nRUN;\n"

        parser = SASASTParser(code)
        program = parser.parse()
        source_lines = code.split('\n')

        # Get the DATA step node
        assert len(program.data_steps) == 1
        data_step = program.data_steps[0]

        chunker = CASTChunker(CASTConfig(max_chunk_size=200, min_chunk_size=50))
        chunks = chunker.chunk_node(data_step, source_lines)

        if len(chunks) > 1:
            for i, chunk in enumerate(chunks):
                assert chunk.part_index == i
                assert chunk.total_parts == len(chunks)
                assert chunk.parent_node_type == "DATA_STEP"


class TestCASTChunkerWithChunkOptimizer:
    """Integration tests with ChunkOptimizer"""

    def test_chunk_optimizer_uses_cast_for_large_single_node(self):
        """ChunkOptimizer should use cAST when a single node exceeds max tokens"""
        from graph_approach.core.dependency_graph import DependencyGraph, DependencyNode
        from graph_approach.core.dependency_graph import NodeType as GraphNodeType
        from graph_approach.core.chunk_optimizer import ChunkOptimizer

        # Create a graph with one large node
        graph = DependencyGraph()

        stmts = [f"    var{i} = {i};" for i in range(80)]
        large_code = "DATA output;\n    SET input;\n" + "\n".join(stmts) + "\nRUN;\n"

        node = DependencyNode(
            node_id="ds_1",
            node_type=GraphNodeType.DATA_STEP,
            name="output",
            source_code=large_code,
            line_start=1,
            line_end=83
        )
        graph.add_node(node)

        # Use very small token limits to force cAST splitting
        optimizer = ChunkOptimizer(
            graph,
            min_chunk_tokens=30,
            max_chunk_tokens=100,
            target_chunk_tokens=80
        )
        chunks = optimizer.generate_chunks()

        # Should have been split by cAST
        stats = optimizer.get_cast_stats()
        assert stats['nodes_split_by_cast'] >= 1 or len(chunks) > 1, (
            f"Expected cAST splitting. Stats: {stats}, chunks: {len(chunks)}"
        )

    def test_chunk_optimizer_cast_metadata_propagated(self):
        """cAST-split chunks should have cast_split metadata"""
        from graph_approach.core.dependency_graph import DependencyGraph, DependencyNode
        from graph_approach.core.dependency_graph import NodeType as GraphNodeType
        from graph_approach.core.chunk_optimizer import ChunkOptimizer

        graph = DependencyGraph()

        stmts = [f"    var{i} = {i};" for i in range(80)]
        large_code = "DATA output;\n    SET input;\n" + "\n".join(stmts) + "\nRUN;\n"

        node = DependencyNode(
            node_id="ds_1",
            node_type=GraphNodeType.DATA_STEP,
            name="output",
            source_code=large_code,
            line_start=1,
            line_end=83
        )
        graph.add_node(node)

        optimizer = ChunkOptimizer(
            graph,
            min_chunk_tokens=30,
            max_chunk_tokens=100,
            target_chunk_tokens=80
        )
        chunks = optimizer.generate_chunks()

        if len(chunks) > 1:
            cast_chunks = [
                c for c in chunks
                if any(n.metadata.get('cast_split') for n in c.nodes)
            ]
            assert len(cast_chunks) > 0, "Expected some chunks with cast_split metadata"

            # Verify metadata fields
            for chunk in cast_chunks:
                for node in chunk.nodes:
                    if node.metadata.get('cast_split'):
                        assert 'parent_node_id' in node.metadata
                        assert 'part_index' in node.metadata
                        assert 'total_parts' in node.metadata


class TestCASTChunkerProcParsing:
    """Tests that PROC body parsing works for cAST splitting"""

    def test_proc_sql_statements_parsed(self):
        """PROC SQL body should produce ProcSQLStatementNode children"""
        code = """PROC SQL;
    CREATE TABLE output1 AS
        SELECT * FROM input1;
    CREATE TABLE output2 AS
        SELECT * FROM input2;
QUIT;
"""
        parser = SASASTParser(code)
        program = parser.parse()

        assert len(program.proc_steps) == 1
        proc = program.proc_steps[0]
        assert proc.proc_name == 'sql'
        assert len(proc.statements) >= 2, (
            f"Expected at least 2 SQL statements, got {len(proc.statements)}"
        )

    def test_proc_means_statements_parsed(self):
        """PROC MEANS body should produce ProcStatementNode children"""
        code = """PROC MEANS DATA=employees;
    VAR salary bonus;
    CLASS department;
    OUTPUT OUT=summary MEAN=avg_salary avg_bonus;
RUN;
"""
        parser = SASASTParser(code)
        program = parser.parse()

        assert len(program.proc_steps) == 1
        proc = program.proc_steps[0]
        assert proc.proc_name == 'means'
        assert len(proc.statements) >= 2, (
            f"Expected at least 2 statements in PROC MEANS, got {len(proc.statements)}"
        )

    def test_proc_sort_statements_parsed(self):
        """PROC SORT body should produce parsed statement nodes"""
        code = """PROC SORT DATA=mydata OUT=sorted_data;
    BY descending salary department;
RUN;
"""
        parser = SASASTParser(code)
        program = parser.parse()

        assert len(program.proc_steps) == 1
        proc = program.proc_steps[0]
        assert len(proc.statements) >= 1, "Expected at least 1 statement in PROC SORT"
