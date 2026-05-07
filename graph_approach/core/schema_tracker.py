"""
Schema Tracker

Tracks dataset schemas through SAS transformations to maintain
type information and column metadata throughout the migration process.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from copy import deepcopy


class DataType(Enum):
    """Data types for columns"""

    STRING = "string"
    INTEGER = "integer"
    DOUBLE = "double"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


@dataclass
class ColumnInfo:
    """
    Information about a column in a dataset

    Attributes:
        name: Column name
        data_type: Data type
        format: SAS format (e.g., "DATE9.", "DOLLAR12.2")
        label: Column label/description
        length: Column length (for strings)
        source: How this column was created (assignment, input, etc.)
    """

    name: str
    data_type: DataType = DataType.UNKNOWN
    format: Optional[str] = None
    label: Optional[str] = None
    length: Optional[int] = None
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "format": self.format,
            "label": self.label,
            "length": self.length,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnInfo":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            data_type=DataType(data.get("data_type", "unknown")),
            format=data.get("format"),
            label=data.get("label"),
            length=data.get("length"),
            source=data.get("source"),
        )


@dataclass
class DatasetSchema:
    """
    Schema for a SAS dataset

    Attributes:
        name: Dataset name
        columns: Dictionary of column name -> ColumnInfo
        source_node_id: Graph node ID that created this dataset
        created_by: Type of step that created it (DATA, PROC SQL, etc.)
        metadata: Additional metadata
    """

    name: str
    columns: Dict[str, ColumnInfo] = field(default_factory=dict)
    source_node_id: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_column(self, column: ColumnInfo) -> None:
        """Add a column to the schema"""
        self.columns[column.name] = column

    def remove_column(self, name: str) -> None:
        """Remove a column from the schema"""
        if name in self.columns:
            del self.columns[name]

    def rename_column(self, old_name: str, new_name: str) -> None:
        """Rename a column"""
        if old_name in self.columns:
            col = self.columns[old_name]
            col.name = new_name
            self.columns[new_name] = col
            del self.columns[old_name]

    def get_column(self, name: str) -> Optional[ColumnInfo]:
        """Get column by name (case-insensitive)"""
        # Try exact match first
        if name in self.columns:
            return self.columns[name]
        # Try case-insensitive
        for col_name, col_info in self.columns.items():
            if col_name.lower() == name.lower():
                return col_info
        return None

    def has_column(self, name: str) -> bool:
        """Check if schema has a column (case-insensitive)"""
        return self.get_column(name) is not None

    def merge_schema(
        self, other: "DatasetSchema", prefer_other: bool = False
    ) -> "DatasetSchema":
        """
        Merge this schema with another schema (for MERGE statements)

        Args:
            other: Schema to merge with
            prefer_other: If True, prefer other's column info on conflicts

        Returns:
            New merged schema
        """
        merged = DatasetSchema(
            name=f"{self.name}_merged", source_node_id=None, created_by="MERGE"
        )

        # Add columns from self
        for col_name, col_info in self.columns.items():
            merged.add_column(deepcopy(col_info))

        # Add/update columns from other
        for col_name, col_info in other.columns.items():
            if col_name in merged.columns and not prefer_other:
                # Column exists, keep existing unless prefer_other
                continue
            merged.add_column(deepcopy(col_info))

        return merged

    def apply_keep(self, keep_vars: List[str]) -> "DatasetSchema":
        """
        Apply KEEP statement to schema

        Args:
            keep_vars: List of variables to keep

        Returns:
            New schema with only kept variables
        """
        new_schema = DatasetSchema(
            name=self.name,
            source_node_id=self.source_node_id,
            created_by=self.created_by,
        )

        keep_vars_lower = [v.lower() for v in keep_vars]
        for col_name, col_info in self.columns.items():
            if col_name.lower() in keep_vars_lower:
                new_schema.add_column(deepcopy(col_info))

        return new_schema

    def apply_drop(self, drop_vars: List[str]) -> "DatasetSchema":
        """
        Apply DROP statement to schema

        Args:
            drop_vars: List of variables to drop

        Returns:
            New schema without dropped variables
        """
        new_schema = DatasetSchema(
            name=self.name,
            source_node_id=self.source_node_id,
            created_by=self.created_by,
        )

        drop_vars_lower = [v.lower() for v in drop_vars]
        for col_name, col_info in self.columns.items():
            if col_name.lower() not in drop_vars_lower:
                new_schema.add_column(deepcopy(col_info))

        return new_schema

    def apply_rename(self, rename_map: Dict[str, str]) -> "DatasetSchema":
        """
        Apply RENAME statement to schema

        Args:
            rename_map: Dictionary of old_name -> new_name

        Returns:
            New schema with renamed variables
        """
        new_schema = DatasetSchema(
            name=self.name,
            source_node_id=self.source_node_id,
            created_by=self.created_by,
        )

        # Create case-insensitive rename map
        rename_map_lower = {k.lower(): v for k, v in rename_map.items()}

        for col_name, col_info in self.columns.items():
            new_col = deepcopy(col_info)
            if col_name.lower() in rename_map_lower:
                new_col.name = rename_map_lower[col_name.lower()]
            new_schema.add_column(new_col)

        return new_schema

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary"""
        return {
            "name": self.name,
            "columns": {name: col.to_dict() for name, col in self.columns.items()},
            "source_node_id": self.source_node_id,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetSchema":
        """Create schema from dictionary"""
        schema = cls(
            name=data["name"],
            source_node_id=data.get("source_node_id"),
            created_by=data.get("created_by"),
            metadata=data.get("metadata", {}),
        )
        for col_data in data.get("columns", {}).values():
            schema.add_column(ColumnInfo.from_dict(col_data))
        return schema

    def __str__(self) -> str:
        return f"DatasetSchema({self.name}, {len(self.columns)} columns)"


class ExecutionContext:
    """
    Maintains execution context during migration

    Tracks datasets, macro variables, libraries, and converted code
    as the migration progresses.
    """

    def __init__(self):
        """Initialize empty execution context"""
        self.datasets: Dict[str, DatasetSchema] = {}
        self.macro_vars: Dict[str, Any] = {}
        self.libraries: Dict[str, str] = {}
        self.file_refs: Dict[str, str] = {}
        self.converted_code: Dict[str, str] = {}  # chunk_id -> pyspark code
        self.variable_name_map: Dict[str, str] = {}  # SAS var -> PySpark var

    def add_dataset(self, schema: DatasetSchema) -> None:
        """Add a dataset schema to the context"""
        self.datasets[schema.name.lower()] = schema

    def get_dataset(self, name: str) -> Optional[DatasetSchema]:
        """Get a dataset schema by name (case-insensitive)"""
        return self.datasets.get(name.lower())

    def has_dataset(self, name: str) -> bool:
        """Check if a dataset exists in context"""
        return name.lower() in self.datasets

    def update_dataset(self, name: str, schema: DatasetSchema) -> None:
        """Update a dataset schema"""
        self.datasets[name.lower()] = schema

    def add_macro_var(self, name: str, value: Any) -> None:
        """Add a macro variable to the context"""
        self.macro_vars[name.lower()] = value

    def resolve_macro_var(self, name: str) -> Optional[Any]:
        """Resolve a macro variable value"""
        return self.macro_vars.get(name.lower())

    def add_library(self, libref: str, path: str) -> None:
        """Add a library reference"""
        self.libraries[libref.lower()] = path

    def get_library(self, libref: str) -> Optional[str]:
        """Get a library path"""
        return self.libraries.get(libref.lower())

    def add_file_ref(self, fileref: str, path: str) -> None:
        """Add a file reference"""
        self.file_refs[fileref.lower()] = path

    def get_file_ref(self, fileref: str) -> Optional[str]:
        """Get a file path"""
        return self.file_refs.get(fileref.lower())

    def add_converted_code(self, chunk_id: str, code: str) -> None:
        """Add converted PySpark code for a chunk"""
        self.converted_code[chunk_id] = code

    def get_converted_code(self, chunk_id: str) -> Optional[str]:
        """Get converted code for a chunk"""
        return self.converted_code.get(chunk_id)

    def map_variable_name(self, sas_name: str, pyspark_name: str) -> None:
        """Map a SAS variable name to its PySpark equivalent"""
        self.variable_name_map[sas_name.lower()] = pyspark_name

    def get_pyspark_variable_name(self, sas_name: str) -> str:
        """Get PySpark variable name for a SAS variable (or return original)"""
        return self.variable_name_map.get(sas_name.lower(), sas_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "datasets": {
                name: schema.to_dict() for name, schema in self.datasets.items()
            },
            "macro_vars": self.macro_vars,
            "libraries": self.libraries,
            "file_refs": self.file_refs,
            "variable_name_map": self.variable_name_map,
            "converted_code_count": len(self.converted_code),
        }

    def __str__(self) -> str:
        return (
            f"ExecutionContext(datasets={len(self.datasets)}, "
            f"macro_vars={len(self.macro_vars)}, "
            f"converted_chunks={len(self.converted_code)})"
        )


class SchemaInferencer:
    """
    Infer dataset schemas from SAS code

    This class analyzes SAS statements to infer column types and schemas.
    """

    def __init__(self):
        """Initialize schema inferencer"""
        pass

    def infer_from_data_step(
        self,
        data_step: Dict[str, Any],
        input_schemas: List[DatasetSchema],
        context: ExecutionContext,
    ) -> DatasetSchema:
        """
        Infer output schema from a DATA step

        Args:
            data_step: Parsed DATA step dictionary
            input_schemas: Schemas of input datasets (from SET/MERGE)
            context: Current execution context

        Returns:
            Inferred schema for output dataset
        """
        output_name = data_step.get("output_datasets", "unknown")
        if " " in output_name:
            output_name = output_name.split()[0]

        schema = DatasetSchema(name=output_name, created_by="DATA_STEP")

        # Start with columns from input schemas (SET/MERGE)
        for input_schema in input_schemas:
            for col_name, col_info in input_schema.columns.items():
                if not schema.has_column(col_name):
                    schema.add_column(deepcopy(col_info))

        # Parse body for new column assignments, transformations
        body = data_step.get("body", "")

        # Extract LENGTH statements
        length_matches = self._extract_length_statements(body)
        for var_name, length in length_matches.items():
            col = schema.get_column(var_name)
            if col:
                col.length = length
                if length and col.data_type == DataType.UNKNOWN:
                    col.data_type = DataType.STRING
            else:
                schema.add_column(
                    ColumnInfo(
                        name=var_name,
                        data_type=DataType.STRING,
                        length=length,
                        source="LENGTH statement",
                    )
                )

        # Extract FORMAT statements
        format_matches = self._extract_format_statements(body)
        for var_name, format_str in format_matches.items():
            col = schema.get_column(var_name)
            if col:
                col.format = format_str
                # Infer type from format
                inferred_type = self._infer_type_from_format(format_str)
                if inferred_type and col.data_type == DataType.UNKNOWN:
                    col.data_type = inferred_type

        # Extract LABEL statements
        label_matches = self._extract_label_statements(body)
        for var_name, label in label_matches.items():
            col = schema.get_column(var_name)
            if col:
                col.label = label

        # TODO: Extract assignment statements to infer new columns

        return schema

    def _extract_length_statements(self, body: str) -> Dict[str, int]:
        """Extract LENGTH statements"""
        lengths = {}
        pattern = r"LENGTH\s+([^;]+);"
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            # Parse "var1 $20 var2 $30" format
            parts = match.split()
            var_name = None
            for part in parts:
                if part.startswith("$"):
                    # Length specification
                    try:
                        length = int(part[1:])
                        if var_name:
                            lengths[var_name] = length
                    except ValueError:
                        pass
                elif part.isdigit():
                    if var_name:
                        lengths[var_name] = int(part)
                else:
                    var_name = part
        return lengths

    def _extract_format_statements(self, body: str) -> Dict[str, str]:
        """Extract FORMAT statements"""
        formats = {}
        pattern = r"FORMAT\s+([^;]+);"
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            parts = match.split()
            if len(parts) >= 2:
                var_name = parts[0]
                format_str = parts[1]
                formats[var_name] = format_str
        return formats

    def _extract_label_statements(self, body: str) -> Dict[str, str]:
        """Extract LABEL statements"""
        labels = {}
        pattern = r"LABEL\s+([^;]+);"
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            # Parse "var1='Label 1' var2='Label 2'" format
            label_pattern = r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
            for var_match in re.finditer(label_pattern, match):
                var_name = var_match.group(1)
                label = var_match.group(2)
                labels[var_name] = label
        return labels

    def _infer_type_from_format(self, format_str: str) -> Optional[DataType]:
        """Infer data type from SAS format"""
        format_lower = format_str.lower()
        if "date" in format_lower:
            return DataType.DATE
        elif "datetime" in format_lower or "time" in format_lower:
            return DataType.DATETIME
        elif format_lower.startswith("$"):
            return DataType.STRING
        elif any(x in format_lower for x in ["dollar", "comma", "percent"]):
            return DataType.DOUBLE
        elif format_lower.startswith("z") or "best" in format_lower:
            return DataType.DOUBLE
        return None
