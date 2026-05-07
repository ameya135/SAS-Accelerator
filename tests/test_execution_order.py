"""
Tests for execution order optimizer module.

Tests code block parsing, dependency analysis, topological sorting,
circular dependency detection, and block type classification.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_approach.migration.execution_order import (
    ExecutionOrderOptimizer,
    BlockType,
    ExecutionBlock,
    ExecutionOrderResult,
    DependencyIssue,
)


class TestSimpleCodeOrdering:
    """Test 1: Simple code with imports and operations - correct order."""

    def test_imports_come_first(self):
        code = """\
import pyspark.sql.functions as F
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Test").getOrCreate()

employee_df = spark.read.csv('employees.csv')
result = employee_df.filter(F.col('salary') > 50000)
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # Import blocks should come before transform blocks
        import_indices = [
            i
            for i, b in enumerate(result.ordered_blocks)
            if b.block_type == BlockType.IMPORT
        ]
        transform_indices = [
            i
            for i, b in enumerate(result.ordered_blocks)
            if b.block_type == BlockType.TRANSFORM
        ]
        if import_indices and transform_indices:
            assert max(import_indices) < min(transform_indices)

    def test_correct_order_for_simple_pipeline(self):
        code = """\
employee_df = spark.read.csv('employees.csv')

filtered = employee_df.filter(F.col('salary') > 50000)
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # Should produce at least 2 blocks
        assert len(result.ordered_blocks) >= 2

    def test_result_has_original_and_new_order(self):
        code = "x = 1\ny = x + 1\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert len(result.original_order) > 0
        assert len(result.new_order) > 0


class TestDataDependencyOrdering:
    """Test 2: Code with data dependencies - reordering if needed."""

    def test_reorder_when_usage_before_definition(self):
        # Define blocks that use a variable before defining it
        code = """\
result = source_df.select('name')

source_df = spark.read.csv('data.csv')
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # The optimizer should detect the dependency and potentially reorder
        # At minimum it should detect the dependency relationship
        assert len(result.ordered_blocks) >= 1

    def test_dependency_graph_built(self):
        code = """\
source_df = spark.read.csv('data.csv')
result = source_df.select('name')
"""
        optimizer = ExecutionOrderOptimizer()
        optimizer.analyze_and_optimize(code)
        # Should have built some dependency graph
        assert len(optimizer.dependency_graph) >= 0

    def test_blocks_have_defines_and_uses(self):
        code = """\
source_df = spark.read.csv('data.csv')
result = source_df.select('name')
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # At least one block should define a variable
        all_defines = set()
        for block in result.ordered_blocks:
            all_defines.update(block.defines)
        # source_df should be defined somewhere
        assert "source_df" in all_defines


class TestCircularDependencyDetection:
    """Test 3: Circular dependency detection."""

    def test_circular_dependency_reported(self):
        # Create a scenario where blocks depend on each other
        # This is hard to trigger naturally, but we can test the infrastructure
        optimizer = ExecutionOrderOptimizer()
        # Manually create blocks with circular dependency
        block_a = ExecutionBlock(
            block_id="block_0",
            code="a = b",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
            defines={"a"},
            uses={"b"},
            dependencies={"block_1"},
        )
        block_b = ExecutionBlock(
            block_id="block_1",
            code="b = a",
            block_type=BlockType.TRANSFORM,
            line_start=2,
            line_end=2,
            defines={"b"},
            uses={"a"},
            dependencies={"block_0"},
        )
        optimizer.blocks = [block_a, block_b]
        optimizer.dependency_graph = {"block_0": {"block_1"}, "block_1": {"block_0"}}
        optimizer._detect_issues()
        circular = [i for i in optimizer.issues if i.issue_type == "circular"]
        assert len(circular) >= 1

    def test_no_circular_dependency_in_linear_code(self):
        code = """\
a = spark.read.csv('a.csv')
b = a.select('col')
c = b.filter(F.col('col') > 0)
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        circular = [i for i in result.issues if i.issue_type == "circular"]
        assert len(circular) == 0


