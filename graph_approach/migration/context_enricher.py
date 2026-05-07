"""
Context Enricher

Builds rich context from dependency graph for LLM prompts.
Combines schema information, dependencies, and examples.
"""

from typing import Dict, List, Any, Optional
from graph_approach.core.chunk_optimizer import Chunk
from graph_approach.core.dependency_graph import DependencyGraph, NodeType
from graph_approach.core.schema_tracker import ExecutionContext, DatasetSchema
from graph_approach.rag.example_retriever import ExampleRetriever


class EnrichedContext:
    """
    Enriched context for a chunk migration

    Contains all information needed for high-quality LLM conversion.
    """

    def __init__(self):
        """Initialize enriched context"""
        self.chunk_info: Dict[str, Any] = {}
        self.dependency_info: Dict[str, Any] = {}
        self.schema_info: Dict[str, Any] = {}
        self.examples: List[Dict] = []
        self.execution_context: Dict[str, Any] = {}
        self.migration_guide: str = ""
        self.additional_context: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chunk_info": self.chunk_info,
            "dependency_info": self.dependency_info,
            "schema_info": self.schema_info,
            "examples": self.examples,
            "execution_context": self.execution_context,
            "has_migration_guide": bool(self.migration_guide),
            "additional_context": self.additional_context
        }


