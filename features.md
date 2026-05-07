# Features (agent-maintained)

This file tracks notable features or structural capabilities added or restored with agent assistance.

## April 18, 2026

- **Built-in AST fallback for graph building**: `program_to_parsed_sas_dict()` bridges `ProgramNode` to the legacy `parsed_sas` structure; no external `sas_code_parser` is required for `GraphBuilder.from_file()` / `migrate_batch` graph construction.

## April 17, 2026

- **Standard `graph_approach` Python package layout**: The migrator, parsers, AST, RAG, visualization, and CLI are again packaged under `graph_approach/`, enabling `python -m graph_approach.cli.*` and stable `from graph_approach...` imports.
- **Optional SAS parser integration**: `GraphBuilder` exposes `SAS_PARSER_AVAILABLE` for callers that depend on the external `sas_code_parser` (for example macro-variable helpers in the migrator). When it is missing, **`GraphBuilder` falls back to the in-repo `SASASTParser`** via `ast_parsed_sas_bridge` so dependency graphs and CLI analyze/migrate can still run.
- **Backend upload size limits**: Oversized multipart uploads return **413 Payload Too Large** via `RequestEntityTooLarge` handling instead of a generic 500.
