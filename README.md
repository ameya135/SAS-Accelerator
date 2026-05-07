# Graph-Based SAS to PySpark Migration Tool

A production-ready, dependency-aware approach to migrating SAS code to PySpark using graph analysis, schema tracking, RAG integration, and intelligent chunking.

## Overview

This tool implements a complete graph-based migration strategy that analyzes SAS code dependencies before conversion, ensuring:
- **Correct execution order** via topological sorting
- **Rich context** for LLM conversion with dependency and schema information
- **Schema tracking** through transformations to maintain type safety
- **Optimal chunking** based on code dependencies and token limits
- **RAG integration** for learning from successful migration patterns
- **Comprehensive visualization** of dependency graphs
- **Detailed reporting** of migration results

## ✅ Complete Implementation (All Weeks)

### Core Graph Infrastructure
- **DependencyGraph**: NetworkX-based graph with 7 node types and 8 edge types
- **Node Types**: DATASET, DATA_STEP, PROC, MACRO, MACRO_VARIABLE, LIBRARY, FILE_REF
- **Edge Types**: READS_FROM, WRITES_TO, CALLS, USES_VARIABLE, DEFINES_VARIABLE, PROC_INPUT, PROC_OUTPUT
- **Graph Operations**: Topological sort, cycle detection, execution layers, dependency traversal, subgraphs

### Dependency Extraction
- **DATA Step Dependencies**: SET, MERGE, UPDATE, MODIFY statements with full relationship tracking
- **PROC Dependencies**: DATA=, OUT= options, PROC-specific logic (SQL FROM/CREATE, IMPORT, EXPORT)
- **Macro Dependencies**: Macro calls, macro variable references (&var), %LET statements, CALL SYMPUT
- **File Dependencies**: LIBNAME, FILENAME, INFILE, FILE statements

### Schema Tracking
- **DatasetSchema**: Track columns, types, formats, labels through transformations
- **ExecutionContext**: Maintain state during migration (datasets, macro vars, converted code, variable mappings)
- **Schema Operations**: KEEP, DROP, RENAME, MERGE transformations
- **Schema Inference**: Infer types from LENGTH, FORMAT, LABEL statements and assignments

### Graph-Based Chunking
- **ChunkOptimizer**: Generate optimal chunks from dependency graph
- **Smart Grouping**: Group related nodes (macros + variables, data steps + datasets)
- **Size Optimization**: Merge small chunks, split large ones based on token limits
- **Layer-Based**: Respect execution layers for correct dependency order

### RAG Integration
- **PatternStore**: ChromaDB-based storage for migration patterns (with fallback mode)
- **ExampleRetriever**: Find and retrieve similar migration examples
- **Automatic Initialization**: Seeds pattern store from migration guide examples
- **Similarity Search**: Vector-based similarity with category filtering

### Context Enrichment
- **ContextEnricher**: Build rich context from graph, schemas, and examples
- **Comprehensive Prompts**: Include dependencies, schemas, variable mappings, similar examples
- **Smart Integration**: Combine all information sources for optimal LLM performance

### Migration Orchestration
- **GraphMigrator**: Complete end-to-end migration orchestrator
- **Multi-Phase Process**: Graph building → Chunking → Context enrichment → LLM conversion → Integration
- **Azure OpenAI Integration**: Full support for GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Variable Tracking**: Consistent variable naming across chunks
- **Error Handling**: Comprehensive error handling and reporting

### Visualization
- **GraphRenderer**: Generate dependency graph visualizations using Graphviz
- **Multiple Formats**: PNG, SVG, PDF, DOT output formats
- **Colored Nodes**: Different colors/shapes for each node type
- **Execution Layers**: Visual grouping by execution layers
- **Legend Generation**: Automatic legend for node and edge types

### Reporting
- **ReportGenerator**: Comprehensive migration reports
- **Multiple Formats**: Markdown and HTML report generation
- **Detailed Statistics**: Graph stats, chunk stats, execution order
- **Migration Results**: Success/failure status, errors, warnings, timing
- **Summary Reports**: Multi-file migration summaries

### CLI Tools
- **analyze.py**: Analyze SAS file dependencies and show graph statistics with beautiful formatting
- **migrate.py**: Perform complete graph-based migration with all features
- **visualize.py**: Generate dependency graph visualizations in multiple formats

## Installation

From the project root (this repository):

```bash
python3 -m pip install -r requirements.txt
```

The root requirements file includes the graph migration library, backend Flask API dependencies, test coverage tooling, and security audit tooling. The Python package code lives under `graph_approach/`; run CLI modules as `python3 -m graph_approach.cli.<command>` from the project root.

