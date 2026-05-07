"""
Tests for the schema tracker module.

Covers:
- ColumnInfo: creation, defaults, serialization
- DatasetSchema: column operations, merge, keep, drop, rename, serialization
- ExecutionContext: dataset tracking, variable name mapping
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from graph_approach.core.schema_tracker import (
    ColumnInfo,
    DataType,
    DatasetSchema,
    ExecutionContext,
)


# ===================================================================
# ColumnInfo Tests
# ===================================================================


class TestColumnInfo:
    """Tests for the ColumnInfo dataclass."""

    # --- Creation ---

    def test_creation_with_defaults(self):
        col = ColumnInfo(name="salary")

        assert col.name == "salary"
        assert col.data_type == DataType.UNKNOWN
        assert col.format is None
        assert col.label is None
        assert col.length is None
        assert col.source is None

    def test_creation_with_all_fields(self):
        col = ColumnInfo(
            name="salary",
            data_type=DataType.DOUBLE,
            format="DOLLAR12.2",
            label="Employee Salary",
            length=8,
            source="assignment",
        )

        assert col.name == "salary"
        assert col.data_type == DataType.DOUBLE
        assert col.format == "DOLLAR12.2"
        assert col.label == "Employee Salary"
        assert col.length == 8
        assert col.source == "assignment"

    def test_creation_various_data_types(self):
        for dt in DataType:
            col = ColumnInfo(name=f"col_{dt.value}", data_type=dt)
            assert col.data_type == dt

    # --- Serialization ---

    def test_to_dict(self):
        col = ColumnInfo(
            name="hire_date",
            data_type=DataType.DATE,
            format="DATE9.",
            label="Hire Date",
            length=10,
            source="input",
        )
        d = col.to_dict()

        assert d["name"] == "hire_date"
        assert d["data_type"] == "date"
        assert d["format"] == "DATE9."
        assert d["label"] == "Hire Date"
        assert d["length"] == 10
        assert d["source"] == "input"

    def test_to_dict_with_defaults(self):
        col = ColumnInfo(name="x")
        d = col.to_dict()

        assert d["name"] == "x"
        assert d["data_type"] == "unknown"
        assert d["format"] is None
        assert d["label"] is None
        assert d["length"] is None
        assert d["source"] is None

    def test_from_dict_round_trip(self):
        original = ColumnInfo(
            name="amount",
            data_type=DataType.DOUBLE,
            format="COMMA12.2",
            label="Total Amount",
            length=8,
            source="calculated",
        )
        restored = ColumnInfo.from_dict(original.to_dict())

        assert restored.name == original.name
        assert restored.data_type == original.data_type
        assert restored.format == original.format
        assert restored.label == original.label
        assert restored.length == original.length
        assert restored.source == original.source

    def test_from_dict_with_missing_fields(self):
        data = {"name": "col1"}
        col = ColumnInfo.from_dict(data)

        assert col.name == "col1"
        assert col.data_type == DataType.UNKNOWN
        assert col.format is None

    def test_from_dict_preserves_data_type(self):
        for dt in DataType:
            col = ColumnInfo.from_dict({"name": "test", "data_type": dt.value})
            assert col.data_type == dt


# ===================================================================
# DatasetSchema Tests
# ===================================================================


class TestDatasetSchemaCreation:
    """Tests for DatasetSchema creation and basic operations."""

    def test_creation_defaults(self):
        schema = DatasetSchema(name="employees")

        assert schema.name == "employees"
        assert schema.columns == {}
        assert schema.source_node_id is None
        assert schema.created_by is None
        assert schema.metadata == {}

    def test_creation_with_all_fields(self):
        schema = DatasetSchema(
            name="employees",
            source_node_id="s1",
            created_by="DATA_STEP",
            metadata={"libref": "mylib"},
        )

        assert schema.name == "employees"
        assert schema.source_node_id == "s1"
        assert schema.created_by == "DATA_STEP"
        assert schema.metadata == {"libref": "mylib"}


class TestDatasetSchemaColumnOps:
    """Tests for add_column, remove_column, rename_column, get_column."""

    def _make_schema_with_columns(self):
        schema = DatasetSchema(name="test_data")
        schema.add_column(ColumnInfo(name="name", data_type=DataType.STRING, length=50))
        schema.add_column(
            ColumnInfo(name="salary", data_type=DataType.DOUBLE, format="DOLLAR12.2")
        )
        schema.add_column(
            ColumnInfo(name="hire_date", data_type=DataType.DATE, format="DATE9.")
        )
        return schema

    def test_add_column(self):
        schema = DatasetSchema(name="test")
        schema.add_column(ColumnInfo(name="col1", data_type=DataType.INTEGER))

        assert "col1" in schema.columns
        assert schema.columns["col1"].data_type == DataType.INTEGER

    def test_add_multiple_columns(self):
        schema = self._make_schema_with_columns()

        assert len(schema.columns) == 3
        assert "name" in schema.columns
        assert "salary" in schema.columns
        assert "hire_date" in schema.columns

    def test_get_column_exact_match(self):
        schema = self._make_schema_with_columns()

        col = schema.get_column("salary")
        assert col is not None
        assert col.name == "salary"
        assert col.data_type == DataType.DOUBLE

    def test_get_column_case_insensitive(self):
        schema = self._make_schema_with_columns()

        assert schema.get_column("Salary") is not None
        assert schema.get_column("SALARY") is not None
        assert schema.get_column("salary") is not None

    def test_get_column_mixed_case(self):
        schema = self._make_schema_with_columns()

        col = schema.get_column("HIRE_DATE")
        assert col is not None
        assert col.data_type == DataType.DATE

    def test_get_column_nonexistent(self):
        schema = self._make_schema_with_columns()
        assert schema.get_column("missing") is None

    def test_has_column(self):
        schema = self._make_schema_with_columns()

        assert schema.has_column("name") is True
        assert schema.has_column("Name") is True
        assert schema.has_column("nonexistent") is False

    def test_remove_column(self):
        schema = self._make_schema_with_columns()
        schema.remove_column("salary")

        assert "salary" not in schema.columns
        assert len(schema.columns) == 2

    def test_remove_column_nonexistent_no_error(self):
        schema = self._make_schema_with_columns()
        schema.remove_column("nonexistent")  # Should not raise
        assert len(schema.columns) == 3

    def test_rename_column(self):
        schema = self._make_schema_with_columns()
        schema.rename_column("salary", "annual_salary")

        assert "salary" not in schema.columns
        assert "annual_salary" in schema.columns
        assert schema.columns["annual_salary"].name == "annual_salary"
        assert schema.columns["annual_salary"].data_type == DataType.DOUBLE

    def test_rename_column_preserves_other_data(self):
        schema = self._make_schema_with_columns()
        schema.rename_column("name", "employee_name")

        col = schema.get_column("employee_name")
        assert col is not None
        assert col.length == 50
        assert col.data_type == DataType.STRING

    def test_rename_column_nonexistent_no_error(self):
        schema = self._make_schema_with_columns()
        schema.rename_column("nonexistent", "new_name")  # Should not raise
        assert len(schema.columns) == 3


class TestDatasetSchemaKeepDropRename:
    """Tests for apply_keep, apply_drop, apply_rename."""

    def _make_schema(self):
        schema = DatasetSchema(name="data", source_node_id="s1", created_by="DATA_STEP")
        schema.add_column(ColumnInfo(name="a", data_type=DataType.STRING))
        schema.add_column(ColumnInfo(name="b", data_type=DataType.INTEGER))
        schema.add_column(ColumnInfo(name="c", data_type=DataType.DOUBLE))
        schema.add_column(ColumnInfo(name="d", data_type=DataType.DATE))
        return schema

    def test_apply_keep(self):
        schema = self._make_schema()
        kept = schema.apply_keep(["a", "c"])

        assert kept.name == "data"
        assert len(kept.columns) == 2
        assert "a" in kept.columns
        assert "c" in kept.columns
        assert "b" not in kept.columns
        assert "d" not in kept.columns

    def test_apply_keep_preserves_metadata(self):
        schema = self._make_schema()
        kept = schema.apply_keep(["a"])

        assert kept.source_node_id == "s1"
        assert kept.created_by == "DATA_STEP"

    def test_apply_keep_case_insensitive(self):
        schema = self._make_schema()
        kept = schema.apply_keep(["A", "B"])

        assert len(kept.columns) == 2

    def test_apply_keep_nonexistent_vars(self):
        schema = self._make_schema()
        kept = schema.apply_keep(["a", "nonexistent"])

        assert len(kept.columns) == 1
        assert "a" in kept.columns

    def test_apply_keep_does_not_mutate_original(self):
        schema = self._make_schema()
        kept = schema.apply_keep(["a"])

        assert len(schema.columns) == 4  # Original unchanged

    def test_apply_drop(self):
        schema = self._make_schema()
        dropped = schema.apply_drop(["b", "d"])

        assert len(dropped.columns) == 2
        assert "a" in dropped.columns
        assert "c" in dropped.columns
        assert "b" not in dropped.columns
        assert "d" not in dropped.columns

    def test_apply_drop_preserves_metadata(self):
        schema = self._make_schema()
        dropped = schema.apply_drop(["a"])

        assert dropped.source_node_id == "s1"
        assert dropped.created_by == "DATA_STEP"

    def test_apply_drop_case_insensitive(self):
        schema = self._make_schema()
        dropped = schema.apply_drop(["A"])

        assert len(dropped.columns) == 3
        assert "a" not in dropped.columns

    def test_apply_drop_nonexistent_vars(self):
        schema = self._make_schema()
        dropped = schema.apply_drop(["nonexistent"])

        assert len(dropped.columns) == 4

    def test_apply_drop_does_not_mutate_original(self):
        schema = self._make_schema()
        schema.apply_drop(["a"])

        assert len(schema.columns) == 4

    def test_apply_rename(self):
        schema = self._make_schema()
        renamed = schema.apply_rename({"a": "alpha", "b": "beta"})

        assert "alpha" in renamed.columns
        assert "beta" in renamed.columns
        assert "a" not in renamed.columns
        assert "b" not in renamed.columns
        # Unchanged column
        assert "c" in renamed.columns

    def test_apply_rename_preserves_data(self):
        schema = self._make_schema()
        renamed = schema.apply_rename({"b": "new_b"})

        col = renamed.get_column("new_b")
        assert col is not None
        assert col.data_type == DataType.INTEGER

    def test_apply_rename_preserves_metadata(self):
        schema = self._make_schema()
        renamed = schema.apply_rename({"a": "new_a"})

        assert renamed.source_node_id == "s1"
        assert renamed.created_by == "DATA_STEP"

    def test_apply_rename_does_not_mutate_original(self):
        schema = self._make_schema()
        schema.apply_rename({"a": "new_a"})

        assert "a" in schema.columns


class TestDatasetSchemaMerge:
    """Tests for merge_schema."""

    def _make_schema_a(self):
        schema = DatasetSchema(name="employees")
        schema.add_column(ColumnInfo(name="id", data_type=DataType.INTEGER))
        schema.add_column(ColumnInfo(name="name", data_type=DataType.STRING))
        return schema

    def _make_schema_b(self):
        schema = DatasetSchema(name="departments")
        schema.add_column(ColumnInfo(name="dept_id", data_type=DataType.INTEGER))
        schema.add_column(ColumnInfo(name="dept_name", data_type=DataType.STRING))
        return schema

    def test_merge_distinct_columns(self):
        a = self._make_schema_a()
        b = self._make_schema_b()
        merged = a.merge_schema(b)

        assert len(merged.columns) == 4
        assert "id" in merged.columns
        assert "name" in merged.columns
        assert "dept_id" in merged.columns
        assert "dept_name" in merged.columns

    def test_merge_result_name(self):
        a = self._make_schema_a()
        b = self._make_schema_b()
        merged = a.merge_schema(b)

        assert merged.name == "employees_merged"
        assert merged.created_by == "MERGE"

    def test_merge_with_overlap_keeps_self(self):
        a = self._make_schema_a()
        b = DatasetSchema(name="b")
        b.add_column(ColumnInfo(name="name", data_type=DataType.DOUBLE))  # Conflict

        merged = a.merge_schema(b)
        # By default, prefer self
        assert merged.get_column("name").data_type == DataType.STRING

    def test_merge_with_overlap_prefer_other(self):
        a = self._make_schema_a()
        b = DatasetSchema(name="b")
        b.add_column(ColumnInfo(name="name", data_type=DataType.DOUBLE))

        merged = a.merge_schema(b, prefer_other=True)
        assert merged.get_column("name").data_type == DataType.DOUBLE

    def test_merge_does_not_mutate_originals(self):
        a = self._make_schema_a()
        b = self._make_schema_b()
        a.merge_schema(b)

        assert len(a.columns) == 2
        assert len(b.columns) == 2


class TestDatasetSchemaSerialization:
    """Tests for to_dict / from_dict round-trip."""

    def test_round_trip(self):
        schema = DatasetSchema(
            name="employees",
            source_node_id="s1",
            created_by="DATA_STEP",
            metadata={"libref": "work"},
        )
        schema.add_column(ColumnInfo(name="id", data_type=DataType.INTEGER))
        schema.add_column(
            ColumnInfo(name="salary", data_type=DataType.DOUBLE, format="DOLLAR12.2")
        )

        restored = DatasetSchema.from_dict(schema.to_dict())

        assert restored.name == "employees"
        assert restored.source_node_id == "s1"
        assert restored.created_by == "DATA_STEP"
        assert len(restored.columns) == 2
        assert restored.get_column("id").data_type == DataType.INTEGER
        assert restored.get_column("salary").format == "DOLLAR12.2"

    def test_to_dict_structure(self):
        schema = DatasetSchema(name="test")
        schema.add_column(ColumnInfo(name="x", data_type=DataType.STRING))

        d = schema.to_dict()
        assert d["name"] == "test"
        assert "columns" in d
        assert "x" in d["columns"]
        assert d["columns"]["x"]["data_type"] == "string"

    def test_round_trip_empty_schema(self):
        schema = DatasetSchema(name="empty")
        restored = DatasetSchema.from_dict(schema.to_dict())

        assert restored.name == "empty"
        assert len(restored.columns) == 0

    def test_str(self):
        schema = DatasetSchema(name="test_data")
        schema.add_column(ColumnInfo(name="a"))
        schema.add_column(ColumnInfo(name="b"))

        s = str(schema)
        assert "test_data" in s
        assert "2 columns" in s


# ===================================================================
# ExecutionContext Tests
# ===================================================================


class TestExecutionContextDatasets:
    """Tests for dataset operations in ExecutionContext."""

    def test_add_and_get_dataset(self):
        ctx = ExecutionContext()
        schema = DatasetSchema(name="employees")
        ctx.add_dataset(schema)

        retrieved = ctx.get_dataset("employees")
        assert retrieved is schema

    def test_get_dataset_case_insensitive(self):
        ctx = ExecutionContext()
        ctx.add_dataset(DatasetSchema(name="Employees"))

        assert ctx.get_dataset("employees") is not None
        assert ctx.get_dataset("EMPLOYEES") is not None
        assert ctx.get_dataset("Employees") is not None

    def test_has_dataset(self):
        ctx = ExecutionContext()
        ctx.add_dataset(DatasetSchema(name="data"))

        assert ctx.has_dataset("data") is True
        assert ctx.has_dataset("Data") is True
        assert ctx.has_dataset("missing") is False

    def test_update_dataset(self):
        ctx = ExecutionContext()
        ctx.add_dataset(DatasetSchema(name="data"))

        updated = DatasetSchema(name="data")
        updated.add_column(ColumnInfo(name="col1"))
        ctx.update_dataset("data", updated)

        retrieved = ctx.get_dataset("data")
        assert len(retrieved.columns) == 1

    def test_get_dataset_nonexistent(self):
        ctx = ExecutionContext()
        assert ctx.get_dataset("missing") is None


class TestExecutionContextVariableMapping:
    """Tests for SAS to PySpark variable name mapping."""

    def test_map_variable_name(self):
        ctx = ExecutionContext()
        ctx.map_variable_name("employee_data", "employee_df")

        assert ctx.get_pyspark_variable_name("employee_data") == "employee_df"

    def test_map_variable_name_case_insensitive(self):
        ctx = ExecutionContext()
        ctx.map_variable_name("Employee_Data", "employee_df")

        assert ctx.get_pyspark_variable_name("employee_data") == "employee_df"
        assert ctx.get_pyspark_variable_name("EMPLOYEE_DATA") == "employee_df"

    def test_get_pyspark_variable_name_unmapped(self):
        """Unmapped variables return the original name."""
        ctx = ExecutionContext()
        result = ctx.get_pyspark_variable_name("unmapped")
        assert result == "unmapped"

    def test_multiple_mappings(self):
        ctx = ExecutionContext()
        ctx.map_variable_name("sas_data1", "spark_df1")
        ctx.map_variable_name("sas_data2", "spark_df2")

        assert ctx.get_pyspark_variable_name("sas_data1") == "spark_df1"
        assert ctx.get_pyspark_variable_name("sas_data2") == "spark_df2"


class TestExecutionContextMacroVars:
    """Tests for macro variable tracking."""

    def test_add_and_resolve_macro_var(self):
        ctx = ExecutionContext()
        ctx.add_macro_var("max_rows", 1000)

        assert ctx.resolve_macro_var("max_rows") == 1000

    def test_resolve_macro_var_case_insensitive(self):
        ctx = ExecutionContext()
        ctx.add_macro_var("Max_Rows", 1000)

        assert ctx.resolve_macro_var("max_rows") == 1000

    def test_resolve_nonexistent(self):
        ctx = ExecutionContext()
        assert ctx.resolve_macro_var("missing") is None


class TestExecutionContextLibraries:
    """Tests for library reference tracking."""

    def test_add_and_get_library(self):
        ctx = ExecutionContext()
        ctx.add_library("mylib", "/data/projects")

        assert ctx.get_library("mylib") == "/data/projects"

    def test_library_case_insensitive(self):
        ctx = ExecutionContext()
        ctx.add_library("MyLib", "/data/projects")

        assert ctx.get_library("mylib") == "/data/projects"

    def test_library_nonexistent(self):
        ctx = ExecutionContext()
        assert ctx.get_library("missing") is None


class TestExecutionContextFileRefs:
    """Tests for file reference tracking."""

    def test_add_and_get_file_ref(self):
        ctx = ExecutionContext()
        ctx.add_file_ref("myfile", "/data/input.csv")

        assert ctx.get_file_ref("myfile") == "/data/input.csv"

    def test_file_ref_case_insensitive(self):
        ctx = ExecutionContext()
        ctx.add_file_ref("MyFile", "/data/input.csv")

        assert ctx.get_file_ref("myfile") == "/data/input.csv"


class TestExecutionContextConvertedCode:
    """Tests for converted code storage."""

    def test_add_and_get_converted_code(self):
        ctx = ExecutionContext()
        ctx.add_converted_code("chunk_1", "df = spark.read.csv(...)")

        assert ctx.get_converted_code("chunk_1") == "df = spark.read.csv(...)"

    def test_converted_code_nonexistent(self):
        ctx = ExecutionContext()
        assert ctx.get_converted_code("missing") is None


class TestExecutionContextSerialization:
    """Tests for to_dict."""

    def test_to_dict(self):
        ctx = ExecutionContext()
        ctx.add_dataset(DatasetSchema(name="data"))
        ctx.add_macro_var("n", 42)
        ctx.add_library("lib", "/path")
        ctx.add_file_ref("fref", "/file.csv")
        ctx.map_variable_name("sas_var", "spark_var")
        ctx.add_converted_code("c1", "code")

        d = ctx.to_dict()

        assert "datasets" in d
        assert "macro_vars" in d
        assert "libraries" in d
        assert "file_refs" in d
        assert "variable_name_map" in d
        assert d["converted_code_count"] == 1

    def test_str(self):
        ctx = ExecutionContext()
        ctx.add_dataset(DatasetSchema(name="d1"))
        ctx.add_dataset(DatasetSchema(name="d2"))
        ctx.add_macro_var("x", 1)
        ctx.add_converted_code("c1", "code")

        s = str(ctx)
        assert "datasets=2" in s
        assert "macro_vars=1" in s
        assert "converted_chunks=1" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
