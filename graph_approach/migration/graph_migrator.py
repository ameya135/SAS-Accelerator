"""
Graph Migrator

Main orchestrator for graph-based SAS to PySpark migration.
Coordinates graph building, chunking, and LLM-based conversion.
Supports parallel chunk conversion using async LLM calls.
"""

import os
import json
import asyncio
import traceback
import random
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AzureOpenAI,
    OpenAI,
)
from dotenv import load_dotenv

from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.core.chunk_optimizer import ChunkOptimizer, Chunk
from graph_approach.core.schema_tracker import ExecutionContext, SchemaInferencer
from graph_approach.rag.pattern_store import PatternStore
from graph_approach.rag.example_retriever import ExampleRetriever
from graph_approach.migration.context_enricher import ContextEnricher
from graph_approach.migration.code_reconciler import CodeReconciler
from graph_approach.migration.variable_tracker import VariableTracker
from graph_approach.migration.execution_order import ExecutionOrderOptimizer

# Import SAS parser for macro variable extraction
try:
    from parser.sas_code_parser import SASParser
except ImportError:
    SASParser = None

# Import AST components for advanced parsing (Phase 2)
try:
    from graph_approach.ast.sas_lexer import SASLexer
    from graph_approach.ast.sas_ast import SASASTParser
    from graph_approach.ast.semantic_analyzer import SemanticAnalyzer

    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False


@dataclass
class MigrationResult:
    """Result of a migration"""

    success: bool
    sas_file: str
    pyspark_code: str = ""
    mapping: str = ""
    chunks_converted: int = 0
    total_chunks: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    validation_report: str = ""
    fixes_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "sas_file": self.sas_file,
            "pyspark_code": self.pyspark_code,
            "mapping": self.mapping,
            "chunks_converted": self.chunks_converted,
            "total_chunks": self.total_chunks,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "validation_report": self.validation_report,
            "fixes_applied": self.fixes_applied,
        }


