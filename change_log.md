# Change log

Per-day record of notable changes to this repository.

## April 18, 2026

- **`graph_approach/parsers/ast_parsed_sas_bridge.py`**: New bridge from `SASASTParser` output to the `parsed_sas` dict shape consumed by `DependencyExtractor`, so graph building works when the external `sas_code_parser` package is not installed.
- **`graph_approach/core/graph_builder.py`**: If the external `SASParser` is unavailable, parse SAS with the in-repo AST via the bridge; on failure, raise a `RuntimeError` that includes the underlying exception.
- **`tests/test_graph_builder.py`**: Removed the skip when the external parser is absent; graph builder tests now run using the built-in AST path.
- **`tests/test_backend_security.py`**: `test_analyze_does_not_leak_internal_details` now allows HTTP 200 when graph analysis succeeds on arbitrary upload bytes, while still asserting no traceback is exposed in JSON.

## April 17, 2026

- **Restored `graph_approach/` package layout**: Moved `api/`, `ast/`, `cli/`, `core/`, `migration/`, `parsers/`, `rag/`, `visualization/`, and the package `__init__.py` back under `graph_approach/` at the project root so existing `from graph_approach...` imports resolve. Resolves `ModuleNotFoundError: No module named 'graph_approach'` when running CLI tools.
- **`backend/app.py`**: Set `_repo_root` to `Path(__file__).parent.parent` (project root) and removed the redundant `sys.path` entry for a nested `graph_approach` folder; graph modules import from the restored package path.
- **`backend/app.py`**: Registered `RequestEntityTooLarge` error handler (413) and handled the same exception in `upload_files` before the generic handler so oversized uploads return 413 instead of 500.
- **`graph_approach/core/graph_builder.py`**: Made optional external `SASParser` import resilient (`ImportError` fallbacks, `SAS_PARSER_AVAILABLE`); raises a clear `RuntimeError` if `sas_code` is given without a parser.
- **Tests**: Updated imports in `tests/test_dependency_extractor.py`, `test_dependency_graph.py`, `test_execution_order.py`, `test_schema_tracker.py`, and `test_variable_tracker.py` to use `graph_approach.*` prefixes. `test_graph_builder.py` skips when the optional external parser is absent. Adjusted `test_backend_security.py` for valid API field names, path assertions, session setup for size tests, and upload/analyze expectations.
- **Documentation**: Updated [README.md](README.md) installation/testing instructions (project root, no `cd graph_approach`) and documented batch migration example using `sas_etl_project/`.