## Quick Start

### 1. Analyze Dependencies

```bash
# Basic analysis with beautiful formatting
python3 -m graph_approach.cli.analyze examples/simple_example.sas

# Save graph data to JSON
python3 -m graph_approach.cli.analyze employee_performance.sas --output graph.json

# JSON output format for programmatic use
python3 -m graph_approach.cli.analyze file.sas --format json
```

### 2. Visualize Dependency Graph

```bash
# Generate PNG visualization
python3 -m graph_approach.cli.visualize examples/simple_example.sas --output graph.png

# Generate SVG (scalable vector)
python3 -m graph_approach.cli.visualize file.sas -o graph.svg --format svg

# Generate DOT file for custom processing
python3 -m graph_approach.cli.visualize file.sas -o graph.dot --format dot
```

### 3. Perform Migration

```bash
# Basic migration (uses environment variables for Azure OpenAI)
python3 -m graph_approach.cli.migrate examples/simple_example.sas --output-dir ./output

# With visualization and specific model
python3 -m graph_approach.cli.migrate file.sas -o ./output --model gpt-4 --visualize

# Without RAG (faster, less context)
python3 -m graph_approach.cli.migrate file.sas -o ./output --no-rag

# With custom API credentials
python3 -m graph_approach.cli.migrate file.sas -o ./output \
    --api-key YOUR_KEY --endpoint YOUR_ENDPOINT

# Batch migration (directory of .sas files)
python3 -m graph_approach.cli.migrate_batch sas_etl_project/ -o ./output_batch
```

### Programmatic Usage

```python
from graph_approach.core.graph_builder import GraphBuilder

# Build graph from SAS file
builder = GraphBuilder.from_file("example.sas")
graph = builder.build_graph()

# Get execution order
execution_order = builder.get_execution_order()
for node in execution_order:
    print(f"{node.node_type.value}: {node.name}")

# Check for cycles
if graph.has_cycles():
    cycles = graph.find_cycles()
    print(f"Cycles detected: {cycles}")

# Get dependency layers (for parallel execution)
layers = graph.get_execution_layers()
for i, layer in enumerate(layers):
    print(f"Layer {i}: {[n.name for n in layer]}")
```

## Architecture

### Core Components

```
graph_approach/
├── core/
│   ├── dependency_graph.py       # Graph data structures
│   ├── graph_builder.py          # Build graph from parsed SAS
│   ├── schema_tracker.py         # Schema tracking
│   └── chunk_optimizer.py        # (TODO) Graph-based chunking
├── parsers/
│   └── dependency_extractor.py   # Extract dependencies from SAS
├── migration/
│   ├── graph_migrator.py         # (TODO) Main orchestrator
│   ├── context_enricher.py       # (TODO) Build rich context
│   └── chunk_converter.py        # (TODO) Convert chunks
├── rag/
│   ├── pattern_store.py          # (TODO) ChromaDB integration
│   └── example_retriever.py      # (TODO) Retrieve examples
├── cli/
│   ├── analyze.py                # ✅ Analyze dependencies
│   ├── migrate.py                # (TODO) Perform migration
│   └── visualize.py              # (TODO) Generate visualizations
└── visualization/
    ├── graph_renderer.py         # (TODO) Graphviz rendering
    └── report_generator.py       # (TODO) Generate reports
```

### Dependency Graph Example

For this SAS code:
```sas
DATA employee_data;
    INPUT emp_id name $ salary;
    DATALINES;
1 John 50000
;
RUN;

DATA high_performers;
    SET employee_data;
    WHERE salary > 55000;
RUN;

PROC MEANS DATA=high_performers;
    VAR salary;
    OUTPUT OUT=salary_stats MEAN=avg_salary;
RUN;
```

The graph structure:
```
employee_data (DATASET)
    ↓ READS_FROM
DATA_STEP_1
    ↓ WRITES_TO
high_performers (DATASET)
    ↓ PROC_INPUT
PROC_MEANS
    ↓ PROC_OUTPUT
salary_stats (DATASET)
```

Execution order: `DATA_STEP_1 → high_performers → PROC_MEANS → salary_stats`

## Graph Analysis Output

Running `python3 -m graph_approach.cli.analyze examples/simple_example.sas` produces:

