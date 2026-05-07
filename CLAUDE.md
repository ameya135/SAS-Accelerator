# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Command Reference

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# CLI: Analyze SAS file dependencies
python3 -m graph_approach.cli.analyze input.sas
python3 -m graph_approach.cli.analyze input.sas --output graph.json
python3 -m graph_approach.cli.analyze input.sas --format json

# CLI: Visualize dependency graph
python3 -m graph_approach.cli.visualize input.sas --output graph.png
python3 -m graph_approach.cli.visualize input.sas -o graph.svg --format svg

# CLI: Migrate single file
python3 -m graph_approach.cli.migrate input.sas --output-dir ./output
python3 -m graph_approach.cli.migrate input.sas -o ./output --model gpt-4 --visualize
python3 -m graph_approach.cli.migrate input.sas -o ./output --no-rag

# CLI: Batch migration
python3 -m graph_approach.cli.migrate_batch input_dir/ --output-dir output/
python3 -m graph_approach.cli.migrate_batch input_dir/ -o output/ --max-workers 4

# Run tests
pytest tests/ -v
pytest tests/test_dependency_graph.py -v
pytest tests/ --cov=graph_approach --cov-report=html

# Security checks
pip-audit
bandit -r graph_approach backend

# Start backend server (port 5002)
cd backend && ./run.sh
# or: cd backend && python3 app.py

# Start frontend (port 3001)
cd frontend && npm run dev
cd frontend && npm run build     # Production build
cd frontend && npm run preview   # Preview production
```

## Project Overview

A **graph-based SAS to PySpark migration tool** that uses dependency analysis to ensure correct conversion order and rich LLM context. This is an advanced implementation that goes beyond simple file-by-file conversion.

### Core Approach

1. **Parse SAS code** → Extract syntax trees
2. **Build dependency graph** → Identify relationships between DATA steps, PROCs, macros, datasets
3. **Topological sort** → Determine correct execution order
4. **Optimize chunks** → Group related code while respecting dependencies
5. **Enrich context** → Add schemas, examples, variable mappings
6. **LLM conversion** → Convert with maximum context for accuracy
7. **Integrate results** → Assemble into cohesive PySpark script

### Key Differentiator from Simple Migration

**Simple approach**: Parse → Chunk arbitrarily → Convert each chunk independently
- Problem: Variable name inconsistencies, missing dependencies, incorrect execution order

**Graph approach**: Parse → Build graph → Topological sort → Smart chunking → Rich context → Convert
- Solution: Consistent variables, dependency-aware, schema tracking, similar examples via RAG

## Architecture

### Module Organization

```
graph_approach/
├── core/                       # Core graph infrastructure
│   ├── dependency_graph.py     # Graph data structures (NetworkX-based)
│   ├── graph_builder.py        # Build graph from SAS code
│   ├── schema_tracker.py       # Track schemas through transformations
│   ├── chunk_optimizer.py      # Generate optimal chunks from graph
│   └── package_generator.py    # Generate Python packages
├── parsers/
│   └── dependency_extractor.py # Extract dependencies from SAS AST
├── migration/
│   ├── graph_migrator.py       # Main migration orchestrator
│   ├── context_enricher.py     # Build rich LLM context
│   ├── batch_migrator.py       # Batch migration support
│   ├── variable_tracker.py     # Track variable names across chunks
│   ├── code_reconciler.py      # Reconcile converted code
│   └── execution_order.py      # Execution order utilities
├── rag/
│   ├── pattern_store.py        # ChromaDB-based pattern storage
│   └── example_retriever.py    # Retrieve similar examples
├── visualization/
│   ├── graph_renderer.py       # Graphviz visualizations
│   └── report_generator.py     # Markdown/HTML reports
├── api/
│   ├── graph_exporter.py       # Export graphs for API
│   ├── schema_exporter.py      # Export schemas for API
│   └── realtime_migrator.py    # Real-time migration support
├── cli/
│   ├── analyze.py              # Analyze dependencies
│   ├── migrate.py              # Migrate single file
│   ├── migrate_batch.py        # Batch migration
│   └── visualize.py            # Generate visualizations
├── ast/
│   ├── sas_lexer.py            # SAS lexer
│   ├── sas_ast.py              # SAS AST definitions
│   └── semantic_analyzer.py    # Semantic analysis
├── backend/
│   ├── app.py                  # Flask API (port 5002)
│   └── run.sh                  # Backend startup script
├── frontend/                    # React + Vite UI
│   ├── src/
│   │   ├── App.jsx             # Main component
│   │   ├── components/         # React components
│   │   └── hooks/              # Custom React hooks
│   └── package.json
└── tests/                       # Unit tests
    ├── test_dependency_graph.py
    ├── test_graph_builder.py
    └── test_validation.py
