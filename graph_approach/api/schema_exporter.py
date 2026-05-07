"""
Schema Exporter

Exports execution context schemas to JSON format for web visualization.
"""

from typing import Dict, List, Any
import json

from graph_approach.core.schema_tracker import (
    ExecutionContext,
    DatasetSchema,
    ColumnInfo,
)


class SchemaExporter:
    """
    Export schemas and execution context to web-friendly JSON format
    """

    @staticmethod
    def export_execution_context(context: ExecutionContext) -> Dict[str, Any]:
        """
        Export execution context to JSON

        Args:
            context: ExecutionContext to export

        Returns:
            Dictionary with datasets, variables, and mappings
        """
        # Export datasets with schemas
        datasets = {}
        for dataset_name, schema in context.datasets.items():
            datasets[dataset_name] = SchemaExporter.export_schema(schema)

        # Export macro variables
        macro_vars = dict(context.macro_vars)

        # Export variable name mappings
        variable_mappings = []
        for sas_name, pyspark_name in context.variable_name_map.items():
            variable_mappings.append({"sas": sas_name, "pyspark": pyspark_name})

        # Export converted code summary
        converted_chunks = []
        for chunk_id, code in context.converted_code.items():
            converted_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "has_code": bool(code and code.strip()),
                    "lines": len(code.split("\n")) if code else 0,
                }
            )

        return {
            "datasets": datasets,
            "macro_vars": macro_vars,
            "variable_mappings": variable_mappings,
            "converted_chunks": converted_chunks,
            "stats": {
                "total_datasets": len(datasets),
                "total_macro_vars": len(macro_vars),
                "total_mappings": len(variable_mappings),
                "total_converted_chunks": len(converted_chunks),
            },
        }

    @staticmethod
    def export_schema(schema: DatasetSchema) -> Dict[str, Any]:
        """
        Export dataset schema to JSON

        Args:
            schema: DatasetSchema to export

        Returns:
            Dictionary with schema details
        """
        columns = []
        for col in schema.columns.values():
            columns.append(
                {
                    "name": col.name,
                    "data_type": col.data_type.value if col.data_type else "UNKNOWN",
                    "length": col.length,
                    "format": col.format,
                    "label": col.label,
                    "source": col.source,
                }
            )

        return {
            "name": schema.name,
            "columns": columns,
            "total_columns": len(columns),
            "source_node_id": schema.source_node_id,
            "created_by": schema.created_by,
            "metadata": schema.metadata,
        }

    @staticmethod
    def export_variable_flow(context: ExecutionContext) -> Dict[str, Any]:
        """
        Export variable name flow for Sankey diagram

        Args:
            context: ExecutionContext

        Returns:
            Dictionary with nodes and links for Sankey diagram
        """
        nodes = []
        links = []
        node_map = {}

        # Create nodes for SAS and PySpark variable names
        index = 0
        for sas_name, pyspark_name in context.variable_name_map.items():
            # SAS node
            if sas_name not in node_map:
                node_map[sas_name] = index
                nodes.append({"name": sas_name, "category": "sas"})
                index += 1

            # PySpark node
            if pyspark_name not in node_map:
                node_map[pyspark_name] = index
                nodes.append({"name": pyspark_name, "category": "pyspark"})
                index += 1

            # Link
            links.append(
                {
                    "source": node_map[sas_name],
                    "target": node_map[pyspark_name],
                    "value": 1,
                }
            )

        return {"nodes": nodes, "links": links}

    @staticmethod
    def export_schema_transformations(
        context: ExecutionContext,
    ) -> List[Dict[str, Any]]:
        """
        Export schema transformation history

        Args:
            context: ExecutionContext

        Returns:
            List of transformation events
        """
        transformations = []

        for dataset_name, schema in context.datasets.items():
            # Check for KEEP/DROP/RENAME operations in metadata
            if hasattr(schema, "metadata") and schema.metadata:
                if "transformations" in schema.metadata:
                    for transform in schema.metadata["transformations"]:
                        transformations.append(
                            {
                                "dataset": dataset_name,
                                "operation": transform.get("type", "UNKNOWN"),
                                "columns": transform.get("columns", []),
                                "details": transform.get("details", ""),
                            }
                        )

        return transformations

    @staticmethod
    def export_to_file(context: ExecutionContext, output_path: str) -> bool:
        """
        Export execution context to JSON file

        Args:
            context: ExecutionContext to export
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            data = SchemaExporter.export_execution_context(context)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error exporting schemas: {e}")
            return False