class ContextEnricher:
    """
    Build rich context for chunk migration

    Combines information from:
    - Dependency graph (what depends on what)
    - Execution context (schemas, variables)
    - Similar examples (RAG)
    - Migration guide
    """

    def __init__(
        self,
        graph: DependencyGraph,
        execution_context: ExecutionContext,
        example_retriever: Optional[ExampleRetriever] = None,
        migration_guide: Optional[str] = None
    ):
        """
        Initialize context enricher

        Args:
            graph: Dependency graph
            execution_context: Current execution context
            example_retriever: RAG example retriever
            migration_guide: Migration guide text
        """
        self.graph = graph
        self.execution_context = execution_context
        self.example_retriever = example_retriever
        self.migration_guide = migration_guide or ""

    def enrich_chunk_context(self, chunk: Chunk) -> EnrichedContext:
        """
        Build enriched context for a chunk

        Args:
            chunk: Chunk to enrich

        Returns:
            EnrichedContext with all information
        """
        context = EnrichedContext()

        # Add chunk information
        context.chunk_info = self._build_chunk_info(chunk)

        # Add dependency information
        context.dependency_info = self._build_dependency_info(chunk)

        # Add schema information
        context.schema_info = self._build_schema_info(chunk)

        # Add examples from RAG
        if self.example_retriever:
            example_context = self.example_retriever.create_example_context(chunk)
            context.examples = example_context.get('examples', [])

        # Add execution context info
        context.execution_context = self._build_execution_context_info()

        # Add migration guide
        context.migration_guide = self.migration_guide

        return context

    def _build_chunk_info(self, chunk: Chunk) -> Dict[str, Any]:
        """Build chunk-specific information"""
        info = {
            "chunk_id": chunk.chunk_id,
            "source_code": chunk.source_code,
            "estimated_tokens": chunk.estimated_tokens,
            "layer": chunk.layer,
            "node_count": len(chunk.nodes),
            "node_types": [n.node_type.value for n in chunk.nodes],
            "node_names": [n.name for n in chunk.nodes],
            "has_macros": any(n.node_type == NodeType.MACRO for n in chunk.nodes),
            "has_data_steps": any(n.node_type == NodeType.DATA_STEP for n in chunk.nodes),
            "has_procs": any(n.node_type == NodeType.PROC for n in chunk.nodes),
        }

        # Detect cAST-split chunks and add context
        for node in chunk.nodes:
            if node.metadata.get('cast_split'):
                info['is_cast_split'] = True
                info['cast_parent_node_id'] = node.metadata.get('parent_node_id', '')
                info['cast_part_index'] = node.metadata.get('part_index', 0)
                info['cast_total_parts'] = node.metadata.get('total_parts', 1)
                info['cast_context_header'] = node.metadata.get('context_header', '')
                break

        return info

    def _build_dependency_info(self, chunk: Chunk) -> Dict[str, Any]:
        """Build dependency information for chunk"""
        dependencies = []
        dependents = []

        for node in chunk.nodes:
            # Get what this node depends on
            node_deps = self.graph.get_dependencies(node.node_id, depth=1)
            for dep in node_deps:
                dependencies.append({
                    "node_id": dep.node_id,
                    "node_type": dep.node_type.value,
                    "name": dep.name
                })

            # Get what depends on this node
            node_dependents = self.graph.get_dependents(node.node_id, depth=1)
            for dep in node_dependents:
                dependents.append({
                    "node_id": dep.node_id,
                    "node_type": dep.node_type.value,
                    "name": dep.name
                })

        return {
            "dependencies": dependencies,
            "dependents": dependents,
            "dependency_count": len(dependencies),
            "dependent_count": len(dependents)
        }

    def _build_schema_info(self, chunk: Chunk) -> Dict[str, Any]:
        """Build schema information for datasets in chunk"""
        schemas = {}

        for node in chunk.nodes:
            # For DATA steps, get input and output schemas
            if node.node_type == NodeType.DATA_STEP:
                # Get input datasets
                input_deps = self.graph.get_dependencies(node.node_id, depth=1)
                for dep in input_deps:
                    if dep.node_type == NodeType.DATASET:
                        schema = self.execution_context.get_dataset(dep.name)
                        if schema:
                            schemas[f"input_{dep.name}"] = self._format_schema(schema)

                # Get output datasets
                output_deps = self.graph.get_dependents(node.node_id, depth=1)
                for dep in output_deps:
                    if dep.node_type == NodeType.DATASET:
                        schema = self.execution_context.get_dataset(dep.name)
                        if schema:
                            schemas[f"output_{dep.name}"] = self._format_schema(schema)

            # For PROCs, get input schemas
            elif node.node_type == NodeType.PROC:
                input_deps = self.graph.get_dependencies(node.node_id, depth=1)
                for dep in input_deps:
                    if dep.node_type == NodeType.DATASET:
                        schema = self.execution_context.get_dataset(dep.name)
                        if schema:
                            schemas[f"proc_input_{dep.name}"] = self._format_schema(schema)

        return {
            "schemas": schemas,
            "num_schemas": len(schemas)
        }

    def _format_schema(self, schema: DatasetSchema) -> Dict[str, Any]:
        """Format schema for context"""
        return {
            "name": schema.name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type.value,
                    "format": col.format,
                    "label": col.label
                }
                for col in schema.columns.values()
            ],
            "column_count": len(schema.columns)
        }

    def _build_execution_context_info(self) -> Dict[str, Any]:
        """Build information from execution context"""
        return {
            "datasets_available": list(self.execution_context.datasets.keys()),
            "macro_variables": list(self.execution_context.macro_vars.keys()),
            "libraries": list(self.execution_context.libraries.keys()),
            "variable_mappings": dict(self.execution_context.variable_name_map),
            "num_converted_chunks": len(self.execution_context.converted_code)
        }

    def build_llm_prompt(
        self,
        chunk: Chunk,
        enriched_context: EnrichedContext,
        include_examples: bool = True,
        include_schemas: bool = True
    ) -> str:
        """
        Build complete LLM prompt with enriched context

        Args:
            chunk: Chunk to convert
            enriched_context: Enriched context
            include_examples: Whether to include similar examples
            include_schemas: Whether to include schema information

        Returns:
            Complete prompt string
        """
        prompt = """You are an expert in SAS and PySpark migration. Convert the following SAS code to production-ready PySpark.

"""

        # Add migration guide context
        if enriched_context.migration_guide:
            prompt += """MIGRATION GUIDE:
{migration_guide}

""".format(migration_guide=enriched_context.migration_guide[:2000])  # Limit guide size

        # Add schema information
        if include_schemas and enriched_context.schema_info.get('schemas'):
            prompt += "DATASET SCHEMAS:\n"
            for schema_name, schema_info in enriched_context.schema_info['schemas'].items():
                prompt += f"\n{schema_name} ({schema_info['column_count']} columns):\n"
                for col in schema_info['columns'][:10]:  # Limit columns shown
                    prompt += f"  - {col['name']}: {col['type']}"
                    if col.get('format'):
                        prompt += f" (format: {col['format']})"
                    prompt += "\n"
            prompt += "\n"

        # Add dependency information
        if enriched_context.dependency_info.get('dependencies'):
            prompt += "DEPENDENCIES:\n"
            prompt += "This code depends on:\n"
            for dep in enriched_context.dependency_info['dependencies'][:5]:
                prompt += f"  - {dep['name']} ({dep['node_type']})\n"
            prompt += "\n"

        # Add variable mappings
        if enriched_context.execution_context.get('variable_mappings'):
            prompt += "VARIABLE NAME MAPPINGS (SAS → PySpark):\n"
            for sas_name, pyspark_name in enriched_context.execution_context['variable_mappings'].items():
                prompt += f"  - {sas_name} → {pyspark_name}\n"
            prompt += "\n"

        # Add similar examples
        if include_examples and self.example_retriever and enriched_context.examples:
            from graph_approach.rag.example_retriever import MigrationPattern
            patterns = [MigrationPattern(**e) for e in enriched_context.examples]
            examples_text = self.example_retriever.format_examples_for_prompt(patterns)
            prompt += examples_text
            prompt += "\n"

        # Add cAST sub-chunk context if applicable
        chunk_info = enriched_context.chunk_info
        if chunk_info.get('is_cast_split'):
            part = chunk_info.get('cast_part_index', 0) + 1
            total = chunk_info.get('cast_total_parts', 1)
            header = chunk_info.get('cast_context_header', '')
            prompt += f"IMPORTANT CONTEXT - This is Part {part} of {total} from a larger SAS construct.\n"
            if header:
                prompt += f"Enclosing construct: {header}\n"
            prompt += "Convert only the code below. The other parts are being converted separately.\n\n"

        # Add the actual code to convert
        prompt += """SAS CODE TO CONVERT:
```sas
{sas_code}
```

INSTRUCTIONS:
1. Convert to PySpark using the migration guide mappings
2. Use the provided schema information for type safety
3. Follow the variable naming conventions from the mappings
4. Maintain the original business logic
5. Add helpful comments explaining transformations
6. Follow PySpark best practices

Return exactly one raw JSON object. Do not include markdown fences, prose, headings, or explanations outside the JSON.
Use pyspark_code_lines so code lines do not need embedded newline escaping:
{{
    "pyspark_code_lines": ["converted PySpark code line 1", "converted PySpark code line 2"],
    "mapping": "Concise conversion summary in 1-3 sentences",
    "variables_created": ["list", "of", "new", "dataframe", "names"]
}}
Keep mapping concise. Put only executable PySpark code in pyspark_code_lines.
""".format(sas_code=chunk.source_code)

        return prompt