```

### Graph Data Structures

**Node Types** (7 types):
- `DATASET`: SAS datasets (created/read)
- `DATA_STEP`: DATA step blocks
- `PROC`: PROC step blocks
- `MACRO`: Macro definitions (%MACRO)
- `MACRO_VARIABLE`: Macro variables (&var, %LET)
- `LIBRARY`: Library references (LIBNAME)
- `FILE_REF`: File references (FILENAME)

**Edge Types** (8 types):
- `READS_FROM`: Node reads from dataset
- `WRITES_TO`: Node writes to dataset
- `CALLS`: Macro/function call
- `USES_VARIABLE`: Uses macro variable
- `DEFINES_VARIABLE`: Defines macro variable
- `PROC_INPUT`: PROC reads dataset
- `PROC_OUTPUT`: PROC writes dataset
- `DEPENDENCY`: Generic dependency

**Graph Operations**:
- Topological sorting for execution order
- Cycle detection and reporting
- Execution layer generation (for parallel execution)
- Subgraph extraction
- Dependency traversal (upstream/downstream)

### Migration Pipeline (5 Phases)

**Phase 1: Graph Construction**
```python
builder = GraphBuilder.from_file("input.sas")
graph = builder.build_graph()
execution_order = builder.get_execution_order()
```

**Phase 2: Chunk Optimization**
```python
optimizer = ChunkOptimizer(graph)
chunks = optimizer.generate_chunks(
    max_tokens=2000,
    min_chunk_size=50
)
```

**Phase 3: Context Enrichment**
```python
enricher = ContextEnricher(graph, pattern_store)
context = enricher.build_context_for_chunk(
    chunk=chunks[0],
    execution_context=exec_ctx
)
```

**Phase 4: LLM Conversion**
```python
migrator = GraphMigrator(
    api_key=api_key,
    azure_endpoint=endpoint,
    model="gpt-4",
    use_rag=True
)
result = migrator.migrate_file("input.sas", "output/")
```

**Phase 5: Integration & Validation**
- Assemble converted chunks
- Generate migration report
- Optionally validate with PySpark

### Schema Tracking

Tracks column-level transformations through the migration:

```python
schema = DatasetSchema(name="employee_data")
schema.add_column(ColumnInfo(
    name="salary",
    data_type=DataType.DOUBLE,
    format="DOLLAR12.2"
))

# Apply transformations
filtered = schema.apply_drop(["temp_col"])
renamed = filtered.apply_rename({"old_name": "new_name"})

# Execution context tracks schemas and variables
context = ExecutionContext()
context.add_dataset(schema)
context.map_variable_name("employee_data", "employee_df")
```

### RAG Integration

Uses ChromaDB to store and retrieve migration patterns:

```python
pattern_store = PatternStore()
pattern_store.initialize_from_guide("migration_guide.md")

retriever = ExampleRetriever(pattern_store)
examples = retriever.get_relevant_examples(
    code_snippet="PROC MEANS",
    category="proc",
    max_results=3
)
```

## Environment Configuration

Create `.env` file in the project root, or copy `.env.example`:

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
SAS_ACCELERATOR_API_KEY=your_backend_api_key_here
SAS_ACCELERATOR_DEV_MODE=false
SAS_ACCELERATOR_CORS_ORIGINS=http://localhost:3001
```

Models supported: `o3`, `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

## Key Technical Details

### Dependency Extraction

**DATA Step Dependencies**:
- `SET`, `MERGE`, `UPDATE`, `MODIFY` statements
- Creates edges: `dataset → READS_FROM → data_step → WRITES_TO → output_dataset`

**PROC Dependencies**:
- `DATA=` option (input)
- `OUT=` option (output)
- Special handling for PROC SQL (`FROM`, `CREATE TABLE`)
- Special handling for PROC IMPORT/EXPORT

**Macro Dependencies**:
- Macro calls: `%macro_name()`
- Macro variable references: `&var`
- Macro definitions: `%MACRO name; ... %MEND;`
- `%LET` statements for variable assignment
- `CALL SYMPUT` for dynamic variable creation

### Chunk Optimization Strategy

1. **Start with execution layers** from topological sort
2. **Group related nodes**: Macros with their variables, DATA steps with output datasets
3. **Estimate token sizes** for each node's code
4. **Merge small chunks** if total tokens < min threshold
5. **Split large chunks** if total tokens > max threshold
6. **Preserve dependencies** - never split dependent nodes across chunks

### Variable Name Tracking

Problem: LLM might generate different variable names for same dataset across chunks
Solution: `ExecutionContext.map_variable_name()` maintains SAS→PySpark mapping

```python
# Chunk 1 converts employee_data → employee_df
context.map_variable_name("employee_data", "employee_df")