```
Analyzing SAS file: examples/simple_example.sas

╭─── 📊 Graph Summary ───╮
│ Total Nodes: 10        │
│ Total Edges: 9         │
│ Has Cycles: No ✓       │
╰─────────────────────────╯

Node Counts by Type
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Node Type      ┃ Count ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ dataset        │     3 │
│ macro          │     1 │
│ macro_variable │     1 │
│ proc           │     2 │
│ data_step      │     3 │
└────────────────┴───────┘

Execution Order:
  1. 📝 [macro_variable] dept
  2. 🔄 [data_step] DATA_16
  3. 🔧 [macro] calculate_bonus
  4. 📊 [dataset] employee_data
  5. 🔄 [data_step] DATA_8
  6. 🔄 [data_step] DATA_26
  7. 📊 [dataset] high_performers
  8. ⚙️ [proc] PROC_MEANS_32
  9. 📊 [dataset] salary_stats
 10. ⚙️ [proc] PROC_PRINT_41
```

## Schema Tracking Example

```python
from graph_approach.core.schema_tracker import (
    DatasetSchema, ColumnInfo, DataType, ExecutionContext
)

# Create a schema
schema = DatasetSchema(name="employee_data")
schema.add_column(ColumnInfo(
    name="emp_id",
    data_type=DataType.INTEGER
))
schema.add_column(ColumnInfo(
    name="salary",
    data_type=DataType.DOUBLE,
    format="DOLLAR12.2"
))

# Apply transformations
filtered = schema.apply_drop(["emp_id"])  # Remove emp_id column
renamed = filtered.apply_rename({"salary": "annual_salary"})

# Use execution context
context = ExecutionContext()
context.add_dataset(schema)
context.add_macro_var("year", 2024)

# Track variable name mappings
context.map_variable_name("employee_data", "employee_df")
pyspark_name = context.get_pyspark_variable_name("employee_data")
# Returns: "employee_df"
```

## Testing

```bash
# Run all tests (from project root)
pytest tests/ -v

# Run specific test file
pytest tests/test_dependency_graph.py -v

# Run with coverage
pytest tests/ --cov=graph_approach --cov-report=html

# Run security checks
pip-audit
bandit -r graph_approach backend
```

## How It Improves Migration

### Current Approach (testing_migrate.py)
```
1. Parse SAS code
2. Chunk arbitrarily: Macros → Metadata → DATA → PROC
3. Convert each chunk independently
4. Limited context (just chunk number)
5. Variable name inconsistencies
```

### Graph-Based Approach
```
1. Parse SAS code
2. Build dependency graph
3. Topological sort for correct order
4. Chunk by dependency layers
5. Rich context for each chunk:
   - Input dataset schemas
   - Macro variable values
   - Previously converted code snippets
   - Similar migration examples (RAG)
6. Track variable names for consistency
7. Schema validation
```

### Example Improvement

**Problem with Current Approach:**
```python
# Chunk 1 conversion
raw_employee_data_df = spark.read...

# Chunk 2 conversion (doesn't know about chunk 1)
filtered_df = raw_employee_data.filter(...)  # ❌ Name mismatch!
```

**With Graph Approach:**
```python
# Context knows: employee_data → employee_df
# Chunk 1
employee_df = spark.read...
context.map_variable_name("employee_data", "employee_df")

# Chunk 2 (gets context)
# Knows employee_data maps to employee_df
filtered_df = employee_df.filter(...)  # ✅ Correct!
```

## Next Steps

### Week 3: Chunk Optimizer & Migration Logic
- [ ] Implement `core/chunk_optimizer.py`
  - Generate optimal chunks from execution layers
  - Merge small related chunks
  - Split large complex chunks
- [ ] Implement `migration/chunk_converter.py`
  - Convert chunks using Azure OpenAI
  - Apply context from graph

### Week 4: RAG & Context Enrichment
- [ ] Implement `rag/pattern_store.py` (ChromaDB)
- [ ] Implement `rag/example_retriever.py`
- [ ] Implement `migration/context_enricher.py`
- [ ] Implement `migration/graph_migrator.py`

### Week 5: Visualization & Polish
- [ ] Implement `visualization/graph_renderer.py` (Graphviz)
- [ ] Implement `visualization/report_generator.py`
- [ ] Implement `cli/migrate.py`
- [ ] Implement `cli/visualize.py`
- [ ] Complete test coverage
- [ ] Performance optimization

## Dependencies

- **networkx**: Graph data structure and algorithms
- **chromadb**: Vector database for RAG (pattern storage)
- **graphviz**: Graph visualization
- **rich**: Beautiful CLI output
- **typer**: CLI argument parsing
- **pytest**: Testing
- **openai**: Azure OpenAI integration

## Contributing

When adding new features:
1. Update the appropriate module in `core/`, `parsers/`, `migration/`, or `rag/`
2. Write unit tests in `tests/`
3. Update this README
4. Test with examples in `examples/`

## License

Part of the SAS to PySpark Migration Tool project.
