"""
Tests for variable tracker module.

Tests variable lifecycle tracking: definition, usage, deletion,
and validation of PySpark code variable correctness.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_approach.migration.variable_tracker import (
    VariableTracker,
    ValidationResult,
    VariableState,
    VariableInfo,
    ValidationIssue,
    VariableOccurrence,
)


class TestSimpleDefinitionThenUsage:
    """Test 1: Simple code with definition then usage should be valid."""

    def test_definition_before_usage_is_valid(self):
        code = """\
employee_df = spark.read.csv('employees.csv', header=True)
result_df = employee_df.select('name', 'salary')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        # No errors about undefined or use-after-delete
        errors = [
            i
            for i in result.issues
            if i.issue_type in ("undefined", "use_after_delete")
        ]
        assert len(errors) == 0

    def test_definition_tracked(self):
        code = "employee_df = spark.read.csv('employees.csv')\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        assert "employee_df" in result.variables
        assert len(result.variables["employee_df"].definitions) == 1

    def test_usage_tracked_after_definition(self):
        code = """\
employee_df = spark.read.csv('employees.csv')
result = employee_df.select('name')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        assert "employee_df" in result.variables
        usages = result.variables["employee_df"].usages
        assert len(usages) >= 1


class TestUsageBeforeDefinition:
    """Test 2: Usage before definition should flag an issue."""

    def test_usage_before_definition_flags_warning(self):
        code = """\
result = employee_df.select('name')
employee_df = spark.read.csv('employees.csv')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        undefined_issues = [
            i
            for i in result.issues
            if i.issue_type == "undefined" and i.variable_name == "employee_df"
        ]
        assert len(undefined_issues) >= 1

    def test_never_defined_variable_flags_warning(self):
        code = "result = missing_df.select('col')\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        undefined_issues = [i for i in result.issues if i.issue_type == "undefined"]
        assert any(i.variable_name == "missing_df" for i in undefined_issues)


class TestUsageAfterDeletion:
    """Test 3: Usage after deletion should flag an issue."""

    def test_usage_after_deletion_flags_warning(self):
        code = """\
employee_df = spark.read.csv('employees.csv')
del employee_df
result = employee_df.select('name')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        use_after_del = [
            i
            for i in result.issues
            if i.issue_type == "use_after_delete" and i.variable_name == "employee_df"
        ]
        assert len(use_after_del) >= 1


class TestDuplicateDefinition:
    """Test 4: Duplicate definition should flag info."""

    def test_duplicate_definition_flags_info(self):
        code = """\
employee_df = spark.read.csv('employees.csv')
employee_df = spark.read.csv('other.csv')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        dup_issues = [
            i
            for i in result.issues
            if i.issue_type == "duplicate_definition"
            and i.variable_name == "employee_df"
        ]
        assert len(dup_issues) == 1
        assert dup_issues[0].severity == "info"


class TestValidPySparkCode:
    """Test 5: Valid PySpark code with spark session, imports, DataFrame ops."""

    def test_valid_full_pyspark_code(self):
        code = """\
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("Test").getOrCreate()

employee_df = spark.read.csv('employees.csv', header=True, inferSchema=True)
filtered = employee_df.filter(F.col('salary') > 50000)
grouped = filtered.groupBy('department').count()
grouped.show()
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        # Should not have critical undefined errors for used variables
        critical = [
            i
            for i in result.issues
            if i.issue_type == "undefined"
            and i.variable_name in ("employee_df", "filtered")
        ]
        # 'filtered' is defined on line 6 and used on line 7, so no issue
        # 'employee_df' is defined on line 5 and used on line 6, so no issue
        assert len(critical) == 0

    def test_spark_session_not_flagged_as_undefined(self):
        code = "spark = SparkSession.builder.getOrCreate()\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        spark_issues = [i for i in result.issues if i.variable_name == "spark"]
        assert len(spark_issues) == 0


class TestMacroVariableDetection:
    """Test 6: Macro variable detection."""

    def test_macro_variable_detected(self):
        code = "result = unemployment_shock * 2\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        assert "unemployment_shock" in result.variables

    def test_macro_variable_default_value_populated(self):
        code = "x = unemployment_shock + gdp_decline\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        assert "unemployment_shock" in result.macro_variables
        assert result.macro_variables["unemployment_shock"] == "5.0"
        assert "gdp_decline" in result.macro_variables
        assert result.macro_variables["gdp_decline"] == "-2.0"

    def test_macro_variable_with_definition_not_in_macro_vars(self):
        """If a macro variable is defined in code, it should not appear in macro_variables."""
        code = """\
unemployment_shock = 3.0
x = unemployment_shock * 2
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        # Since it has a definition, it should not be auto-initialized as macro var
        assert "unemployment_shock" not in result.macro_variables