# Chunk 2 asks: what's the PySpark name for employee_data?
pyspark_name = context.get_pyspark_variable_name("employee_data")
# Returns: "employee_df"
```

### Visualization

**Graph visualization** (Graphviz):
- Color-coded nodes by type
- Different shapes: rectangles for datasets, ovals for steps, hexagons for macros
- Execution layers shown as subgraphs
- Legend auto-generated
- Formats: PNG, SVG, PDF, DOT

**Migration reports** (Markdown/HTML):
- Graph statistics
- Execution order
- Chunk breakdown
- Success/failure status per chunk
- Errors and warnings
- Timing information

## Backend API

Flask server on port 5002 with endpoints:

- `POST /api/analyze` - Analyze SAS file, return graph
- `POST /api/migrate` - Migrate SAS file
- `GET /api/graph/<session_id>` - Get graph data
- `GET /api/schema/<session_id>` - Get schema info
- `GET /api/status/<session_id>` - Migration status
- `GET /api/download/<session_id>` - Download results

Frontend (React + Vite) on port 3001 provides visual interface.

## Common Development Tasks

### Adding New Dependency Type

1. Add to `EdgeType` enum in `core/dependency_graph.py`
2. Update `dependency_extractor.py` to extract new dependency
3. Add extraction logic in `graph_builder.py`
4. Update visualization colors in `visualization/graph_renderer.py`

### Adding New Node Type

1. Add to `NodeType` enum in `core/dependency_graph.py`
2. Update `graph_builder.py` to create nodes of this type
3. Add emoji/icon in CLI tools (`cli/analyze.py`)
4. Add visualization styling in `visualization/graph_renderer.py`

### Modifying Chunking Strategy

Edit `core/chunk_optimizer.py`:
- `_should_group_nodes()` - Defines which nodes should stay together
- `_estimate_token_size()` - Estimates chunk size
- `generate_chunks()` - Main chunking algorithm

### Adding New Migration Examples

1. Add examples to migration guide markdown
2. Run `pattern_store.initialize_from_guide()` to re-index
3. Examples automatically retrieved via RAG during migration

### Debugging Failed Conversions

1. Check execution order: `python3 -m graph_approach.cli.analyze file.sas`
2. Visualize graph: `python3 -m graph_approach.cli.visualize file.sas -o graph.png`
3. Review chunks: Enable debug logging in `GraphMigrator`
4. Check LLM context: Print enriched context before API call
5. Validate graph: `graph.has_cycles()` should be False

## Testing

Run tests with pytest:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_dependency_graph.py -v

# With coverage
pytest tests/ --cov=graph_approach --cov-report=html
```

Test files:
- `test_dependency_graph.py` - Graph data structure tests
- `test_graph_builder.py` - Graph construction tests
- `test_validation.py` - Validation tests

## Important Considerations

### Cycles in Dependency Graph

If graph has cycles, migration will fail. Handle by:
1. Detecting cycles: `graph.has_cycles()`
2. Finding cycle nodes: `graph.find_cycles()`
3. Manual intervention: Break cycles by reordering SAS code or splitting dependencies

### ChromaDB Initialization

Pattern store uses ChromaDB which may fail in some environments. Fallback mode stores patterns in-memory without vector search.

### Token Limits

Default chunking uses max 2000 tokens per chunk. Adjust via:
```python
optimizer.generate_chunks(max_tokens=4000)
```

### Model Selection

- `o3`: Latest model, best quality, slower
- `gpt-4`: High quality, balanced speed
- `gpt-4-turbo`: Faster, good quality
- `gpt-3.5-turbo`: Fastest, lower quality

### Frontend Development

Frontend in `frontend/` is React + Vite app with:
- Hot reload in dev mode: `npm run dev`
- Production build: `npm run build` (output to `dist/`)
- Tailwind CSS for styling
- Axios for API calls
- ReactFlow for graph visualization

## Python Path Setup

CLI tools add parent directories to `sys.path` for imports. When importing modules programmatically:

```python
import sys
from pathlib import Path

# Add graph_approach to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from graph_approach.core.graph_builder import GraphBuilder
```

## Migration Guide Integration

The tool references a migration guide (typically `SAS_to_pyspark_migration_guide.md` in parent directory) that contains:
- SAS→PySpark function mappings
- Common patterns and their conversions
- Examples with explanations

This guide is:
1. Loaded by RAG pattern store
2. Indexed for similarity search
3. Used to retrieve relevant examples during conversion