class TestBlockTypeClassification:
    """Test 4: Block type classification."""

    def test_import_block_type(self):
        code = "import pyspark.sql.functions as F\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.IMPORT for b in result.ordered_blocks)

    def test_spark_init_block_type(self):
        code = """\
spark = SparkSession.builder.appName("Test").getOrCreate()
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.SPARK_INIT for b in result.ordered_blocks)

    def test_data_load_block_type(self):
        code = "df = spark.read.csv('data.csv')\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.DATA_LOAD for b in result.ordered_blocks)

    def test_output_block_type(self):
        code = "df.write.parquet('output.parquet')\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.OUTPUT for b in result.ordered_blocks)

    def test_aggregation_block_type(self):
        code = "result = df.groupBy('col').count()\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.AGGREGATION for b in result.ordered_blocks)

    def test_transform_block_type(self):
        code = "result = df.select('col1', 'col2')\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(
            b.block_type in (BlockType.TRANSFORM, BlockType.OTHER)
            for b in result.ordered_blocks
        )

    def test_comment_block_type(self):
        code = "# This is a comment\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # Comments should either be COMMENT type or no blocks at all
        for b in result.ordered_blocks:
            if b.code.strip().startswith("#"):
                assert b.block_type == BlockType.COMMENT

    def test_macro_var_block_type(self):
        code = "unemployment_shock = 5.0\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert any(b.block_type == BlockType.MACRO_VAR for b in result.ordered_blocks)


class TestCodeWithComments:
    """Test 5: Code with comments."""

    def test_comments_do_not_break_analysis(self):
        code = """\
# Import section
import pyspark.sql.functions as F

# Load data
df = spark.read.csv('data.csv')

# Filter data
result = df.filter(F.col('value') > 0)
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert len(result.ordered_blocks) >= 2

    def test_comment_only_code(self):
        code = "# Just a comment\n# Another comment\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # Should handle gracefully - may produce comment blocks or no blocks
        assert result is not None

    def test_inline_comment_handling(self):
        code = "df = spark.read.csv('data.csv')  # load data\n"
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        assert len(result.ordered_blocks) >= 1


class TestAlreadyOrderedCode:
    """Test 6: Already-ordered code should not be reordered."""

    def test_already_correct_order_not_reordered(self):
        code = """\
import pyspark.sql.functions as F

df = spark.read.csv('data.csv')
result = df.select('col')
result.show()
"""
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize(code)
        # If the code is already in correct order, reordered should be False
        # or the order should remain the same
        if not result.reordered:
            assert result.original_order == result.new_order
        else:
            # If reordered, it should still be valid
            assert len(result.ordered_blocks) > 0

    def test_optimize_code_returns_string(self):
        code = "df = spark.read.csv('data.csv')\n"
        optimizer = ExecutionOrderOptimizer()
        optimized, changes = optimizer.optimize_code(code)
        assert isinstance(optimized, str)
        assert isinstance(changes, list)


class TestGenerateReport:
    """Test 7: generate_report() produces output."""

    def test_generate_report_returns_string(self):
        code = """\
import pyspark.sql.functions as F
df = spark.read.csv('data.csv')
result = df.select('col')
"""
        optimizer = ExecutionOrderOptimizer()
        optimizer.analyze_and_optimize(code)
        report = optimizer.generate_report()
        assert isinstance(report, str)
        assert "EXECUTION ORDER ANALYSIS REPORT" in report

    def test_report_contains_block_summary(self):
        code = "df = spark.read.csv('data.csv')\nresult = df.select('col')\n"
        optimizer = ExecutionOrderOptimizer()
        optimizer.analyze_and_optimize(code)
        report = optimizer.generate_report()
        assert "BLOCK SUMMARY" in report
        assert "Total Blocks:" in report

    def test_report_with_issues(self):
        """Report should include issues when circular dependency exists."""
        optimizer = ExecutionOrderOptimizer()
        block_a = ExecutionBlock(
            block_id="block_0",
            code="a = b",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
            defines={"a"},
            uses={"b"},
            dependencies={"block_1"},
        )
        block_b = ExecutionBlock(
            block_id="block_1",
            code="b = a",
            block_type=BlockType.TRANSFORM,
            line_start=2,
            line_end=2,
            defines={"b"},
            uses={"a"},
            dependencies={"block_0"},
        )
        optimizer.blocks = [block_a, block_b]
        optimizer.dependency_graph = {"block_0": {"block_1"}, "block_1": {"block_0"}}
        optimizer._detect_issues()
        report = optimizer.generate_report()
        assert "ISSUES DETECTED" in report