class GraphMigrator:
    """
    Graph-based SAS to PySpark migrator

    Orchestrates the complete migration process using dependency
    analysis, schema tracking, and RAG-enhanced LLM conversion.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        model: Optional[str] = None,
        use_rag: bool = True,
        pattern_store_path: Optional[str] = None,
        migration_guide_path: Optional[str] = None,
        max_concurrent: int = 5,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        allow_partial_output: bool = True,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize graph migrator

        Args:
            api_key: LLM API key (or from provider-specific env)
            azure_endpoint: Azure OpenAI endpoint, or OpenAI-compatible base URL
                for non-Azure providers when base_url is not set
            model: Model or Azure deployment name to use for migration
            use_rag: Whether to use RAG for examples
            pattern_store_path: Path to pattern store DB
            migration_guide_path: Path to migration guide
            max_concurrent: Maximum concurrent LLM calls (default 5)
            provider: LLM provider: "azure" or "openrouter"
            base_url: OpenAI-compatible base URL for non-Azure providers
            max_retries: Maximum retry attempts for transient LLM failures
            allow_partial_output: Whether to write .py output when some chunks fail
            max_tokens: Maximum completion tokens for chunk conversion calls
        """
        # Load environment variables
        load_dotenv()

        self.provider = self._normalize_provider(provider or os.getenv("LLM_PROVIDER"))
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.allow_partial_output = allow_partial_output
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "12000"))
        self.base_url = None
        self.azure_endpoint = None

        self._configure_llm_clients(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            model=model,
            base_url=base_url,
        )

        # Load migration guide
        self.migration_guide = self._load_migration_guide(migration_guide_path)

        # Initialize RAG components
        self.use_rag = use_rag
        if use_rag:
            self.pattern_store = PatternStore(db_path=pattern_store_path)
            # Initialize with migration guide examples
            if self.pattern_store.count_patterns() == 0:
                self.pattern_store.initialize_with_examples(migration_guide_path)
            self.example_retriever = ExampleRetriever(self.pattern_store)
        else:
            self.pattern_store = None
            self.example_retriever = None

        self.schema_inferencer = SchemaInferencer()

        # Initialize code reconciler
        self.code_reconciler = CodeReconciler(
            use_llm=True,
            llm_client=self.client,
            llm_model=self.model,
        )

    def _normalize_provider(self, provider: Optional[str]) -> str:
        """Normalize provider aliases to internal names."""
        normalized = (provider or "azure").strip().lower().replace("_", "-")
        aliases = {
            "azure-openai": "azure",
            "openrouter-ai": "openrouter",
        }
        normalized = aliases.get(normalized, normalized)

        if normalized not in {"azure", "openrouter"}:
            raise ValueError(
                f"Unsupported LLM provider '{provider}'. Supported providers: azure, openrouter"
            )

        return normalized

    def _configure_llm_clients(
        self,
        api_key: Optional[str],
        azure_endpoint: Optional[str],
        model: Optional[str],
        base_url: Optional[str],
    ) -> None:
        """Configure sync and async OpenAI-compatible clients."""
        if self.provider == "azure":
            self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
            self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            self.model = (
                model
                or os.getenv("AZURE_OPENAI_MODEL")
                or os.getenv("DEFAULT_LLM_MODEL")
                or "gpt-4"
            )

            if not self.api_key or not self.azure_endpoint:
                raise ValueError(
                    "Azure OpenAI credentials not provided. Set AZURE_OPENAI_API_KEY "
                    "and AZURE_OPENAI_ENDPOINT, or pass --api-key and --endpoint."
                )

            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-08-01-preview",
                azure_endpoint=self.azure_endpoint,
            )
            self.async_client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version="2024-08-01-preview",
                azure_endpoint=self.azure_endpoint,
            )
            return

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = (
            base_url
            or azure_endpoint
            or os.getenv("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1"
        )
        self.model = (
            model
            or os.getenv("OPENROUTER_MODEL")
            or os.getenv("DEFAULT_LLM_MODEL")
            or "qwen/qwen-2.5-coder-32b-instruct"
        )

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY or pass --api-key."
            )

        default_headers = {}
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        app_name = os.getenv("OPENROUTER_APP_NAME") or "SAS Accelerator"
        if referer:
            default_headers["HTTP-Referer"] = referer
        if app_name:
            default_headers["X-Title"] = app_name

        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url,
        }
        if default_headers:
            client_kwargs["default_headers"] = default_headers

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    def _migration_response_format(self) -> Dict[str, Any]:
        """Return the response format expected from the migration LLM."""
        if self.provider != "openrouter":
            return {"type": "json_object"}

        mode = os.getenv("OPENROUTER_RESPONSE_FORMAT", "none").strip().lower()
        if mode in {"none", "off", "false", "disabled"}:
            return {}
        if mode == "json_object":
            return {"type": "json_object"}
        if mode != "json_schema":
            raise ValueError(
                "OPENROUTER_RESPONSE_FORMAT must be one of: none, json_object, json_schema"
            )

        return self._migration_json_schema_response_format()

    def _migration_json_schema_response_format(self) -> Dict[str, Any]:
        """Return the strict JSON schema response format."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "sas_migration_chunk",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "pyspark_code_lines": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Production-ready PySpark code lines converted from the SAS chunk.",
                        },
                        "mapping": {
                            "type": "string",
                            "description": "Concise explanation of how SAS constructs map to PySpark.",
                        },
                        "variables_created": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "PySpark DataFrame or variable names created by the converted code.",
                        },
                    },
                    "required": ["pyspark_code_lines", "mapping", "variables_created"],
                    "additionalProperties": False,
                },
            },
        }

    def _completion_extra_body(self) -> Optional[Dict[str, Any]]:
        """OpenRouter-specific request hints."""
        if self.provider != "openrouter":
            return None

        extra_body: Dict[str, Any] = {}
        if os.getenv("OPENROUTER_REQUIRE_PARAMETERS", "false").lower() == "true":
            extra_body["provider"] = {"require_parameters": True}
        if os.getenv("OPENROUTER_RESPONSE_HEALING", "false").lower() == "true":
            extra_body["plugins"] = [{"id": "response-healing"}]
        return extra_body or None

    def _chat_kwargs(self, prompt: str) -> Dict[str, Any]:
        """Build chat completion keyword arguments."""
        system_message = (
            "You are a SAS to PySpark migration engine. Return exactly one raw JSON "
            "object and nothing else. Do not use markdown fences, headings, prose, "
            "or comments outside JSON. The first character of your response must be "
            "'{' and the last character must be '}'. Prefer the field "
            "'pyspark_code_lines' as an array of code lines; include 'mapping' and "
            "'variables_created'. Keep mapping concise. Do not omit closing brackets "
            "or braces."
        )
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
        }
        response_format = self._migration_response_format()
        if response_format:
            kwargs["response_format"] = response_format
        extra_body = self._completion_extra_body()
        if extra_body:
            kwargs["extra_body"] = extra_body
        return kwargs

    def _is_retryable_llm_error(self, error: Exception) -> bool:
        """Return whether an LLM exception is likely transient."""
        if isinstance(error, (APIConnectionError, APITimeoutError)):
            return True
        if isinstance(error, APIStatusError):
            return error.status_code in {408, 409, 429, 500, 502, 503, 504}
        return False

    def _retry_delay(self, attempt: int) -> float:
        """Compute capped exponential backoff with jitter."""
        return min(2**attempt, 8) + random.uniform(0, 0.5)

    def _extract_response_text(self, completion: Any) -> str:
        """Extract text from an OpenAI-compatible chat completion."""
        choices = getattr(completion, "choices", None) or []
        if not choices:
            raise ValueError("LLM response contained no choices")

        choice = choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None) if message else None

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    text_parts.append(part.get("text") or part.get("content") or "")
                else:
                    text_parts.append(getattr(part, "text", "") or str(part))
            content = "".join(text_parts)

        if content is None or not str(content).strip():
            finish_reason = getattr(choice, "finish_reason", None)
            raise ValueError(f"LLM response content was empty (finish_reason={finish_reason})")

        return str(content).strip()

    def _json_candidates(self, response_text: str) -> List[str]:
        """Yield likely JSON candidates, preferring explicit JSON fences."""
        text = response_text.strip()
        candidates = [
            match.group(1).strip()
            for match in re.finditer(
                r"```json\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE
            )
        ]
        candidates.append(text)
        return candidates

    def _decode_first_json_value(self, response_text: str) -> Any:
        """Decode the first valid JSON value from response text."""
        decoder = json.JSONDecoder()
        errors: List[json.JSONDecodeError] = []

        for candidate in self._json_candidates(response_text):
            stripped = candidate.strip()
            search_positions = [
                idx for idx, char in enumerate(stripped) if char in "[{"
            ]
            if stripped and stripped[0] in "[{":
                search_positions.insert(0, 0)

            seen_positions = set()
            for pos in search_positions:
                if pos in seen_positions:
                    continue
                seen_positions.add(pos)
                try:
                    value, _ = decoder.raw_decode(stripped[pos:])
                    return value
                except json.JSONDecodeError as e:
                    errors.append(e)

        if errors:
            raise errors[0]
        raise json.JSONDecodeError("Expecting value", response_text, 0)

    def _parse_migration_response(self, completion: Any) -> Dict[str, Any]:
        """Parse and validate an LLM migration response."""
        response_text = self._extract_response_text(completion)

        try:
            result = self._decode_first_json_value(response_text)
        except json.JSONDecodeError as e:
            snippet = response_text[:500].replace("\n", "\\n")
            raise ValueError(
                f"LLM returned invalid JSON: {e.msg} at line {e.lineno} column {e.colno}. "
                f"Response starts with: {snippet!r}"
            ) from e

        if not isinstance(result, dict):
            raise ValueError(f"LLM JSON response must be an object, got {type(result).__name__}")

        if isinstance(result.get("pyspark_code_lines"), list):
            pyspark_code = "\n".join(
                str(line) for line in result["pyspark_code_lines"]
            )
        else:
            pyspark_code = result.get("pyspark_code")

        if not isinstance(pyspark_code, str) or not pyspark_code.strip():
            raise ValueError(
                "LLM JSON response missing non-empty 'pyspark_code' or "
                "'pyspark_code_lines'"
            )

        mapping = result.get("mapping", "")
        if isinstance(mapping, list):
            mapping = "\n".join(str(item) for item in mapping)
        elif not isinstance(mapping, str):
            mapping = str(mapping)

        variables_created = result.get("variables_created", [])
        if isinstance(variables_created, str):
            variables_created = [variables_created]
        elif not isinstance(variables_created, list):
            variables_created = []

        return {
            "pyspark_code": pyspark_code,
            "mapping": mapping,
            "variables_created": [str(var) for var in variables_created],
        }

    def _create_chat_completion(self, prompt: str) -> Any:
        """Create a synchronous chat completion with retry handling."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.chat.completions.create(**self._chat_kwargs(prompt))
            except Exception as e:
                last_error = e
                if attempt >= self.max_retries or not self._is_retryable_llm_error(e):
                    raise
                delay = self._retry_delay(attempt)
                print(f"  ⚠ LLM transient error: {e}. Retrying in {delay:.1f}s...")
                import time

                time.sleep(delay)
        raise last_error

    async def _create_chat_completion_async(self, prompt: str, chunk_id: str) -> Any:
        """Create an async chat completion with retry handling."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self.async_client.chat.completions.create(
                    **self._chat_kwargs(prompt)
                )
            except Exception as e:
                last_error = e
                if attempt >= self.max_retries or not self._is_retryable_llm_error(e):
                    raise
                delay = self._retry_delay(attempt)
                print(
                    f"    ⚠ Chunk {chunk_id} transient LLM error: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
        raise last_error

    def _load_migration_guide(self, guide_path: Optional[str] = None) -> str:
        """Load migration guide"""
        if guide_path is None:
            # Try default locations
            base_dir = Path(__file__).parent.parent.parent
            guide_path = str(base_dir / "SAS_to_pyspark_migration_guide.md")

        try:
            with open(guide_path, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, IOError) as e:
            print(f"Warning: Could not load migration guide from {guide_path}: {e}")
            return ""

    def migrate_file(
        self, sas_file_path: str, output_dir: str, visualize: bool = False
    ) -> MigrationResult:
        """
        Migrate a SAS file to PySpark using graph-based approach

        Args:
            sas_file_path: Path to SAS file
            output_dir: Directory to save output
            visualize: Whether to generate visualizations

        Returns:
            MigrationResult
        """
        start_time = datetime.now()

        print(f"\n{'=' * 60}")
        print(f"Graph-Based Migration: {sas_file_path}")
        print(f"{'=' * 60}\n")

        result = MigrationResult(success=False, sas_file=sas_file_path)
        outputs_saved = False
        result.metadata.update(
            {
                "provider": self.provider,
                "model": self.model,
                "use_rag": self.use_rag,
                "max_concurrent": self.max_concurrent,
                "max_retries": self.max_retries,
                "max_tokens": self.max_tokens,
                "status": "failed",
                "failed_chunks": [],
                "converted_chunk_ids": [],
                "skipped_chunk_ids": [],
                "partial_output": False,
                "output_quality": "unknown",
                "start_time": start_time.isoformat(),
            }
        )

        try:
            # Step 1: Build dependency graph
            print("Step 1: Building dependency graph...")
            builder = GraphBuilder.from_file(sas_file_path)
            graph = builder.build_graph()
            summary = builder.get_summary()
            print(
                f"  ✓ Graph built: {summary['total_nodes']} nodes, {summary['total_edges']} edges"
            )

            if summary["has_cycles"]:
                cycles = graph.find_cycles()
                result.warnings.append(
                    f"Dependency cycles detected (will be resolved): {cycles}"
                )
                print(f"  ⚠ Warning: Cycles detected (will be handled automatically)")
                print(f"    Cycles found: {cycles}")
                print(f"    This is often caused by SAS in-place dataset updates")

            # Step 2: Generate optimized chunks
            print("\nStep 2: Generating optimized chunks...")
            optimizer = ChunkOptimizer(graph)
            chunks = optimizer.generate_chunks()
            chunk_summary = optimizer.get_chunk_summary(chunks)
            cast_stats = optimizer.get_cast_stats()
            print(f"  ✓ Generated {len(chunks)} chunks")
            print(
                f"    Average tokens per chunk: {chunk_summary['avg_tokens_per_chunk']:.0f}"
            )
            if cast_stats["nodes_split_by_cast"] > 0:
                print(
                    f"    cAST splitting: {cast_stats['nodes_split_by_cast']} node(s) split into {cast_stats['subchunks_created']} sub-chunks"
                )

            result.total_chunks = len(chunks)

            # Count layers for display
            chunks_by_layer: Dict[int, List[Chunk]] = defaultdict(list)
            for chunk in chunks:
                chunks_by_layer[chunk.layer].append(chunk)
            num_layers = len(chunks_by_layer)

            # Step 3: Initialize execution context
            print("\nStep 3: Initializing execution context...")
            execution_context = ExecutionContext()
            print(f"  ✓ Initialized schema inferencer")
            print(f"  ✓ Created execution context")
            print(
                f"  ✓ Ready to process {len(chunks)} chunks across {num_layers} layers"
            )
            if self.use_rag and self.example_retriever:
                print(f"  ✓ RAG enabled with pattern store")
            print(f"  ✓ Max concurrent LLM calls: {self.max_concurrent}")

            # Step 4: Convert chunks in parallel by layer
            print("\nStep 4: Converting chunks (parallel by layer)...")
            print(f"  Total: {len(chunks)} chunks in {num_layers} layers")

            # Use async parallel conversion
            converted_chunks, failed_chunks = asyncio.run(
                self._convert_chunks_parallel(chunks, graph, execution_context)
            )

            result.chunks_converted = len(converted_chunks)
            result.metadata["failed_chunks"] = failed_chunks
            result.metadata["converted_chunk_ids"] = [
                chunk["chunk_id"] for chunk in converted_chunks
            ]
            result.metadata["skipped_chunk_ids"] = [
                chunk["chunk_id"] for chunk in failed_chunks
            ]

            # Report any chunks that failed
            failed_count = len(chunks) - len(converted_chunks)
            if failed_count > 0:
                result.errors.append(f"{failed_count} chunk(s) failed to convert")
                print(f"\n  ⚠ {failed_count} chunk(s) failed to convert")
                for failed in failed_chunks:
                    print(
                        f"    - {failed['chunk_id']}: {failed['error_type']} - "
                        f"{failed['error_message']}"
                    )

            macro_var_init = None
            sas_code = None
            if converted_chunks:
                print("\nStep 5: Extracting SAS macro variables...")
            if converted_chunks and SASParser is not None:
                try:
                    with open(sas_file_path, "r", encoding="utf-8") as f:
                        sas_code = f.read()
                    sas_parser = SASParser()
                    macro_var_init = sas_parser.get_macro_var_initialization(sas_code)
                    parsed = sas_parser.parse_content(sas_code)
                    macro_summary = parsed.get("macro_variables", {}).get("summary", {})
                    print(
                        f"  ✓ Found {macro_summary.get('total_definitions', 0)} macro variable definitions"
                    )
                    if macro_summary.get("total_undefined", 0) > 0:
                        print(
                            f"  ⚠ {macro_summary.get('total_undefined', 0)} undefined macro variables will need initialization"
                        )
                except Exception as e:
                    print(f"  ⚠ Could not extract macro variables: {e}")

            # Step 5b: AST-based semantic analysis (if available)
            if converted_chunks and AST_AVAILABLE and sas_code:
                print("\nStep 5b: Performing AST-based semantic analysis...")
                try:
                    ast_parser = SASASTParser(sas_code)
                    program_ast = ast_parser.parse()

                    analyzer = SemanticAnalyzer()
                    symbol_table, semantic_errors, dependencies = analyzer.analyze(
                        program_ast
                    )

                    print(f"  ✓ AST analysis complete")
                    print(f"    - Data steps: {len(program_ast.data_steps)}")
                    print(f"    - PROC steps: {len(program_ast.proc_steps)}")
                    print(f"    - Macros: {len(program_ast.macros)}")
                    print(f"    - Datasets read: {len(dependencies.datasets_read)}")
                    print(
                        f"    - Datasets written: {len(dependencies.datasets_written)}"
                    )

                    # Add semantic analysis results to metadata
                    result.metadata["ast_analysis"] = {
                        "data_steps": len(program_ast.data_steps),
                        "proc_steps": len(program_ast.proc_steps),
                        "macros": len(program_ast.macros),
                        "datasets_read": list(dependencies.datasets_read),
                        "datasets_written": list(dependencies.datasets_written),
                        "macro_vars_used": list(dependencies.macro_vars_used),
                        "macro_vars_defined": list(dependencies.macro_vars_defined),
                    }

                    # Generate enhanced macro var initialization from AST
                    ast_macro_init = analyzer.generate_python_declarations()
                    if (
                        ast_macro_init and len(ast_macro_init) > 50
                    ):  # Has content beyond header
                        macro_var_init = ast_macro_init
                        print(f"  ✓ Generated macro variable declarations from AST")

                    # Add warnings from semantic analysis
                    for error in semantic_errors:
                        if error.severity == "warning":
                            result.warnings.append(
                                f"Line {error.line}: {error.message}"
                            )
                        elif error.severity == "error":
                            result.errors.append(f"Line {error.line}: {error.message}")

                    if semantic_errors:
                        print(f"  ⚠ Found {len(semantic_errors)} semantic issues")

                except Exception as e:
                    print(f"  ⚠ AST analysis failed (continuing without): {e}")

            if converted_chunks:
                # Step 6: Reconcile and integrate chunks into complete script
                print("\nStep 6: Reconciling and integrating chunks...")
                print("  - Deduplicating imports")
                print("  - Resolving variable name conflicts")
                print("  - Removing duplicate code blocks")
                print("  - Validating variable lifecycle")
                print("  - Optimizing execution order")
                print("  - Performing final LLM cleanup")

                # Use enhanced reconciler with validation
                reconcile_result = self.code_reconciler.reconcile_chunks_with_report(
                    converted_chunks, execution_context, sas_macro_vars=macro_var_init
                )

                result.pyspark_code = reconcile_result.code
                result.validation_report = reconcile_result.validation_report
                result.fixes_applied = reconcile_result.fixes_applied
                result.warnings.extend(reconcile_result.warnings)
                result.errors.extend(reconcile_result.errors)

                print(f"  ✓ Reconciliation complete")
                if reconcile_result.fixes_applied:
                    print(
                        f"  ✓ Applied {len(reconcile_result.fixes_applied)} automatic fixes"
                    )
                if reconcile_result.warnings:
                    print(
                        f"  ⚠ {len(reconcile_result.warnings)} warnings (see validation report)"
                    )

                # Step 7: Final execution order optimization
                print("\nStep 7: Optimizing final execution order...")
                exec_optimizer = ExecutionOrderOptimizer()
                optimized_code, order_changes = exec_optimizer.optimize_code(
                    result.pyspark_code
                )
                if order_changes and "No reordering needed" not in order_changes[0]:
                    result.pyspark_code = optimized_code
                    result.fixes_applied.extend(order_changes)
                    print(f"  ✓ Execution order optimized")
                else:
                    print(f"  ✓ Code already in optimal execution order")
            else:
                print("\nStep 5-7: Skipping reconciliation because no chunks converted")
                result.validation_report = "No chunks converted; reconciliation skipped."
                result.fixes_applied.append(
                    "Skipped reconciliation because no chunks converted"
                )

            # Generate mapping document
            result.mapping = self._generate_mapping_document(
                sas_file_path, converted_chunks, summary
            )

            # Determine status before saving outputs so JSON artifacts match return value.
            # These issues are NOT critical (expected in chunk-based migration):
            # - Duplicate definitions (different chunks may produce same DataFrame)
            # - Undefined variables (may be defined in chunks that failed)
            # - "May not exist" warnings from semantic analysis
            non_critical_patterns = [
                "warning",
                "duplicate",
                "multiple times",
                "may not exist",
                "may not be defined",
                "never defined",
                "used but never",
            ]
            critical_errors = [
                e
                for e in result.errors
                if not any(x in e.lower() for x in non_critical_patterns)
            ]

            # Move non-critical errors to warnings for better UX
            for error in result.errors[:]:
                if any(x in error.lower() for x in non_critical_patterns):
                    result.warnings.append(error)
                    result.errors.remove(error)

            critical_errors = [
                e
                for e in result.errors
                if not any(x in e.lower() for x in non_critical_patterns)
            ]

            if (
                result.total_chunks > 0
                and result.chunks_converted == result.total_chunks
                and not critical_errors
            ):
                status = "success"
            elif result.chunks_converted > 0:
                status = "partial"
            else:
                status = "failed"

            result.success = status == "success"
            result.metadata["status"] = status
            result.metadata["output_quality"] = (
                "complete"
                if status == "success"
                else "partial"
                if status == "partial"
                else "no_converted_chunks"
            )

            write_python_output = bool(result.pyspark_code.strip()) and (
                status == "success" or (status == "partial" and self.allow_partial_output)
            )
            result.metadata["partial_output"] = status == "partial" and write_python_output
            if status == "partial" and not self.allow_partial_output:
                result.warnings.append(
                    "Partial PySpark output was not written because partial output is disabled"
                )

            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
            result.metadata.update(
                {
                    "end_time": end_time.isoformat(),
                    "allow_partial_output": self.allow_partial_output,
                    "max_tokens": self.max_tokens,
                }
            )

            # Save outputs
            os.makedirs(output_dir, exist_ok=True)
            self._save_outputs(
                result, output_dir, sas_file_path, write_python=write_python_output
            )
            outputs_saved = True

            print(
                f"\n✓ Migration completed {'successfully' if result.success else 'with issues'}!"
            )
            print(f"  Converted {result.chunks_converted}/{result.total_chunks} chunks")
            print(f"  Applied {len(result.fixes_applied)} automatic fixes")
            if status == "partial":
                print(
                    "  ⚠ Partial output "
                    f"{'written' if write_python_output else 'not written'}"
                )
            if result.warnings:
                print(f"  ⚠ {len(result.warnings)} warnings to review")
            if critical_errors:
                print(f"  ✗ {len(critical_errors)} critical errors")

        except Exception as e:
            result.errors.append(str(e))
            print(f"\n✗ Migration failed: {e}")
            traceback.print_exc()

        finally:
            if not outputs_saved:
                end_time = datetime.now()
                result.execution_time = (end_time - start_time).total_seconds()
                result.metadata.update({"end_time": end_time.isoformat()})

        return result

    def _convert_chunk_with_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Convert a chunk using LLM (synchronous version)

        Args:
            prompt: Complete prompt with context

        Returns:
            Dictionary with pyspark_code, mapping, variables_created
        """
        try:
            completion = self._create_chat_completion(prompt)
            return self._parse_migration_response(completion)

        except Exception as e:
            print(f"  ✗ LLM conversion failed: {e}")
            return None

    async def _convert_chunk_async(
        self,
        chunk: Chunk,
        graph: Any,
        execution_context: ExecutionContext,
        semaphore: asyncio.Semaphore,
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Convert a single chunk asynchronously

        Args:
            chunk: The chunk to convert
            graph: Dependency graph
            execution_context: Execution context with variable mappings
            semaphore: Semaphore for rate limiting

        Returns:
            Tuple of (chunk_id, converted_result or None)
        """
        async with semaphore:
            try:
                # Build enriched context
                context_enricher = ContextEnricher(
                    graph=graph,
                    execution_context=execution_context,
                    example_retriever=self.example_retriever,
                    migration_guide=self.migration_guide,
                )

                enriched_context = context_enricher.enrich_chunk_context(chunk)
                prompt = context_enricher.build_llm_prompt(chunk, enriched_context)

                # Call async LLM
                completion = await self._create_chat_completion_async(
                    prompt, chunk.chunk_id
                )
                result = self._parse_migration_response(completion)
                return (chunk.chunk_id, result, None)

            except Exception as e:
                print(f"    ✗ Chunk {chunk.chunk_id} failed: {e}")
                return (chunk.chunk_id, None, self._chunk_error_metadata(chunk, e))

    async def _convert_chunks_parallel(
        self, chunks: List[Chunk], graph: Any, execution_context: ExecutionContext
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Convert chunks in parallel by layer

        Chunks in the same layer are independent and can be converted
        simultaneously. After each layer completes, we update the
        execution context before moving to the next layer.

        Args:
            chunks: List of chunks to convert
            graph: Dependency graph
            execution_context: Execution context with variable mappings

        Returns:
            Tuple of converted chunk dictionaries and failed chunk metadata
        """
        # Group chunks by layer
        chunks_by_layer: Dict[int, List[Chunk]] = defaultdict(list)
        for chunk in chunks:
            chunks_by_layer[chunk.layer].append(chunk)

        num_layers = len(chunks_by_layer)
        total_chunks = len(chunks)
        converted_chunks = []
        failed_chunks = []
        chunks_completed = 0

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process each layer
        for layer_idx in sorted(chunks_by_layer.keys()):
            layer_chunks = chunks_by_layer[layer_idx]
            layer_size = len(layer_chunks)

            print(
                f"\n  Layer {layer_idx + 1}/{num_layers}: Converting {layer_size} chunk(s) in parallel..."
            )

            # Separate cAST sub-chunks (need sequential processing) from independent chunks
            cast_groups: Dict[str, List[Chunk]] = defaultdict(list)
            independent_chunks: List[Chunk] = []

            for chunk in layer_chunks:
                parent_id = None
                for node in chunk.nodes:
                    if node.metadata.get("cast_split"):
                        parent_id = node.metadata.get("parent_node_id")
                        break
                if parent_id:
                    cast_groups[parent_id].append(chunk)
                else:
                    independent_chunks.append(chunk)

            # Sort cAST groups by part_index for sequential processing
            for parent_id in cast_groups:
                cast_groups[parent_id].sort(
                    key=lambda c: next(
                        (
                            n.metadata.get("part_index", 0)
                            for n in c.nodes
                            if n.metadata.get("cast_split")
                        ),
                        0,
                    )
                )

            # Convert independent chunks in parallel
            tasks = [
                self._convert_chunk_async(chunk, graph, execution_context, semaphore)
                for chunk in independent_chunks
            ]

            # Convert cAST sub-chunk groups sequentially (each group in parallel with others)
            async def convert_cast_group(
                group_chunks: List[Chunk],
            ) -> List[Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]]:
                group_results = []
                for chunk in group_chunks:
                    result = await self._convert_chunk_async(
                        chunk, graph, execution_context, semaphore
                    )
                    group_results.append(result)
                return group_results

            cast_tasks = [convert_cast_group(group) for group in cast_groups.values()]

            # Wait for all tasks
            independent_results = await asyncio.gather(*tasks) if tasks else []
            cast_results_nested = (
                await asyncio.gather(*cast_tasks) if cast_tasks else []
            )

            # Flatten results
            results = list(independent_results)
            for group_result in cast_results_nested:
                results.extend(group_result)

            # Process results
            layer_success = 0
            layer_failed = 0
            for chunk_id, result, failure in results:
                chunks_completed += 1
                if result:
                    # Find the original chunk
                    chunk = next(
                        (c for c in layer_chunks if c.chunk_id == chunk_id), None
                    )

                    chunk_dict = {
                        "chunk_id": chunk_id,
                        "pyspark_code": result.get("pyspark_code", ""),
                        "mapping": result.get("mapping", ""),
                        "variables_created": result.get("variables_created", []),
                    }

                    # Propagate cAST metadata for reconciler
                    if chunk:
                        for node in chunk.nodes:
                            if node.metadata.get("cast_split"):
                                chunk_dict["cast_split"] = True
                                chunk_dict["parent_node_id"] = node.metadata.get(
                                    "parent_node_id", ""
                                )
                                chunk_dict["part_index"] = node.metadata.get(
                                    "part_index", 0
                                )
                                chunk_dict["total_parts"] = node.metadata.get(
                                    "total_parts", 1
                                )
                                chunk_dict["context_header"] = node.metadata.get(
                                    "context_header", ""
                                )
                                break

                    converted_chunks.append(chunk_dict)

                    # Update execution context
                    if chunk:
                        for var in result.get("variables_created", []):
                            sas_name = chunk.nodes[0].name if chunk.nodes else "unknown"
                            execution_context.map_variable_name(sas_name, var)
                        execution_context.add_converted_code(
                            chunk_id, result.get("pyspark_code", "")
                        )

                    layer_success += 1
                else:
                    layer_failed += 1
                    if failure:
                        failed_chunks.append(failure)

            print(
                f"    ✓ Layer {layer_idx + 1} complete: {layer_success} succeeded, {layer_failed} failed"
            )

        return converted_chunks, failed_chunks

    def _chunk_error_metadata(self, chunk: Chunk, error: Exception) -> Dict[str, Any]:
        """Build structured metadata for a failed chunk conversion."""
        message = str(error)
        response_snippet = None
        snippet_match = re.search(r"Response starts with: (.+)$", message)
        if snippet_match:
            response_snippet = snippet_match.group(1)

        return {
            "chunk_id": chunk.chunk_id,
            "layer": chunk.layer,
            "node_ids": [node.node_id for node in chunk.nodes],
            "node_names": [node.name for node in chunk.nodes],
            "error_type": type(error).__name__,
            "error_message": message,
            "response_snippet": response_snippet,
        }

    def _integrate_chunks(
        self,
        converted_chunks: List[Dict[str, Any]],
        execution_context: ExecutionContext,
    ) -> str:
        """
        Integrate converted chunks into complete PySpark script using reconciler

        Args:
            converted_chunks: List of converted chunk dictionaries
            execution_context: Execution context with variable mappings

        Returns:
            Complete PySpark code
        """
        # Use CodeReconciler to create clean, integrated script
        return self.code_reconciler.reconcile_chunks(
            converted_chunks, execution_context
        )

    def _generate_mapping_document(
        self,
        sas_file: str,
        converted_chunks: List[Dict[str, Any]],
        graph_summary: Dict[str, Any],
    ) -> str:
        """Generate mapping document"""
        mapping = []

        mapping.append("SAS TO PYSPARK MIGRATION MAPPING")
        mapping.append("=" * 60)
        mapping.append(f"Source File: {sas_file}")
        mapping.append(
            f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        mapping.append(f"Migration Method: Graph-Based Dependency Analysis")
        mapping.append("")

        mapping.append("GRAPH SUMMARY:")
        mapping.append(f"  Total Nodes: {graph_summary['total_nodes']}")
        mapping.append(f"  Total Edges: {graph_summary['total_edges']}")
        mapping.append(f"  Has Cycles: {graph_summary['has_cycles']}")
        mapping.append("")

        mapping.append("CHUNK-BY-CHUNK MAPPING:")
        mapping.append("-" * 60)

        for chunk in converted_chunks:
            mapping.append(f"\n{chunk['chunk_id']}:")
            mapping.append(chunk.get("mapping", "No mapping provided"))
            mapping.append("")

        return "\n".join(mapping)

    def _save_outputs(
        self,
        result: MigrationResult,
        output_dir: str,
        sas_file_path: str,
        write_python: bool = True,
    ) -> None:
        """Save migration outputs"""
        stem = Path(sas_file_path).stem
        output_files: Dict[str, str] = {}

        # Save PySpark code
        pyspark_file = os.path.join(output_dir, f"{stem}.py")
        if write_python:
            with open(pyspark_file, "w", encoding="utf-8") as f:
                f.write(result.pyspark_code)
            output_files["pyspark"] = pyspark_file
            print(f"  Saved: {pyspark_file}")
        else:
            print(f"  Skipped PySpark output: {pyspark_file}")

        # Save mapping
        mapping_file = os.path.join(output_dir, f"{stem}_mapping.txt")
        with open(mapping_file, "w", encoding="utf-8") as f:
            f.write(result.mapping)
        output_files["mapping"] = mapping_file
        print(f"  Saved: {mapping_file}")

        # Save validation report if available
        if result.validation_report:
            validation_file = os.path.join(output_dir, f"{stem}_validation.txt")
            with open(validation_file, "w", encoding="utf-8") as f:
                f.write(result.validation_report)
                f.write("\n\nFIXES APPLIED:\n")
                for fix in result.fixes_applied:
                    f.write(f"  - {fix}\n")
            output_files["validation"] = validation_file
            print(f"  Saved: {validation_file}")

        # Save result metadata
        result_file = os.path.join(output_dir, f"{stem}_result.json")
        output_files["result"] = result_file
        result.metadata["output_files"] = output_files
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"  Saved: {result_file}")