class TestCommentsIgnored:
    """Test 7: Code with comments should be ignored for variable analysis."""

    def test_comment_only_lines_ignored(self):
        code = """\
# result = undefined_df.select('col')
# del undefined_df
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        # No variables should be tracked from pure comment lines
        assert (
            "undefined_df" not in result.variables
            or len(result.variables.get("undefined_df", VariableInfo(name="x")).usages)
            == 0
        )

    def test_inline_comments_stripped(self):
        code = "result = employee_df.select('name')  # select names\n"
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        # employee_df should be tracked from the code part, not the comment
        assert "employee_df" in result.variables


class TestEmptyCode:
    """Test 8: Empty code should be valid."""

    def test_empty_code_is_valid(self):
        tracker = VariableTracker()
        result = tracker.analyze_code("")
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_whitespace_only_code_is_valid(self):
        tracker = VariableTracker()
        result = tracker.analyze_code("   \n  \n")
        assert result.is_valid is True

    def test_only_comments_code_is_valid(self):
        tracker = VariableTracker()
        result = tracker.analyze_code("# just a comment\n# another\n")
        assert result.is_valid is True


class TestValidationResultGetErrors:
    """Test 9: ValidationResult.get_errors() filters correctly."""

    def test_get_errors_returns_only_errors(self):
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    issue_type="test",
                    variable_name="a",
                    line_number=1,
                    message="error msg",
                    severity="error",
                ),
                ValidationIssue(
                    issue_type="test",
                    variable_name="b",
                    line_number=2,
                    message="warning msg",
                    severity="warning",
                ),
                ValidationIssue(
                    issue_type="test",
                    variable_name="c",
                    line_number=3,
                    message="info msg",
                    severity="info",
                ),
            ],
        )
        errors = result.get_errors()
        assert len(errors) == 1
        assert errors[0].severity == "error"

    def test_get_errors_empty_when_none(self):
        result = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(
                    issue_type="test",
                    variable_name="a",
                    line_number=1,
                    message="warning msg",
                    severity="warning",
                ),
            ],
        )
        errors = result.get_errors()
        assert len(errors) == 0

    def test_get_errors_multiple_errors(self):
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    issue_type="t1",
                    variable_name="a",
                    line_number=1,
                    message="e1",
                    severity="error",
                ),
                ValidationIssue(
                    issue_type="t2",
                    variable_name="b",
                    line_number=2,
                    message="e2",
                    severity="error",
                ),
            ],
        )
        errors = result.get_errors()
        assert len(errors) == 2


class TestValidationResultGetWarnings:
    """Test 10: ValidationResult.get_warnings() filters correctly."""

    def test_get_warnings_returns_only_warnings(self):
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    issue_type="test",
                    variable_name="a",
                    line_number=1,
                    message="error msg",
                    severity="error",
                ),
                ValidationIssue(
                    issue_type="test",
                    variable_name="b",
                    line_number=2,
                    message="warning msg",
                    severity="warning",
                ),
                ValidationIssue(
                    issue_type="test",
                    variable_name="c",
                    line_number=3,
                    message="info msg",
                    severity="info",
                ),
            ],
        )
        warnings = result.get_warnings()
        assert len(warnings) == 1
        assert warnings[0].severity == "warning"

    def test_get_warnings_empty_when_none(self):
        result = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(
                    issue_type="test",
                    variable_name="a",
                    line_number=1,
                    message="info msg",
                    severity="info",
                ),
            ],
        )
        warnings = result.get_warnings()
        assert len(warnings) == 0


class TestVariableTrackerHelpers:
    """Additional tests for helper methods."""

    def test_find_undefined_variables(self):
        code = "result = undefined_df.select('col')\n"
        tracker = VariableTracker()
        tracker.analyze_code(code)
        undefined = tracker.find_undefined_variables()
        assert "undefined_df" in undefined

    def test_find_use_after_delete(self):
        code = """\
employee_df = spark.read.csv('data.csv')
del employee_df
result = employee_df.select('name')
"""
        tracker = VariableTracker()
        tracker.analyze_code(code)
        issues = tracker.find_use_after_delete()
        assert len(issues) >= 1
        var_name, del_line, use_line = issues[0]
        assert var_name == "employee_df"

    def test_suggest_fixes_adds_placeholder(self):
        code = "result = missing_df.select('col')\n"
        tracker = VariableTracker()
        tracker.analyze_code(code)
        fixed_code, fixes = tracker.suggest_fixes(code)
        assert len(fixes) >= 1
        assert "missing_df" in fixed_code

    def test_generate_validation_report(self):
        code = "result = undefined_df.select('col')\n"
        tracker = VariableTracker()
        tracker.analyze_code(code)
        report = tracker.generate_validation_report()
        assert "VARIABLE LIFECYCLE VALIDATION REPORT" in report
        assert "Total Issues:" in report

    def test_variable_info_first_definition_line(self):
        info = VariableInfo(
            name="test",
            definitions=[
                VariableOccurrence(line_number=5, occurrence_type="definition"),
                VariableOccurrence(line_number=10, occurrence_type="definition"),
            ],
        )
        assert info.first_definition_line == 5

    def test_variable_info_first_usage_line_none(self):
        info = VariableInfo(name="test")
        assert info.first_usage_line is None

    def test_variable_info_first_deletion_line(self):
        info = VariableInfo(
            name="test",
            deletions=[
                VariableOccurrence(line_number=7, occurrence_type="deletion"),
            ],
        )
        assert info.first_deletion_line == 7

    def test_ignore_vars_not_tracked(self):
        """Ensure built-in names like spark, F, True are ignored."""
        code = """\
result = True
x = F.col('name')
"""
        tracker = VariableTracker()
        result = tracker.analyze_code(code)
        assert "True" not in result.variables
        assert "F" not in result.variables

    def test_suggest_fixes_comments_out_deletions(self):
        code = """\
employee_df = spark.read.csv('data.csv')
del employee_df
result = employee_df.select('name')
"""
        tracker = VariableTracker()
        tracker.analyze_code(code)
        fixed_code, fixes = tracker.suggest_fixes(code)
        assert "COMMENTED OUT" in fixed_code