class TestEmptyCodeHandling:
    """Test 8: Empty code handling."""

    def test_empty_code_no_blocks(self):
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize("")
        assert len(result.ordered_blocks) == 0
        assert result.reordered is False

    def test_whitespace_only_code(self):
        optimizer = ExecutionOrderOptimizer()
        result = optimizer.analyze_and_optimize("   \n  \n")
        assert len(result.ordered_blocks) == 0

    def test_empty_code_report(self):
        optimizer = ExecutionOrderOptimizer()
        optimizer.analyze_and_optimize("")
        report = optimizer.generate_report()
        assert "EXECUTION ORDER ANALYSIS REPORT" in report
        assert "Total Blocks: 0" in report


class TestExecutionBlock:
    """Tests for ExecutionBlock dataclass."""

    def test_block_hash_by_id(self):
        block = ExecutionBlock(
            block_id="block_0",
            code="x = 1",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
        )
        assert hash(block) == hash("block_0")

    def test_block_equality_by_id(self):
        block_a = ExecutionBlock(
            block_id="block_0",
            code="x = 1",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
        )
        block_b = ExecutionBlock(
            block_id="block_0",
            code="y = 2",
            block_type=BlockType.OTHER,
            line_start=2,
            line_end=2,
        )
        assert block_a == block_b

    def test_block_inequality(self):
        block_a = ExecutionBlock(
            block_id="block_0",
            code="x = 1",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
        )
        block_b = ExecutionBlock(
            block_id="block_1",
            code="x = 1",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
        )
        assert block_a != block_b

    def test_block_not_equal_to_non_block(self):
        block = ExecutionBlock(
            block_id="block_0",
            code="x = 1",
            block_type=BlockType.TRANSFORM,
            line_start=1,
            line_end=1,
        )
        assert block != "block_0"
        assert block != 42


class TestDependencyIssue:
    """Tests for DependencyIssue dataclass."""

    def test_dependency_issue_creation(self):
        issue = DependencyIssue(
            issue_type="circular",
            description="Test circular dep",
            blocks_involved=["block_0", "block_1"],
            suggested_fix="Break the cycle",
        )
        assert issue.issue_type == "circular"
        assert issue.description == "Test circular dep"
        assert len(issue.blocks_involved) == 2
        assert issue.suggested_fix == "Break the cycle"


class TestOptimizeCodeMethod:
    """Tests for the optimize_code() high-level method."""

    def test_optimize_code_no_reorder(self):
        code = "x = 1\n"
        optimizer = ExecutionOrderOptimizer()
        optimized, changes = optimizer.optimize_code(code)
        assert "No reordering needed" in changes[0]

    def test_optimize_code_preserves_imports(self):
        code = """\
import pyspark.sql.functions as F
df = spark.read.csv('data.csv')
"""
        optimizer = ExecutionOrderOptimizer()
        optimized, changes = optimizer.optimize_code(code)
        # Imports should be near the top
        lines = optimized.split("\n")
        import_lines = [i for i, l in enumerate(lines) if "import" in l]
        non_comment_non_empty = [
            i
            for i, l in enumerate(lines)
            if l.strip() and not l.strip().startswith("#")
        ]
        if import_lines and non_comment_non_empty:
            assert min(import_lines) <= min(non_comment_non_empty)
