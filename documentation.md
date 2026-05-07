# SAS Accelerator — Technical Documentation

> A graph-based SAS-to-PySpark migration tool with cAST-aware chunking, dependency analysis, schema tracking, and RAG-enhanced LLM conversion.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [AST Layer — Deep Dive](#3-ast-layer--deep-dive)
   - [3.1 SAS Lexer (`ast/sas_lexer.py`)](#31-sas-lexer)
   - [3.2 SAS AST (`ast/sas_ast.py`)](#32-sas-ast)
   - [3.3 Semantic Analyzer (`ast/semantic_analyzer.py`)](#33-semantic-analyzer)
4. [cAST Chunking — Full Deep Dive](#4-cast-chunking--full-deep-dive)
5. [Core Graph Infrastructure](#5-core-graph-infrastructure)
   - [5.1 Dependency Graph (`core/dependency_graph.py`)](#51-dependency-graph)
   - [5.2 Graph Builder (`core/graph_builder.py`)](#52-graph-builder)
   - [5.3 Dependency Extractor (`parsers/dependency_extractor.py`)](#53-dependency-extractor)
   - [5.4 Schema Tracker (`core/schema_tracker.py`)](#54-schema-tracker)
   - [5.5 Chunk Optimizer (`core/chunk_optimizer.py`)](#55-chunk-optimizer)
6. [Migration Pipeline](#6-migration-pipeline)
   - [6.1 Context Enricher (`migration/context_enricher.py`)](#61-context-enricher)
   - [6.2 Graph Migrator (`migration/graph_migrator.py`)](#62-graph-migrator)
   - [6.3 Variable Tracker (`migration/variable_tracker.py`)](#63-variable-tracker)
   - [6.3b Batch Migrator (`migration/batch_migrator.py`)](#63b-batch-migrator)
   - [6.4 Execution Order Optimizer (`migration/execution_order.py`)](#64-execution-order-optimizer)
   - [6.5 Code Reconciler (`migration/code_reconciler.py`)](#65-code-reconciler)
7. [RAG System](#7-rag-system)
8. [Backend API (`backend/app.py`)](#8-backend-api)
9. [Frontend](#9-frontend)
10. [CLI Tools](#10-cli-tools)
11. [Visualization & Reporting](#11-visualization--reporting)
12. [Package Generator](#12-package-generator)
13. [Testing](#13-testing)
14. [Configuration & Deployment](#14-configuration--deployment)
15. [End-to-End Flow Walkthrough](#15-end-to-end-flow-walkthrough)

---

## 1. Overview

### What It Does

The SAS Accelerator converts legacy SAS programs into production-ready PySpark code. Unlike naive LLM-based converters that chunk code arbitrarily and send each chunk in isolation, this tool:

1. **Parses** the SAS source into a full Abstract Syntax Tree (AST).
2. **Builds a dependency graph** that maps every DATA step, PROC, macro, dataset, library, and file reference as a node, with typed edges representing how they relate.
3. **Topologically sorts** the graph to determine correct execution order.
4. **Optimizes chunks** using the cAST algorithm — splitting large constructs at syntactic boundaries and greedily merging small siblings.
5. **Enriches context** for each chunk: input/output schemas, variable name maps, RAG-retrieved examples, and the full migration guide.
6. **Converts** chunks concurrently (async, up to 5 parallel LLM calls per layer) via Azure OpenAI.
7. **Reconciles** all converted chunks into a single coherent PySpark script, deduplicating imports, resolving variable naming conflicts, and running a final LLM-assisted cleanup pass.

### Key Differentiators

| Simple Approach | Graph Approach |
|-----------------|----------------|
| Chunk arbitrarily (fixed lines/tokens) | Chunk at AST syntactic boundaries |
| Convert each chunk independently | Enrich with dependency info, schemas, and examples |
| No execution order guarantee | Topological sort enforces correct order |
| Variable names may diverge across chunks | `ExecutionContext.variable_name_map` keeps names consistent |
| Schema types unknown | `SchemaTracker` propagates column types through transformations |

### Quick Start (CLI)

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze SAS file dependencies
python -m graph_approach.cli.analyze input.sas
python -m graph_approach.cli.analyze input.sas --format json

# Visualize dependency graph
python -m graph_approach.cli.visualize input.sas --output graph.png

# Migrate a single file
python -m graph_approach.cli.migrate input.sas --output-dir ./output
python -m graph_approach.cli.migrate input.sas -o ./output --model gpt-4 --visualize

# Batch migration
python -m graph_approach.cli.migrate_batch input_dir/ --output-dir output/
python -m graph_approach.cli.migrate_batch input_dir/ -o output/ --max-workers 4

# Start backend API (port 5002)
cd backend && ./run.sh

# Start frontend (port 3000)
cd frontend && npm run dev
```

---

## 2. Architecture Overview

### End-to-End Pipeline

```
SAS Source File
      │
      ▼
┌─────────────────────┐
│  SASParser (regex)  │  ── Splits into data_steps, proc_steps, macros
└─────────┬───────────┘
          │ parsed_sas dict
          ▼
┌─────────────────────┐
│  DependencyExtractor│  ── Extracts inputs/outputs, macro vars, file refs
└─────────┬───────────┘
          │ deps dict
          ▼
┌─────────────────────┐
│    GraphBuilder     │  ── Adds nodes & typed edges to DependencyGraph
└─────────┬───────────┘
          │ DependencyGraph (NetworkX DiGraph)
          ▼
┌─────────────────────┐
│  ChunkOptimizer     │  ── Topological sort → layer groups → merge/split
│  + CASTChunker      │     Large nodes split at AST boundaries (cAST)
└─────────┬───────────┘
          │ List[Chunk]
          ▼
┌─────────────────────┐
│  ContextEnricher    │  ── Schemas, dependencies, RAG examples → prompt
└─────────┬───────────┘
          │ LLM prompt per chunk
          ▼
┌─────────────────────┐
│  Azure OpenAI       │  ── Async, max 5 concurrent, layer-by-layer
│  (async per layer)  │
└─────────┬───────────┘
          │ List[{pyspark_code, mapping, variables_created}]
          ▼
┌─────────────────────┐
│  CodeReconciler     │  ── Reassemble cAST chunks → dedup imports →
│                     │     variable mapping → topo reorder → LLM cleanup
└─────────┬───────────┘
          │
          ▼
     output/*.py   (PySpark script)
     output/*_mapping.txt
     output/*_validation.txt
     output/*_result.json
```

### Module Map

```
graph_approach/           (root — IS the package)
├── ast/
│   ├── sas_lexer.py       Tokenizes SAS → Token stream (40+ TokenType values)
│   ├── sas_ast.py         Parses tokens → AST (30+ NodeType values)
│   └── semantic_analyzer.py  Symbol tables, type inference, DependencyInfo
├── core/
│   ├── dependency_graph.py  NetworkX-backed graph: NodeType(7), EdgeType(8)
│   ├── graph_builder.py     Orchestrates SASParser + DependencyExtractor
│   ├── cast_chunker.py      cAST algorithm: recursive split + greedy merge
│   ├── chunk_optimizer.py   Layer-based chunking, delegates large nodes → cAST
│   ├── schema_tracker.py    DatasetSchema, ExecutionContext, SchemaInferencer
│   └── package_generator.py Generates setup.py, requirements.txt, README
├── parsers/
│   └── dependency_extractor.py  Regex extraction: SET/MERGE/PROC SQL/IMPORT
├── migration/
│   ├── graph_migrator.py    Main orchestrator, async parallel LLM calls
│   ├── context_enricher.py  Builds EnrichedContext + LLM prompt
│   ├── batch_migrator.py    ThreadPoolExecutor over multiple SAS files
│   ├── variable_tracker.py  Tracks definition/usage/deletion in PySpark output
│   ├── code_reconciler.py   Merges all chunks → clean final script
│   └── execution_order.py   BlockType-aware topological reorder of final code
├── rag/
│   ├── pattern_store.py     ChromaDB + fallback Jaccard for pattern storage
│   └── example_retriever.py Category boost, formats examples for prompts
├── visualization/
│   ├── graph_renderer.py    Graphviz: color-coded nodes/edges, PNG/SVG/PDF
│   └── report_generator.py  Markdown/HTML migration report
├── api/
│   ├── graph_exporter.py    Export graph → React Flow / D3 / JSON
│   ├── schema_exporter.py   Export schemas for API consumption
│   └── realtime_migrator.py SSE-based streaming migration events
├── cli/
│   ├── analyze.py           CLI: rich-formatted graph analysis
│   ├── migrate.py           CLI: single-file migration
│   ├── migrate_batch.py     CLI: batch migration
│   └── visualize.py         CLI: graph visualization
├── backend/
│   └── app.py               Flask API, port 5002
├── frontend/
│   └── src/
│       ├── App.jsx           6-step wizard
│       ├── components/       UI components
│       └── hooks/
│           └── useGraphMigration.js  All API state + calls
├── data/
│   └── chroma_db/           ChromaDB persistence directory
└── tests/
    ├── test_dependency_graph.py
    ├── test_graph_builder.py
    ├── test_cast_chunker.py
    └── test_validation.py
```

---

## 3. AST Layer — Deep Dive

The AST layer (`ast/`) provides a full tokenizer → parser → semantic analyzer pipeline for SAS code. It is used by `CASTChunker` for syntactic splitting and by `GraphMigrator` for enhanced macro variable initialization.

### 3.1 SAS Lexer

**File:** `ast/sas_lexer.py`

#### TokenType Enum (40+ values)

```python
class TokenType(Enum):
    # Literals
    INTEGER = auto()         # 42
    FLOAT = auto()           # 3.14, 1.5e-3
    STRING = auto()          # 'hello', "world"
    DATE_LITERAL = auto()    # '01JAN2023'd
    TIME_LITERAL = auto()    # '09:30:00't
    DATETIME_LITERAL = auto()# '01JAN2023:09:30:00'dt

    # Identifiers / keywords
    IDENTIFIER = auto()      # myvar, employee_data
    KEYWORD = auto()         # data, set, merge, proc, run ...
    PROC_NAME = auto()       # sql, means, sort, freq, print ...
    FORMAT = auto()          # DATE9., DOLLAR12.2
    INFORMAT = auto()
    LABEL = auto()

    # Macro
    MACRO_VAR = auto()       # &varname, &mylib.
    MACRO_FUNC = auto()      # %sysfunc(...)
    MACRO_KEYWORD = auto()   # %let, %macro, %mend, %if, %do ...

    # Operators
    ASSIGN = auto()          # =
    PLUS / MINUS / MULTIPLY / DIVIDE / POWER = auto()
    EQ / NE / LT / LE / GT / GE = auto()
    AND / OR / NOT = auto()
    IN / CONCAT = auto()     # in, ||

    # Punctuation
    SEMICOLON / COMMA / DOT / COLON = auto()
    LPAREN / RPAREN / LBRACKET / RBRACKET / LBRACE / RBRACE = auto()

    # Special
    COMMENT / NEWLINE / WHITESPACE / EOF / UNKNOWN = auto()
```

#### Tokenization Algorithm

The lexer uses a **priority-ordered list of compiled regex patterns**. At each position, it tries patterns in order and takes the first match. Critical ordering:

1. Block comments `/* ... */` and line comments `* ... ;` — caught first to avoid misidentifying `*` as MULTIPLY.
2. Macro keywords `%macro`, `%let`, etc. — before generic identifiers to avoid misclassification.
3. Macro variables `&varname` — before `&` operator.
4. Date/time literals `'01JAN2023'd` — before plain STRING, since `'text'` suffix `d/t/dt` marks temporal values.
5. Plain strings `'...'` and `"..."`.
6. Numbers — float patterns before integer to capture decimal point correctly.
7. Multi-character operators (`**`, `||`, `<=`, `>=`, `^=`, `~=`, `<>`) before single-char operators.
8. Single-char operators.
9. Identifiers — after all operators; classified into KEYWORD / PROC_NAME / IDENTIFIER.

```python
def _build_patterns(self) -> None:
    self.patterns = [
        (re.compile(r'/\*.*?\*/', re.DOTALL), TokenType.COMMENT),
        (re.compile(r'^\s*\*[^;]*;', re.MULTILINE), TokenType.COMMENT),
        (re.compile(r'%[a-zA-Z_][a-zA-Z0-9_]*'), self._classify_macro_token),
        (re.compile(r'&[a-zA-Z_][a-zA-Z0-9_]*\.?'), TokenType.MACRO_VAR),
        (re.compile(r"'[^']*'dt", re.IGNORECASE), TokenType.DATETIME_LITERAL),
        (re.compile(r"'[^']*'d",  re.IGNORECASE), TokenType.DATE_LITERAL),
        (re.compile(r"'[^']*'t",  re.IGNORECASE), TokenType.TIME_LITERAL),
        (re.compile(r"'[^']*'"),                   TokenType.STRING),
        (re.compile(r'\d+\.\d*([eE][+-]?\d+)?'),   TokenType.FLOAT),
        (re.compile(r'\*\*'),  TokenType.POWER),
        (re.compile(r'\|\|'), TokenType.CONCAT),
        # ... more single-char operators ...
        (re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'), self._classify_identifier),
        (re.compile(r'[ \t]+'), TokenType.WHITESPACE),
        (re.compile(r'\n'),    TokenType.NEWLINE),
    ]
```

#### Identifier Classification

```python
def _classify_identifier(self, value: str) -> TokenType:
    lower = value.lower()
    if lower in self.KEYWORDS:    return TokenType.KEYWORD
    if lower in self.PROC_NAMES:  return TokenType.PROC_NAME
    return TokenType.IDENTIFIER
```

**KEYWORDS** includes ~80 SAS keywords: control flow (`if`, `then`, `else`, `do`, `end`), DATA step statements (`set`, `merge`, `update`, `modify`, `keep`, `drop`, `retain`, `array`, `length`, `format`, `label`), common functions (`sum`, `mean`, `substr`, `lag`, `coalesce`, `input`, `put`), and PROC statement keywords (`class`, `var`, `model`, `tables`, `from`, `create`).

**PROC_NAMES** covers ~35 procedure names: `print`, `sort`, `means`, `freq`, `sql`, `transpose`, `append`, `reg`, `logistic`, `sgplot`, etc.

**MACRO_KEYWORDS** (prefixed `%`): `%macro`, `%mend`, `%let`, `%if`, `%then`, `%else`, `%do`, `%end`, `%global`, `%local`, `%sysfunc`, `%eval`, `%str`, `%quote`, `%scan`, `%substr`, `%upcase`, etc. (~30 values).

#### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `tokenize` | `() -> List[Token]` | Tokenize entire source; populates `self.tokens` |
| `get_token_stream` | `() -> Generator[Token, None, None]` | Lazy token generator |
| `peek_token` | `(offset=0) -> Token` | Look ahead without consuming |

Each `Token` carries: `type: TokenType`, `value: str`, `line: int`, `column: int`.

---

### 3.2 SAS AST

**File:** `ast/sas_ast.py`

#### NodeType Enum (30+ values)

```python
class NodeType(Enum):
    PROGRAM = auto()

    # Top-level constructs
    DATA_STEP = auto()
    PROC_STEP = auto()
    MACRO_DEF = auto()
    MACRO_CALL = auto()

    # Statements
    ASSIGNMENT = auto()
    IF_STATEMENT = auto()
    DO_LOOP = auto()
    SET_STATEMENT = auto()
    MERGE_STATEMENT = auto()
    OUTPUT_STATEMENT = auto()
    DROP_STATEMENT = auto()
    KEEP_STATEMENT = auto()
    WHERE_STATEMENT = auto()
    BY_STATEMENT = auto()
    RETAIN_STATEMENT = auto()
    LENGTH_STATEMENT = auto()
    FORMAT_STATEMENT = auto()
    LABEL_STATEMENT = auto()
    ARRAY_STATEMENT = auto()
    CALL_STATEMENT = auto()
    PUT_STATEMENT = auto()
    INPUT_STATEMENT = auto()
    INFILE_STATEMENT = auto()
    FILE_STATEMENT = auto()

    # Expressions
    BINARY_OP = auto()
    UNARY_OP = auto()
    FUNCTION_CALL = auto()
    VARIABLE = auto()
    LITERAL = auto()
    ARRAY_REF = auto()
    MACRO_VAR_REF = auto()

    # PROC body
    PROC_STATEMENT = auto()
    PROC_SQL_STATEMENT = auto()

    # Globals
    COMMENT = auto()
    OPTIONS = auto()
    LIBNAME = auto()
    FILENAME = auto()
    TITLE = auto()
```

#### ASTNode Base Class

```python
@dataclass
class ASTNode:
    node_type: NodeType
    line_start: int = 0
    line_end: int = 0
    children: List['ASTNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.node_type.name,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'metadata': self.metadata,
            'children': [c.to_dict() for c in self.children]
        }
```

#### Node Hierarchy

```
ProgramNode
├── data_steps: List[DataStepNode]
├── proc_steps: List[ProcNode]
├── macros: List[MacroNode]
└── global_statements: List[ASTNode]  (LIBNAME, FILENAME, OPTIONS, TITLE...)

DataStepNode
├── output_datasets: List[str]
├── input_datasets: List[str]
├── statements: List[ASTNode]        ← children for cAST splitting
├── variables_defined: List[str]
└── variables_used: List[str]

ProcNode
├── proc_name: str
├── options: Dict[str, Any]
├── input_datasets: List[str]
├── output_datasets: List[str]
└── statements: List[ASTNode]        ← children for cAST splitting

MacroNode
├── name: str
├── parameters: List[str]
├── body: List[ASTNode]              ← children for cAST splitting
└── local_vars: List[str]
```

#### Specialized Statement Nodes

| Node class | Key fields |
|------------|-----------|
| `AssignmentNode` | `target: str`, `expression: ExpressionNode` |
| `IfStatementNode` | `condition: ExpressionNode`, `then_branch: List[ASTNode]`, `else_branch: List[ASTNode]` |
| `DoLoopNode` | `loop_var: str`, `start/stop/by: ExpressionNode`, `body: List[ASTNode]` |
| `SetStatementNode` | `datasets: List[str]`, `options: Dict` |
| `MergeStatementNode` | `datasets: List[str]`, `by_vars: List[str]` |
| `FunctionCallNode` | `func_name: str`, `arguments: List[ExpressionNode]` |
| `BinaryOpNode` | `operator: str`, `left: ExpressionNode`, `right: ExpressionNode` |
| `VariableNode` | `name: str` |
| `LiteralNode` | `value: Any`, `literal_type: str` |
| `MacroVarRefNode` | `name: str` (the `&varname` reference) |
| `ProcStatementNode` | `keyword: str`, `options: Dict` |
| `ProcSQLStatementNode` | `sql_text: str` |

#### SASASTParser

The parser is a top-down recursive descent parser that receives the token stream from `SASLexer`.

```python
parser = SASASTParser(sas_code)
program = parser.parse()           # Returns ProgramNode
```

**Key parsing methods:**

| Method | What it parses |
|--------|---------------|
| `parse()` | Top-level: dispatches to parse_data_step, parse_proc, parse_macro, parse_global |
| `parse_data_step()` | `DATA outputs; body; RUN;` → `DataStepNode` |
| `parse_proc()` | `PROC name options; body; RUN/QUIT;` → `ProcNode` |
| `parse_macro()` | `%MACRO name(params); body; %MEND;` → `MacroNode` |
| `parse_statement()` | Dispatches to specific statement parsers |
| `parse_assignment()` | `var = expr;` → `AssignmentNode` |
| `parse_if_statement()` | `IF cond THEN ... ELSE ...;` → `IfStatementNode` |
| `parse_do_loop()` | `DO var = start TO stop BY step; body; END;` → `DoLoopNode` |
| `parse_expression()` | Pratt parser for expressions |
| `parse_function_call()` | `func(arg1, arg2)` → `FunctionCallNode` |

---

### 3.3 Semantic Analyzer

**File:** `ast/semantic_analyzer.py`

#### DataType and SymbolKind Enums

```python
class DataType(Enum):
    NUMERIC = auto()
    CHARACTER = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    UNKNOWN = auto()

class SymbolKind(Enum):
    VARIABLE = auto()
    DATASET = auto()
    MACRO_VAR = auto()
    MACRO = auto()
    LIBRARY = auto()
    FILEREF = auto()
    FORMAT = auto()
    INFORMAT = auto()
    ARRAY = auto()
```

#### Symbol Dataclass

```python
@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    data_type: DataType = DataType.UNKNOWN
    scope: str = "global"
    line_defined: int = 0
    line_last_used: int = 0
    is_initialized: bool = False
    length: Optional[int] = None    # For CHARACTER variables
    format: Optional[str] = None
    informat: Optional[str] = None
    label: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
```

Lookup key is `f"{name.lower()}:{kind.name}"` — case-insensitive, kind-aware.

#### SymbolTable

Implements lexical scoping with parent references:

```python
class SymbolTable:
    symbols: Dict[str, Symbol]     # key = "name:KIND"
    parent: Optional['SymbolTable']
    scope_name: str                # "global", data-step name, macro name

    def define(self, symbol: Symbol) -> None:   # Sets symbol.scope = self.scope_name
    def lookup(self, name, kind) -> Optional[Symbol]:  # Walks parent chain
    def create_child_scope(self, name: str) -> 'SymbolTable'
    def merge_from_child(self, child: 'SymbolTable') -> None:
        # Only MACRO_VAR symbols bubble up to parent
```

Child scopes are created for each DATA step and macro body. `merge_from_child` propagates `%LET` / `CALL SYMPUT` macro variable definitions back to the parent (global) scope.

#### DependencyInfo

```python
@dataclass
class DependencyInfo:
    datasets_read: Set[str]
    datasets_written: Set[str]
    macro_vars_used: Set[str]
    macro_vars_defined: Set[str]
    macros_called: Set[str]
    libraries_used: Set[str]
```

#### SemanticAnalyzer

Three-pass analysis:

```python
symbol_table, errors, dependency_info = analyzer.analyze(program_ast)
```

**Pass 1 — Macros:** Scan `program.macros`, register each macro in the global symbol table, create child scopes for their bodies, extract local variable definitions and `%LET` statements.

**Pass 2 — Global statements:** Process `LIBNAME`, `FILENAME`, `OPTIONS`, `TITLE`, and top-level `%LET`.

**Pass 3 — DATA steps and PROCs:** For each DATA step, create a child scope; analyze `SET`/`MERGE`/`UPDATE` inputs (datasets_read), output dataset declarations (datasets_written), all assignment targets (new variables), `CALL SYMPUT` (macro_vars_defined), and `&var` references (macro_vars_used). For PROCs, extract `DATA=` and `OUT=` options.

**Type Inference** (`_infer_function_return_type`):

| Function name | Inferred DataType |
|--------------|-------------------|
| `date`, `today`, `mdy`, `datepart` | DATE |
| `time`, `timepart` | TIME |
| `datetime` | DATETIME |
| `substr`, `trim`, `upcase`, `compress`, `cats`, `catx` | CHARACTER |
| `input` with date format | DATE |
| Others | NUMERIC or UNKNOWN |

**Output:**
- `symbol_table`: Populated global `SymbolTable` with nested child scopes.
- `errors`: List of `SemanticError(message, line, severity)`.
- `dependency_info`: Fully populated `DependencyInfo`.

**Python declaration generation:**

```python
init_code = analyzer.generate_python_declarations()
# Emits Python variable initializations for all discovered macro variables
# e.g.: start_date = "01JAN2023"  # SAS macro variable
```

---

## 4. cAST Chunking — Full Deep Dive

**File:** `core/cast_chunker.py`

### Background

The **cAST** (contextual Abstract Syntax Tree) algorithm is adapted from research by CMU / Augment Code. In their evaluation on code retrieval and generation tasks, cAST chunking improved **Recall@5 by +4.3%** and **Pass@1 by +2.67%** over fixed-size chunking. The key insight: splitting at syntactic boundaries (not arbitrary line counts) ensures each chunk is semantically complete and the LLM receives coherent, well-bounded context.

### CASTConfig

```python
@dataclass
class CASTConfig:
    max_chunk_size: int = 4500   # Non-whitespace chars ≈ 1500 tokens
    min_chunk_size: int = 300    # Non-whitespace chars ≈ 100 tokens
```

The **size metric** is non-whitespace character count (see `_get_size`). This is more stable than raw character count: SAS indentation varies wildly, but logic density is what matters for LLM context windows.

```python
@staticmethod
def _get_size(code: str) -> int:
    return sum(1 for c in code if not c.isspace())
```

### SASTChunk Dataclass

```python
@dataclass
class SASTChunk:
    source_code: str              # Extracted SAS source text
    ast_nodes: List[ASTNode]      # AST nodes this chunk covers
    line_start: int = 0           # 1-based line start in original file
    line_end: int = 0             # 1-based line end
    size: int = 0                 # Non-whitespace char count
    node_types: List[str] = ...   # e.g., ["DATA_STEP", "PROC_STEP"]
    context_header: str = ""      # Enclosing construct header for sub-chunks
    part_index: int = 0           # 0-based index within parent split (e.g., 0)
    total_parts: int = 1          # Total parts from parent split (e.g., 3)
    parent_node_type: str = ""    # NodeType of the split parent (e.g., "DATA_STEP")
```

When `total_parts > 1`, the chunk is a sub-chunk of a larger construct that was split. The LLM prompt includes a preamble: _"This is Part X of Y from a larger SAS construct. Enclosing construct: DATA output_ds; SET input_ds;"_.

### Core Algorithm: `_chunk_nodes()`

```python
def _chunk_nodes(
    self,
    nodes: List[ASTNode],
    source_lines: List[str],
    depth: int,
    context_header: str = ""
) -> List[SASTChunk]:
```

This is the heart of the algorithm. It processes a list of sibling AST nodes and produces a list of `SASTChunk` objects. The algorithm uses a **greedy merge accumulator** with **recursive splitting** for oversized nodes.

**Pseudocode:**

```
accumulator_nodes = []
accumulator_size = 0
chunks = []

for node in nodes:
    node_size = non_whitespace_size(extract_source(node))

    CASE 1: node_size > max_chunk_size
        # This single node is already too large
        flush accumulator → append chunk
        children = get_children(node)
        if children:
            # Recurse into children at depth+1
            node_header = build_context_header(node)
            combined_header = context_header + "\n" + node_header
            sub_chunks = _chunk_nodes(children, source_lines,
                                       depth+1, combined_header)
            chunks.extend(sub_chunks)
        else:
            # Leaf node too large → return as-is (cannot split further)
            chunks.append(SASTChunk(node_source, context_header=context_header))

    CASE 2: accumulator_size + node_size > max_chunk_size
        # Adding this node would exceed limit → flush first
        flush accumulator → append chunk
        accumulator = [node]
        accumulator_size = node_size

    CASE 3: fits in accumulator
        # Greedy merge
        accumulator.append(node)
        accumulator_size += node_size

flush remaining accumulator → append chunk
chunks = _merge_tiny_trailing(chunks)
return chunks
```

**Key invariants:**
- A chunk never exceeds `max_chunk_size` (unless it's an unsplittable leaf node).
- Sibling nodes that fit together are always merged (greedy).
- The recursion depth matches the SAS nesting depth (DATA/PROC → statements → DO blocks → IF branches).
- Context headers cascade: a sub-chunk inside a DO loop inside a DATA step sees: `"DATA output; SET input; DO i = 1 TO 10;"`.

### Context Header Building: `_build_context_header()`

```python
@staticmethod
def _build_context_header(node: ASTNode, source_lines: List[str]) -> str:
```

Produces a short header string that identifies the enclosing construct:

| Node type | Example output |
|-----------|---------------|
| `DataStepNode` | `"DATA employee_data; SET raw_employees;"` |
| `ProcNode` | `"PROC SQL;"` |
| `MacroNode` | `"%MACRO process_region(region, year);"` |
| `DoLoopNode` | `"DO i = 1 TO n;"` or `"DO;"` (for `DO WHILE`) |
| `IfStatementNode` | `"IF ... THEN DO;"` |
| Fallback | First source line of the node |

For `DataStepNode`, the builder additionally peeks at the first 3 statements to find a `SET_STATEMENT` or `MERGE_STATEMENT` and appends it:

```python
if isinstance(node, DataStepNode):
    datasets = ', '.join(node.output_datasets) if node.output_datasets else 'unknown'
    header = f"DATA {datasets};"
    for stmt in node.statements[:3]:
        if stmt.node_type == ASTNodeType.SET_STATEMENT:
            header += f" SET {', '.join(stmt.datasets)};"
            break
    return header
```

### Post-Processing: `_merge_tiny_trailing()`

After the main greedy pass, a second pass merges "orphan" chunks that are smaller than `min_chunk_size` into their predecessor, provided the merged result would not exceed `max_chunk_size`:

```python
def _merge_tiny_trailing(self, chunks: List[SASTChunk]) -> List[SASTChunk]:
    merged = []
    for chunk in chunks:
        if (merged
                and chunk.size < self.config.min_chunk_size
                and merged[-1].size + chunk.size <= self.config.max_chunk_size):
            # Merge: combine source, union node lists, keep earlier context_header
            prev = merged[-1]
            combined_source = prev.source_code + "\n" + chunk.source_code
            merged[-1] = SASTChunk(
                source_code=combined_source,
                ast_nodes=prev.ast_nodes + chunk.ast_nodes,
                line_start=prev.line_start,
                line_end=max(prev.line_end, chunk.line_end),
                size=self._get_size(combined_source),
                node_types=prev.node_types + chunk.node_types,
                context_header=prev.context_header or chunk.context_header,
            )
        else:
            merged.append(chunk)
    return merged
```

This prevents tiny trailing statement groups (e.g., a single `RUN;`) from becoming their own chunk.

### Child Accessor: `_get_children()`

SAS-specific per-type child mapping:

```python
def _get_children(self, node: ASTNode) -> List[ASTNode]:
    if isinstance(node, ProgramNode):    return list(node.children)
    elif isinstance(node, DataStepNode): return list(node.statements)
    elif isinstance(node, ProcNode):     return list(node.statements)
    elif isinstance(node, MacroNode):    return list(node.body)
    elif isinstance(node, IfStatementNode):
        return list(node.then_branch) + list(node.else_branch)
    elif isinstance(node, DoLoopNode):   return list(node.body)
    elif hasattr(node, 'children') and node.children:
        return list(node.children)
    return []
```

### Public Entry Points

**`chunk_code(code: str) -> List[SASTChunk]`** — Full file chunking:
1. Parses `code` → `ProgramNode`.
2. If parsing fails → returns single `SASTChunk` tagged `UNPARSEABLE`.
3. Otherwise, calls `_chunk_nodes(program.children, source_lines, depth=0)`.

**`chunk_node(node: ASTNode, source_lines: List[str]) -> List[SASTChunk]`** — Single-node splitting (called by `ChunkOptimizer` for oversized single-node chunks):
1. If node fits in `max_chunk_size` or has no children → return single chunk.
2. Otherwise, build context header, recurse into children.
3. Tag all sub-chunks with `context_header`, `part_index`, `total_parts`, `parent_node_type`.

### Integration with ChunkOptimizer

When `ChunkOptimizer._split_large_chunk()` encounters a **single-node** chunk exceeding `max_chunk_tokens`:

```python
cast_chunks = self.cast_chunker.chunk_code(node.source_code)
# if len(cast_chunks) > 1:
for i, cast_chunk in enumerate(cast_chunks):
    sub_node = DependencyNode(
        node_id=f"{parent_node_id}_cast_{i}",
        metadata={
            'cast_split': True,
            'parent_node_id': parent_node_id,
            'part_index': i,
            'total_parts': len(cast_chunks),
            'context_header': cast_chunk.context_header,
            'cast_node_types': cast_chunk.node_types,
        },
        line_start=cast_chunk.line_start + node.line_start - 1,
        line_end=cast_chunk.line_end + node.line_start - 1,
    )
```

Each cAST sub-chunk becomes its own `DependencyNode` and `Chunk`, tagged with `cast_split=True` for later reassembly.

### Reassembly in CodeReconciler

`CodeReconciler._reassemble_cast_chunks()`:

1. Scans `converted_chunks` for `chunk.get('cast_split') == True`.
2. Groups by `parent_node_id`.
3. Sorts each group by `part_index`.
4. Concatenates `pyspark_code` parts, deduplicating import lines within the group.
5. Produces one reassembled chunk dict with `chunk_id = f"{parent_id}_reassembled"`.

This ensures the converted sub-chunks flow together as a single unit in the final script, avoiding duplicate `import pyspark.sql.functions as F` lines appearing multiple times.

---

## 5. Core Graph Infrastructure

### 5.1 Dependency Graph

**File:** `core/dependency_graph.py`

#### NodeType (7 types)

| NodeType | Description | Example |
|----------|-------------|---------|
| `DATASET` | A SAS dataset | `work.employee_data` |
| `DATA_STEP` | A DATA step block | `DATA output; SET input; RUN;` |
| `PROC` | A PROC step block | `PROC SORT DATA=emp; BY dept; RUN;` |
| `MACRO` | A macro definition | `%MACRO calc_tax(rate); ... %MEND;` |
| `MACRO_VARIABLE` | A macro variable | `&start_date`, `&report_year` |
| `LIBRARY` | A LIBNAME reference | `LIBNAME mylib '/data/';` |
| `FILE_REF` | A FILENAME reference | `FILENAME raw '/data/input.csv';` |

#### EdgeType (8 types)

| EdgeType | Direction | Description |
|----------|-----------|-------------|
| `READS_FROM` | dataset → data_step | DATA step reads from dataset (SET/MERGE/UPDATE/MODIFY) |
| `WRITES_TO` | data_step → dataset | DATA step creates dataset |
| `CALLS` | macro → macro | Macro calls another macro |
| `USES_VARIABLE` | macro_var → node | Node reads `&varname` |
| `DEFINES_VARIABLE` | node → macro_var | Node writes macro var (`%LET`, `CALL SYMPUT`) |
| `DEPENDS_ON_FILE` | file_ref → node | Node references INFILE/FILE fileref |
| `PROC_INPUT` | dataset → proc | PROC reads dataset (DATA= option) |
| `PROC_OUTPUT` | proc → dataset | PROC creates dataset (OUT= option) |

#### DependencyNode Dataclass

```python
@dataclass
class DependencyNode:
    node_id: str             # Unique ID, e.g. "data_step_3"
    node_type: NodeType
    name: str                # Human-readable, e.g. "employee_data"
    source_code: str = ""    # Original SAS code block
    metadata: Dict[str, Any] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0
```

Equality and hashing are based solely on `node_id`.

#### DependencyGraph Key Methods

```python
graph = DependencyGraph()                           # NetworkX DiGraph backend

# Adding nodes and edges
graph.add_node(node: DependencyNode)
graph.add_edge(from_id, to_id, edge_type: EdgeType, metadata=None)

# Traversal
graph.get_dependencies(node_id, depth=1)   # What this node depends on
graph.get_dependents(node_id, depth=1)     # What depends on this node
graph.get_nodes_by_type(NodeType.MACRO)
graph.get_root_nodes()                     # Nodes with no predecessors
graph.get_leaf_nodes()                     # Nodes with no successors

# Ordering
graph.topological_sort() -> List[DependencyNode]
graph.get_execution_layers() -> List[List[DependencyNode]]

# Cycle handling
graph.has_cycles() -> bool
graph.find_cycles() -> List[List[str]]     # Simple cycles via nx.simple_cycles
graph.break_cycles() -> List[Tuple[str, str, EdgeType]]  # Removes strategic edges

# Subgraph
graph.get_subgraph(node_ids: List[str]) -> DependencyGraph

# Serialization
graph.to_dict() / DependencyGraph.from_dict(data)
```

#### `break_cycles()` — 3-Tier Strategy

1. **Self-referential edges** (`A → A`): Remove immediately.
2. **In-place update pattern**: `DATASET → DATA_STEP → DATASET` (SAS datasets modified in-place). Removes the `READS_FROM` edge and marks the DATA step node `metadata['in_place_update'] = True`.
3. **Weakest-edge removal**: Assigns priority scores to edge types (`READS_FROM=1`, `USES_VARIABLE=1`, `PROC_INPUT=2`, `DEFINES_VARIABLE=2`, `WRITES_TO=3`, `PROC_OUTPUT=3`, `CALLS=4`). Removes the lowest-priority edge in the cycle.

---

### 5.2 Graph Builder

**File:** `core/graph_builder.py`

The `GraphBuilder` orchestrates SAS parsing and graph construction in a 6-step sequence:

```python
builder = GraphBuilder.from_file("input.sas")
graph = builder.build_graph()
```

**Construction order:**

1. `_add_library_nodes()` — Regex-scan raw SAS code for `LIBNAME` statements → `NodeType.LIBRARY` nodes.
2. `_add_file_nodes()` — Regex-scan for `FILENAME` statements → `NodeType.FILE_REF` nodes.
3. `_add_macro_nodes(macro_deps)` — Two-pass: first create `NodeType.MACRO` nodes, then add `DEFINES_VARIABLE`/`USES_VARIABLE` edges to macro variable nodes.
4. `_add_data_step_nodes(data_step_deps)` — Create `NodeType.DATA_STEP` nodes; add `WRITES_TO` edges to output datasets, `READS_FROM` edges from input datasets.
5. `_add_proc_nodes(proc_deps)` — Create `NodeType.PROC` nodes; add `PROC_INPUT`/`PROC_OUTPUT` edges.
6. `_add_cross_references(dependencies)` — Add `CALLS` edges between macros.

**Lazy `_find_or_create_dataset_node(dataset_name)`:**

```python
def _find_or_create_dataset_node(self, dataset_name: str) -> DependencyNode:
    existing = self._find_node_by_name(dataset_name, NodeType.DATASET)
    if existing:
        return existing
    node = DependencyNode(
        node_id=self._generate_node_id("dataset"),
        node_type=NodeType.DATASET,
        name=dataset_name,
        metadata={'created_implicitly': True}
    )
    self.graph.add_node(node)
    return node
```

Datasets appear as nodes even if only referenced as inputs, never explicitly created. This enables cross-file analysis.

**Summary output:**

```python
builder.get_summary()  # ->
{
    'total_nodes': 42,
    'total_edges': 67,
    'has_cycles': False,
    'node_counts_by_type': {'dataset': 15, 'data_step': 8, 'proc': 6, ...},
    'root_nodes': 3,
    'leaf_nodes': 7
}
```

---

### 5.3 Dependency Extractor

**File:** `parsers/dependency_extractor.py`

Regex-based extraction. The key data structures:

```python
@dataclass
class DataStepDependencies:
    outputs: List[str]           # Created datasets (DATA statement)
    inputs: List[str]            # Input datasets (SET, MERGE, UPDATE, MODIFY)
    macro_vars_used: List[str]   # &var references
    macro_vars_defined: List[str]# CALL SYMPUT / CALL SYMPUTX
    file_refs: List[str]         # INFILE, FILE filerefs

@dataclass
class ProcDependencies:
    proc_name: str
    inputs: List[str]            # DATA= option
    outputs: List[str]           # OUT= option
    file_refs: List[str]
    macro_vars_used: List[str]

@dataclass
class MacroDependencies:
    macro_name: str
    calls: List[str]             # %other_macro(...) calls
    macro_vars_used: List[str]
    macro_vars_defined: List[str]# %LET statements inside macro
    datasets_referenced: List[str]
```

**Extraction patterns (key examples):**

| Pattern | Regex | Extracts |
|---------|-------|---------|
| SET statement | `\bSET\s+([^;]+)` | Input datasets |
| MERGE statement | `\bMERGE\s+([^;]+)` | Input datasets |
| UPDATE/MODIFY | `\bUPDATE\s+([^;]+)` | Input datasets |
| PROC DATA= | `\bDATA\s*=\s*([^\s;]+)` | PROC input |
| PROC OUT= | `\bOUT\s*=\s*([^\s;]+)` | PROC output |
| PROC SQL FROM | `\bFROM\s+([^\s;,WHERE]+)` | SQL input tables |
| PROC SQL CREATE | `CREATE\s+TABLE\s+([^\s(;]+)` | SQL output tables |
| CALL SYMPUT | `CALL\s+SYMPUT[X]?\s*\(\s*["\']([^"\']+)["\']` | Macro var definitions |
| Macro variable | `&([a-zA-Z_]\w*)` | Macro var references |
| Macro call | `%([a-zA-Z_]\w*)\s*\(` | Macro calls |
| LIBNAME | `LIBNAME\s+([a-zA-Z_]\w*)\s+["\']?([^;"\']+)` | Libraries |
| FILENAME | `FILENAME\s+([a-zA-Z_]\w*)\s+["\']([^"\']+)["\']` | File refs |

**`_parse_dataset_list(dataset_string)`:**

Handles: `"data1"`, `"data1 data2 data3"`, `"mylib.dataset"`, `"data1(keep=var1 var2)"`.

1. Remove options in parentheses: `re.sub(r'\([^)]*\)', '', s)`.
2. Split on `[\s,]+`.
3. Filter with `^[a-zA-Z_][\w\.]*$` (valid name pattern).
4. Strip SQL keywords: `run`, `quit`, `by`, `where`, `if`.

Automatic exclusions for macro variable names: `sysdate`, `systime`, `sysday`, `syslast`, `sysrc`, `sqlobs`, `sqlrc`.

---

### 5.4 Schema Tracker

**File:** `core/schema_tracker.py`

#### DataType Enum

```python
class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    DOUBLE = "double"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"
```

#### ColumnInfo

```python
@dataclass
class ColumnInfo:
    name: str
    data_type: DataType = DataType.UNKNOWN
    format: Optional[str] = None       # SAS format, e.g. "DATE9.", "DOLLAR12.2"
    label: Optional[str] = None
    length: Optional[int] = None       # Character length
    source: Optional[str] = None       # "LENGTH statement", "FORMAT statement", etc.
```

#### DatasetSchema — Immutable Transformation Pattern

All transformation methods return **new** `DatasetSchema` instances (immutable/functional style):

```python
schema = DatasetSchema(name="employee_data")
schema.add_column(ColumnInfo(name="salary", data_type=DataType.DOUBLE, format="DOLLAR12.2"))

# KEEP: retain only listed columns
kept = schema.apply_keep(["emp_id", "salary", "dept"])

# DROP: remove listed columns
dropped = schema.apply_drop(["temp_col", "internal_flag"])

# RENAME: create new schema with renamed columns
renamed = schema.apply_rename({"old_name": "new_name", "dept_code": "department"})

# MERGE: combine two schemas (MERGE statement)
merged = schema1.merge_schema(schema2, prefer_other=False)
```

Case-insensitive column lookup:

```python
col = schema.get_column("SALARY")   # Finds "salary" regardless of case
```

#### ExecutionContext

Maintains migration state across all chunks:

```python
context = ExecutionContext()

# Dataset schemas
context.add_dataset(schema)
context.get_dataset("employee_data")    # Case-insensitive
context.update_dataset("employee_data", new_schema)

# Macro variables (resolved values)
context.add_macro_var("start_date", "2023-01-01")
context.resolve_macro_var("start_date")

# Libraries and file references
context.add_library("mylib", "/data/employee/")
context.get_library("mylib")

# Variable name mapping (SAS → PySpark)
context.map_variable_name("employee_data", "employee_df")
context.get_pyspark_variable_name("employee_data")  # → "employee_df"

# Converted chunks
context.add_converted_code("chunk_001", pyspark_code)
context.get_converted_code("chunk_001")
```

The `variable_name_map` is the mechanism that prevents variable name drift. Chunk 1 might name a DataFrame `employee_df`; without the map, Chunk 3 might independently call it `employees_df`. The map normalizes this.

#### SchemaInferencer

Infers schemas from parsed SAS structures:

```python
inferencer = SchemaInferencer()
schema = inferencer.infer_from_data_step(data_step_dict, input_schemas, context)
```

**Format-to-type mapping:**

| SAS format pattern | Inferred DataType |
|--------------------|-------------------|
| Contains `date` | DATE |
| Contains `datetime` or `time` | DATETIME |
| Starts with `$` | STRING |
| `dollar`, `comma`, `percent` | DOUBLE |
| Starts with `z`, contains `best` | DOUBLE |

---

### 5.5 Chunk Optimizer

**File:** `core/chunk_optimizer.py`

#### Chunk Dataclass

```python
@dataclass
class Chunk:
    chunk_id: str                     # e.g., "chunk_001"
    nodes: List[DependencyNode]       # Graph nodes in this chunk
    dependencies: List[str]           # Chunk IDs this chunk depends on
    source_code: str = ""             # Combined SAS source
    context: Dict[str, Any] = ...     # Metadata: has_macros, node_types, etc.
    estimated_tokens: int = 0         # non_whitespace_chars // 3
    layer: int = 0                    # Execution layer (for parallelism)
```

Token estimation:
```python
non_ws = sum(1 for c in self.source_code if not c.isspace())
self.estimated_tokens = non_ws // 3
```

#### Parameters

```python
ChunkOptimizer(
    graph,
    min_chunk_tokens=100,    # Merge smaller chunks
    max_chunk_tokens=2000,   # Split larger chunks
    target_chunk_tokens=1000 # Merge target
)
```

The `CASTChunker` is initialized with scaled limits: `max_chunk_size = max_chunk_tokens * 3` (converting token estimate back to non-whitespace chars).

#### Chunking Algorithm (`generate_chunks()`)

1. **Cycle breaking**: If `graph.has_cycles()`, call `graph.break_cycles()` first.
2. **Execution layers**: `graph.get_execution_layers()` — nodes in the same layer have no dependencies between them.
3. **Initial chunks from layers**: Within each layer, `_group_related_nodes()` groups:
   - `MACRO` nodes with `MACRO_VARIABLE` nodes they define.
   - `DATA_STEP` nodes with their output `DATASET` nodes.
   - `PROC` nodes with their output `DATASET` nodes.
4. **Merge small chunks**: Within each layer, sort by `estimated_tokens`, greedily merge chunks below `min_chunk_tokens` if merged total ≤ `target_chunk_tokens`.
5. **Split large chunks**: Chunks exceeding `max_chunk_tokens` are split:
   - **Multi-node chunk**: Split at node boundaries, targeting `target_chunk_tokens` per piece.
   - **Single-node chunk**: Delegate to `CASTChunker.chunk_code(node.source_code)` for AST-aware splitting.
6. **Add chunk dependencies**: Build `node_id → chunk_id` map; for each chunk, walk its nodes' graph predecessors to find which other chunks they depend on.
7. **Enrich chunk context**: Add `has_macros`, `has_data_steps`, `has_procs`, `node_types`, `node_names`, `dependency_count` to `chunk.context`.

**cAST statistics:**
```python
stats = optimizer.get_cast_stats()
# {'nodes_split_by_cast': 3, 'subchunks_created': 11}
```

---

## 6. Migration Pipeline

### 6.1 Context Enricher

**File:** `migration/context_enricher.py`

#### EnrichedContext Container

```python
class EnrichedContext:
    chunk_info: Dict[str, Any]          # chunk_id, node_types, cAST metadata
    dependency_info: Dict[str, Any]     # upstream/downstream nodes
    schema_info: Dict[str, Any]         # input/output dataset schemas
    examples: List[Dict]                # RAG-retrieved patterns
    execution_context: Dict[str, Any]   # available datasets, variable_mappings
    migration_guide: str                # Full migration guide text
    additional_context: Dict[str, Any]
```

#### 5-Step Context Building (`enrich_chunk_context`)

1. **Chunk info**: node types, names, `is_cast_split`, `cast_part_index`, `cast_total_parts`, `cast_context_header`.
2. **Dependency info**: walk graph for 1-hop predecessors (what this chunk needs) and successors (what needs this chunk).
3. **Schema info**: for each DATA_STEP node, look up schemas of its input/output datasets from `execution_context`.
4. **RAG examples**: `example_retriever.create_example_context(chunk)` → similarity-ranked patterns.
5. **Execution context**: available dataset names, macro variable names, library refs, `variable_name_map`.

#### LLM Prompt Structure (`build_llm_prompt`)

```
[System preamble: expert SAS/PySpark migrator]

MIGRATION GUIDE:
  {migration_guide[:2000]}

DATASET SCHEMAS:
  input_employee_data (5 columns):
    - emp_id: integer
    - salary: double (format: DOLLAR12.2)
    ...

DEPENDENCIES:
  This code depends on:
    - employee_data (dataset)
    - calc_bonus (macro)

VARIABLE NAME MAPPINGS (SAS → PySpark):
  - employee_data → employee_df
  - dept_summary → dept_summary_df

SIMILAR EXAMPLES:
  Example 1 (similarity: 0.87):
  SAS:     DATA step with MERGE ...
  PySpark: employee_df.join(dept_df, ...) ...

[IF cAST sub-chunk]:
IMPORTANT CONTEXT - This is Part 2 of 4 from a larger SAS construct.
Enclosing construct: DATA output_emp; SET employees;
Convert only the code below. The other parts are being converted separately.

SAS CODE TO CONVERT:
```sas
{chunk.source_code}
```

INSTRUCTIONS:
1–6: PySpark best practices, type safety, comments, variable naming

[JSON response format]:
{
    "pyspark_code": "...",
    "mapping": "...",
    "variables_created": ["employee_df", ...]
}
```

---

### 6.2 Graph Migrator

**File:** `migration/graph_migrator.py`

#### MigrationResult Dataclass

```python
@dataclass
class MigrationResult:
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
```

#### 7-Phase Orchestration (`migrate_file`)

```python
result = migrator.migrate_file("input.sas", "./output", visualize=False)
```

| Phase | What happens |
|-------|-------------|
| 1. Graph construction | `GraphBuilder.from_file()` → `build_graph()` |
| 2. Chunk generation | `ChunkOptimizer.generate_chunks()` |
| 3. Execution context init | `ExecutionContext()` created; RAG enabled if `use_rag=True` |
| 4. Parallel LLM conversion | `asyncio.run(_convert_chunks_parallel())` — layer by layer, semaphore(5) |
| 5. Macro variable extraction | `SASParser.get_macro_var_initialization()` + optional AST semantic analysis |
| 5b. AST semantic analysis | `SASASTParser` + `SemanticAnalyzer.analyze()` if AST module available |
| 6. Reconciliation | `CodeReconciler.reconcile_chunks_with_report()` |
| 7. Execution order | `ExecutionOrderOptimizer.optimize_code()` |

**Azure OpenAI clients:**

```python
self.client = AzureOpenAI(api_version="2024-08-01-preview", ...)       # sync
self.async_client = AsyncAzureOpenAI(api_version="2024-08-01-preview", ...)  # async
```

**Async parallel conversion (`_convert_chunks_parallel`):**

- Groups chunks by `layer`.
- Within each layer, separates **cAST sub-chunks** (must be converted sequentially to maintain context) from **independent chunks**.
- Independent chunks: `asyncio.gather(*tasks)` with `asyncio.Semaphore(max_concurrent=5)`.
- cAST sub-chunk groups: each group converted sequentially, but different groups run concurrently.
- After each layer completes, updates `execution_context.variable_name_map` from `variables_created`.

**Success determination:**

```python
# Non-critical patterns (warnings, not errors):
non_critical = ['warning', 'duplicate', 'multiple times', 'may not exist',
                'may not be defined', 'never defined', 'used but never']

critical_errors = [e for e in result.errors
                   if not any(x in e.lower() for x in non_critical)]

result.success = (result.chunks_converted > 0 and len(critical_errors) == 0)
```

**Output artifacts:**

| File | Content |
|------|---------|
| `{stem}.py` | Generated PySpark code |
| `{stem}_mapping.txt` | Chunk-by-chunk SAS → PySpark mapping |
| `{stem}_validation.txt` | Variable lifecycle report + fixes applied |
| `{stem}_result.json` | Full `MigrationResult` as JSON |

---

### 6.3 Variable Tracker

**File:** `migration/variable_tracker.py`

Analyzes generated PySpark code to validate variable lifecycle.

#### Key Data Structures

```python
class VariableState(Enum):
    UNDEFINED = "undefined"
    DEFINED = "defined"
    DELETED = "deleted"

@dataclass
class VariableInfo:
    name: str
    definitions: List[VariableOccurrence]
    usages: List[VariableOccurrence]
    deletions: List[VariableOccurrence]

@dataclass
class ValidationIssue:
    issue_type: str    # 'undefined', 'use_after_delete', 'duplicate_definition', 'unused'
    variable_name: str
    line_number: int
    message: str
    severity: str = "error"   # 'error', 'warning', 'info'
    suggested_fix: str = ""
```

#### Detection Patterns

```python
self.patterns = {
    'definition':  r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?!.*==)',  # var = ...
    'deletion':    r'^\s*del\s+([a-zA-Z_][a-zA-Z0-9_]*)',             # del var
    'df_usage':    r'\b(\w+)\s*\.\s*(select|filter|join|groupBy|...)', # df.method(
    'arg_usage':   r'(?:spark\.table|F\.col|\.join)\s*\(\s*(\w+)',     # func(var
    'expr_usage':  r'(?<!["\'])([a-zA-Z_][a-zA-Z0-9_]*_df)\b',       # var_df refs
    'macro_ref':   r'&([a-zA-Z_][a-zA-Z0-9_]*)',                       # &sas_macro_var
}
```

**Ignored variables (PySpark/Python builtins):**

```python
self.ignore_vars = {
    'spark', 'F', 'T', 'Window', 'Row', 'SparkSession',
    'StructType', 'StructField', 'StringType', 'IntegerType', ...
    'datetime', 'date', 'print', 'len', 'str', 'int', 'float', ...
}
```

**Three-pass analysis:**

1. Scan all lines → record definitions, usages, deletions.
2. Validate lifecycle: use-before-define (warning), use-after-delete (warning), duplicate definitions (info), unused variables (info).
3. Detect common SAS macro variable names appearing as undefined Python variables → add to `macro_vars` dict with default values.

**Auto-fix via `suggest_fixes(code)`:**

- Inserts macro variable initialization block after imports.
- Adds placeholder `spark.read.csv(...)` definitions for undefined DataFrames.
- Comments out `del var` statements where the variable is used later.

---

### 6.3b Batch Migrator

**File:** `migration/batch_migrator.py`

#### BatchMigrationResult

```python
@dataclass
class BatchMigrationResult:
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_chunks_converted: int = 0
    total_chunks: int = 0
    total_execution_time: float = 0.0
    start_time: str = ""
    end_time: str = ""
    file_results: List[MigrationResult] = field(default_factory=list)
    errors: Dict[str, List[str]] = field(default_factory=dict)  # file → errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": ...,
            "success_rate": f"{(successful/total*100):.1f}%",
            "file_results": [r.to_dict() for r in self.file_results],
            ...
        }
```

#### BatchMigrator

```python
BatchMigrator(
    migrator: GraphMigrator,   # Pre-configured migrator
    max_workers: int = 4,      # ThreadPoolExecutor workers
    continue_on_error: bool = True   # Continue if individual files fail
)
self._lock = threading.Lock()  # Thread-safe aggregation
```

**File discovery:**

```python
sas_files = migrator_obj.discover_sas_files(
    directory="/data/sas_programs",
    pattern="*.sas",
    recursive=True        # Uses rglob() vs glob()
)
```

Returns sorted `List[Path]`, filtered to `.sas` suffix only.

**`migrate_file_safe(sas_file, output_dir)`:**

Wraps `self.migrator.migrate_file()`. Catches all exceptions and returns `MigrationResult(success=False, errors=[str(e)])` on error — never raises.

**`migrate_batch()` — concurrent execution:**

```python
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    # Submit all files upfront
    future_to_file = {
        executor.submit(self.migrate_file_safe, f, output_dir): f
        for f in sas_files
    }

    for future in as_completed(future_to_file):
        sas_file = future_to_file[future]
        try:
            result = future.result()           # Get result or re-raise
            with self._lock:                   # Thread-safe aggregation
                batch_result.file_results.append(result)
                if result.success:
                    batch_result.successful_files += 1
                    ...
                else:
                    batch_result.failed_files += 1
                    batch_result.errors[str(sas_file)] = result.errors

            if progress_callback:
                progress_callback(sas_file, completed, total)

            if not self.continue_on_error and not result.success:
                for f in future_to_file:
                    f.cancel()    # Cancel remaining
                break

        except Exception as e:
            with self._lock:
                batch_result.errors[str(sas_file)] = [str(e)]
            if not self.continue_on_error:
                ...cancel...
```

**Three-tier error handling:**
1. `migrate_file_safe` catch (file-level)
2. `future.result()` catch (executor-level)
3. `continue_on_error` cancellation (batch-level)

**Markdown summary report** (`generate_batch_summary`):

```markdown
# BATCH MIGRATION SUMMARY
## Overall Statistics
- Total Files: 12
- Successful: 10
- Failed: 2
- Success Rate: 83.3%
- Total Chunks Converted: 87/94
## Failed Files
### /data/problematic.sas
**Errors:** - Graph cycle could not be resolved
## Successful Files
| File | Chunks | Warnings | Time (s) |
|------|--------|----------|----------|
| program1.sas | 8/8 | 2 | 45.23 |
```

**Usage example:**

```python
from graph_approach.migration.graph_migrator import GraphMigrator
from graph_approach.migration.batch_migrator import BatchMigrator

migrator = GraphMigrator(api_key=KEY, azure_endpoint=ENDPOINT, model="gpt-4")
batch = BatchMigrator(migrator, max_workers=4, continue_on_error=True)

def on_progress(file, idx, total):
    print(f"[{idx}/{total}] Completed: {file.name}")

result = batch.migrate_batch(
    sas_directory="/data/programs/",
    output_dir="/data/output/",
    pattern="*.sas",
    recursive=True,
    progress_callback=on_progress
)

batch.generate_batch_summary(result, "/data/output/batch_summary.md")
print(f"Success rate: {result.successful_files}/{result.total_files}")
```

---

### 6.4 Execution Order Optimizer

**File:** `migration/execution_order.py`

Operates on the **final assembled PySpark script** (after reconciliation) to ensure blocks are in correct execution order.

#### BlockType Enum

```python
class BlockType(Enum):
    IMPORT = "import"
    SPARK_INIT = "spark_init"
    MACRO_VAR = "macro_var"
    DATA_LOAD = "data_load"
    TRANSFORM = "transform"
    AGGREGATION = "aggregation"
    OUTPUT = "output"
    COMMENT = "comment"
    OTHER = "other"
```

#### Key Structures

```python
@dataclass
class ExecutionBlock:
    block_id: str
    code: str
    block_type: BlockType
    line_start: int
    line_end: int
    defines: Set[str]       # Variables defined in this block
    uses: Set[str]          # Variables used (consumed) in this block
    dependencies: Set[str]  # Block IDs this block depends on

@dataclass
class DependencyIssue:
    issue_type: str         # 'circular', 'missing', 'order'
    description: str
    blocks_involved: List[str]
    suggested_fix: str = ""
```

#### Algorithm

1. **Parse** the assembled code into `ExecutionBlock` objects by detecting natural breaks (blank lines, comment sections, import groups).
2. **Analyze** each block: classify `BlockType`, extract `defines` (assignment targets) and `uses` (DataFrame method call receivers, RHS references).
3. **Build dependency graph**: map `variable → block_id` for the first definition; for each block, add edges from blocks whose defines this block uses.
4. **Detect issues**: circular dependencies, undefined variables, out-of-order definitions.
5. **Topological sort**: reorder blocks to ensure dependency order.

```python
optimizer = ExecutionOrderOptimizer()
optimized_code, changes = optimizer.optimize_code(pyspark_code)
# changes: ["Moved block_3 before block_1 (variable dependency)"]
```

---

### 6.5 Code Reconciler

**File:** `migration/code_reconciler.py`

#### ReconciliationResult

```python
@dataclass
class ReconciliationResult:
    code: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    validation_report: str = ""
```

#### 10-Step Reconciliation Process

```python
result = reconciler.reconcile_chunks_with_report(
    converted_chunks,      # List[Dict] from LLM
    execution_context,
    sas_macro_vars=init_block  # Optional Python init code
)
```

| Step | What happens |
|------|-------------|
| 0 | **Reassemble cAST sub-chunks** (`_reassemble_cast_chunks`) — groups by `parent_node_id`, sorts by `part_index`, merges code, deduplicates imports within group |
| 1 | **Filter invalid chunks** — skip empty, comment-only, placeholder chunks |
| 2 | **Extract and deduplicate imports** — categorize `from X import Y,Z` and `import X`; merge per-module, sort alphabetically |
| 3 | **Build variable mapping** — find DataFrames with similar names (`employee_df` vs `employee_data`), pick canonical name (prefers `_df` suffix) |
| 4 | **Extract code blocks** with `defines`/`uses` metadata |
| 5 | **Apply variable name consistency** — regex word-boundary replacement of old → canonical names |
| 6 | **Remove duplicate definitions** — if same DataFrame defined multiple times, keep longest definition |
| 7 | **Topological reorder** — build block dependency graph from defines/uses, sort |
| 8 | **Assemble script** — header + imports + SparkSession init + macro vars init + code blocks |
| 9 | **Validate and fix** (`VariableTracker`) — auto-fix undefined vars and use-after-delete |
| 10 | **LLM cleanup** (optional) — for files ≤500 lines: single LLM call; for larger: split at blank lines, clean each section |

**`_reassemble_cast_chunks()` in detail:**

```python
def _reassemble_cast_chunks(self, chunks):
    cast_groups = defaultdict(list)
    regular_chunks = []

    for chunk in chunks:
        if chunk.get('cast_split'):
            cast_groups[chunk['parent_node_id']].append(chunk)
        else:
            regular_chunks.append(chunk)

    for parent_id, group in cast_groups.items():
        group.sort(key=lambda c: c.get('part_index', 0))

        # Merge code parts
        merged_code = '\n\n'.join(part['pyspark_code'] for part in group)

        # Deduplicate imports within group
        seen_imports = set()
        deduped_lines = []
        for line in merged_code.split('\n'):
            if line.strip().startswith(('import ', 'from ')):
                if line.strip() not in seen_imports:
                    seen_imports.add(line.strip())
                    deduped_lines.append(line)
            else:
                deduped_lines.append(line)

        regular_chunks.append({
            'chunk_id': f"{parent_id}_reassembled",
            'pyspark_code': '\n'.join(deduped_lines),
            'variables_created': list(dict.fromkeys(all_variables))  # deduped, ordered
        })

    return regular_chunks
```

---

## 7. RAG System

**Files:** `rag/pattern_store.py`, `rag/example_retriever.py`

### PatternStore

```python
store = PatternStore(db_path="data/chroma_db/")
```

**ChromaDB mode** (when `chromadb` is installed):
- Uses `chromadb.PersistentClient` at `data/chroma_db/`.
- Collection: `"migration_patterns"`.
- Documents = SAS code strings; metadata includes `pyspark_code`, `category`, `source`.
- Vector embeddings computed automatically by ChromaDB.
- Similarity query: `collection.query(query_texts=[sas_code], n_results=n)`.
- Distance-to-similarity: `similarity = 1.0 - min(distance, 1.0)`.

**Fallback mode** (no ChromaDB):
- In-memory `dict[pattern_id → MigrationPattern]`.
- Jaccard similarity on tokenized SAS code.
- `intersection / union` of word sets.

```python
# Add a pattern
store.add_pattern(
    pattern_id="guide_example_1",
    sas_code="DATA emp; SET raw; salary = salary * 1.1; RUN;",
    pyspark_code="employee_df = raw_df.withColumn('salary', F.col('salary') * 1.1)",
    metadata={"source": "migration_guide", "category": "data_step"}
)

# Initialize from migration guide (extracts ```sas / ```python block pairs)
count = store.initialize_with_examples("SAS_to_pyspark_migration_guide.md")

# Find similar patterns
patterns = store.find_similar_patterns(sas_code, n_results=3, min_similarity=0.5)
```

Categories automatically detected during guide parsing: `proc_sql`, `proc`, `data_step`, `macro`, `general`.

### ExampleRetriever

```python
retriever = ExampleRetriever(pattern_store)
patterns = retriever.get_relevant_examples(chunk, max_examples=3, min_similarity=0.5)
```

**Category boost (1.2x):** Patterns whose category matches the chunk's content type (macro-heavy chunk → `macro` patterns scored higher) get their similarity score multiplied by 1.2 before ranking.

**`format_examples_for_prompt(patterns)`:**

```
SIMILAR EXAMPLES FROM MIGRATION GUIDE:

Example 1 (Similarity: 0.85):
SAS Code:
  DATA emp_filtered;
    SET employees;
    WHERE salary > 50000;
  RUN;
PySpark Equivalent:
  emp_filtered_df = employees_df.filter(F.col("salary") > 50000)
---
```

---

## 8. Backend API

**File:** `backend/app.py`

Flask server on **port 5002** with CORS enabled. Sessions stored in-memory dict with auto-cleanup thread (hourly, 24h expiry).

### All Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/health` | — | `{status, graph_modules_available, timestamp}` |
| POST | `/api/graph/analyze` | multipart: `file` (SAS), `format?` (react-flow/d3/json) | `{success, graph, chunks, summary, chunk_summary}` |
| GET | `/api/graph/analyze-session/<id>` | — | `{success, graph, chunks, summary}` |
| POST | `/api/graph-migrate/initialize` | JSON: `{model?, use_rag?}` | `{success, session_id, config}` |
| POST | `/api/graph-migrate/upload/<id>` | multipart: `file` | `{success, filename, size}` |
| POST | `/api/graph-migrate/start/<id>` | JSON: `{visualize?}` | SSE stream of events |
| GET | `/api/graph-migrate/status/<id>` | — | `{status, progress, current_phase}` |
| GET | `/api/graph-migrate/result/<id>` | — | `{success, pyspark_code, mapping, ...}` |
| GET | `/api/graph-migrate/download/<id>` | — | ZIP file with all outputs |

### Session Lifecycle

```
POST /initialize    → session_id created, temp_dir allocated
POST /upload/:id    → SAS file saved to session temp_dir
POST /start/:id     → migration starts (SSE stream for real-time updates)
GET  /status/:id    → poll migration progress
GET  /result/:id    → get full MigrationResult JSON
GET  /download/:id  → download ZIP with .py, _mapping.txt, _validation.txt
                      (session cleanup on download or after 24h)
```

**Auto-cleanup thread:**

```python
def periodic_cleanup():
    while True:
        time.sleep(3600)  # Every hour
        cleanup_old_sessions()

threading.Thread(target=periodic_cleanup, daemon=True).start()
```

Sessions older than `SESSION_TIMEOUT_HOURS = 24` have their temp dirs deleted.

---

## 9. Frontend

**Stack:** React + Vite, Tailwind CSS, Axios, React Flow

### 6-Step Wizard Flow

| Step | Component | Description |
|------|-----------|-------------|
| 1 | `WelcomePanel` | Overview + "Start Migration" CTA |
| 2 | `FileUpload` | Drag-and-drop `.sas` file upload |
| 3 | `GraphStats` + `DependencyGraph` | Visualize dependency graph using React Flow |
| 4 | `ChunkViewer` | View generated chunks with token estimates |
| 5 | `MigrationPipeline` | Real-time migration progress per chunk/layer |
| 6 | `ResultsPanel` | View and download PySpark output, mapping, validation report |

### `useGraphMigration` Hook

**File:** `frontend/src/hooks/useGraphMigration.js`

Central state manager for the entire wizard:

**State variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `sessionId` | string | Backend session UUID |
| `currentStep` | number | Wizard step (1–6) |
| `uploadedFile` | File | The SAS file |
| `graphData` | object | React Flow nodes/edges |
| `chunks` | array | Chunk list with metadata |
| `graphSummary` | object | `{total_nodes, total_edges, has_cycles, ...}` |
| `migrationStatus` | string | `'idle'|'running'|'complete'|'error'` |
| `migrationResult` | object | Full MigrationResult |
| `progress` | number | 0–100 percentage |
| `currentPhase` | string | Current migration phase name |
| `error` | string | Error message if any |

**Methods:**

| Method | Description |
|--------|-------------|
| `initializeSession(config)` | POST `/initialize`, store session_id |
| `uploadFile(file)` | POST `/upload/:id` with FormData |
| `analyzeGraph()` | POST `/graph/analyze`, populate graphData + chunks |
| `startMigration()` | POST `/start/:id`, subscribe to SSE events |
| `pollStatus()` | GET `/status/:id`, update progress |
| `getResult()` | GET `/result/:id`, populate migrationResult |
| `downloadResults()` | GET `/download/:id`, trigger ZIP download |
| `reset()` | Clear all state, return to step 1 |

### React Flow Graph Visualization

The dependency graph is rendered using React Flow. Node positions are calculated from **execution layers**:
- Layer 0 → `x = 0`
- Layer 1 → `x = 250`
- Each node within a layer is stacked vertically with `y` offset.

**Custom node types** by `NodeType`:
- `DATASET` → blue rectangle
- `DATA_STEP` → orange rounded rectangle
- `PROC` → purple rounded rectangle
- `MACRO` → green hexagon
- `MACRO_VARIABLE` → yellow diamond
- `LIBRARY` → gray cylinder
- `FILE_REF` → brown document icon

---

## 10. CLI Tools

**Files:** `cli/analyze.py`, `cli/migrate.py`, `cli/migrate_batch.py`, `cli/visualize.py`

All CLI tools use `argparse` and `rich` for formatted console output.

### `cli/analyze.py`

```bash
python -m graph_approach.cli.analyze input.sas [options]
```

| Flag | Description |
|------|-------------|
| `--format {text,json}` | Output format (default: text) |
| `--output PATH` | Save graph JSON to file |
| `--no-execution-order` | Skip execution order display |
| `--no-cycles` | Skip cycle detection display |

Output (text mode): rich table of nodes by type (with emoji), execution layers, cycle warnings.

### `cli/migrate.py`

```bash
python -m graph_approach.cli.migrate input.sas [options]
```

| Flag | Description |
|------|-------------|
| `-o, --output-dir PATH` | Output directory (required) |
| `--model {o3,gpt-4,gpt-4-turbo,gpt-3.5-turbo}` | LLM model (default: gpt-4) |
| `--no-rag` | Disable RAG examples |
| `--visualize` | Generate graph visualization |
| `--max-concurrent INT` | Max parallel LLM calls (default: 5) |

Artifacts saved: `{stem}.py`, `{stem}_mapping.txt`, `{stem}_validation.txt`, `{stem}_result.json`.

### `cli/migrate_batch.py`

```bash
python -m graph_approach.cli.migrate_batch input_dir/ [options]
```

| Flag | Description |
|------|-------------|
| `-o, --output-dir PATH` | Output directory (required) |
| `--max-workers INT` | Parallel file workers (default: 4) |
| `--pattern GLOB` | File pattern (default: `*.sas`) |
| `--recursive` | Search subdirectories |
| `--no-continue-on-error` | Stop on first failure |
| `--model STR` | LLM model |

Generates `batch_summary.md` in output directory.

### `cli/visualize.py`

```bash
python -m graph_approach.cli.visualize input.sas [options]
```

| Flag | Description |
|------|-------------|
| `-o, --output PATH` | Output file path (required) |
| `--format {png,svg,pdf,dot}` | Output format (default: png) |
| `--show-source` | Include source code in node tooltips |
| `--layers` | Render as layered subgraph layout |

---

## 11. Visualization & Reporting

**Files:** `visualization/graph_renderer.py`, `visualization/report_generator.py`

### GraphRenderer

```python
renderer = GraphRenderer(graph)
renderer.render_to_file("output.png", format="png")
renderer.render_to_dot("output.dot")
```

Uses Graphviz (`graphviz` Python package). Node styling:

| NodeType | Color | Shape |
|----------|-------|-------|
| `DATASET` | lightblue | rectangle |
| `DATA_STEP` | orange | rounded rectangle |
| `PROC` | mediumpurple | rounded rectangle |
| `MACRO` | lightgreen | hexagon |
| `MACRO_VARIABLE` | yellow | diamond |
| `LIBRARY` | lightgray | cylinder |
| `FILE_REF` | sandybrown | note |

Edge styling by `EdgeType`: solid for data flow (`READS_FROM`, `WRITES_TO`, `PROC_INPUT`, `PROC_OUTPUT`), dashed for control flow (`CALLS`, `USES_VARIABLE`, `DEFINES_VARIABLE`).

Execution layers rendered as Graphviz **subgraphs** with horizontal rank grouping. Auto-generated legend in bottom-left corner.

Formats supported: `png`, `svg`, `pdf`, `dot` (raw Graphviz source).

### ReportGenerator

Produces Markdown or HTML migration reports:

```python
reporter = ReportGenerator()
report = reporter.generate_migration_report(result, graph_summary)
batch_report = reporter.generate_summary_report(batch_result)  # for batch
```

Report sections:
- Graph statistics (node counts by type, edge counts, cycles)
- Execution order summary
- Chunk breakdown table (chunk ID, nodes, estimated tokens, layer, status)
- Conversion results per chunk (success/failure, errors, warnings)
- Timing information
- Fixes applied

---

## 12. Package Generator

**File:** `core/package_generator.py`

Generates a deployable Python package from the migration output:

```python
generator = PackageGenerator(output_dir="./output", package_name="my_pipeline")
generator.generate(migration_result)
```

**Generated files:**

| File | Content |
|------|---------|
| `setup.py` | Package metadata, `install_requires=['pyspark>=3.0']` |
| `requirements.txt` | Pinned dependencies |
| `__init__.py` | Package root with version |
| `README.md` | Auto-generated usage instructions |
| `.gitignore` | Python/PySpark standard ignores |

---

## 13. Testing

**Directory:** `tests/`

| File | Coverage |
|------|---------|
| `test_dependency_graph.py` | `DependencyGraph` CRUD, topological sort, cycle detection, `break_cycles()`, subgraph extraction, serialization |
| `test_graph_builder.py` | `GraphBuilder.from_file()`, node/edge counts for known SAS samples, `get_execution_order()` |
| `test_cast_chunker.py` | `CASTChunker.chunk_code()` size limits, context headers, `_merge_tiny_trailing()`, single-node splitting |
| `test_validation.py` | `VariableTracker.analyze_code()`, undefined variables, use-after-delete, `suggest_fixes()` |

**Running tests:**

```bash
# All tests
pytest tests/ -v

# Single file
pytest tests/test_dependency_graph.py -v

# With coverage
pytest tests/ --cov=graph_approach --cov-report=html
# Report at: htmlcov/index.html
```

---

## 14. Configuration & Deployment

### Environment Variables (`.env`)

Create at project root (same directory as this file):

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=gpt-4
```

Loaded via `python-dotenv` in `GraphMigrator.__init__()`.

### `requirements.txt` Key Dependencies

```
networkx          # Graph algorithms
openai            # Azure OpenAI client
python-dotenv     # .env loading
flask             # Backend API
flask-cors        # CORS headers
chromadb          # Vector DB for RAG (optional)
graphviz          # Graph visualization
rich              # CLI formatting
```

### Backend Startup

```bash
cd backend
./run.sh        # Sets env, starts Flask on port 5002
# Or manually:
python app.py
```

`run.sh` exports env vars and calls `flask run --port 5002`.

### Frontend Startup

```bash
cd frontend
npm install        # First time
npm run dev        # Dev server on port 3000 (hot reload)
npm run build      # Production build → dist/
npm run preview    # Preview production build
```

The frontend proxies API calls to `http://localhost:5002` (configured in `vite.config.js`).

### Python Path Setup

The project root IS the `graph_approach` package. When running CLI tools or importing programmatically:

```python
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.migration.graph_migrator import GraphMigrator
```

All CLI tools do this automatically at the top of each file.

---

## 15. End-to-End Flow Walkthrough

### Scenario: User uploads `employee_analysis.sas`

**Step 1: Session initialization (Frontend → Backend)**

```
User clicks "Start Migration"
  → POST /api/graph-migrate/initialize {model: "gpt-4", use_rag: true}
  ← {session_id: "uuid-abc123", config: {...}}
```

**Step 2: File upload**

```
User drags SAS file
  → POST /api/graph-migrate/upload/uuid-abc123 (multipart: file)
  ← {success: true, filename: "employee_analysis.sas"}
File saved to: /tmp/graph_migration_uuid-abc123_<hash>/employee_analysis.sas
```

**Step 3: Graph analysis**

```
Frontend requests graph visualization
  → POST /api/graph/analyze (file: employee_analysis.sas, format: react-flow)

Backend:
  GraphBuilder.from_file() → SASParser.parse_content() → DependencyExtractor.extract_all_dependencies()
  graph.add_node(LIBRARY: mylib), add_node(MACRO: calc_bonus), ...
  graph.add_edge(employee_data → data_step_5, READS_FROM)
  ChunkOptimizer.generate_chunks() → 8 chunks in 4 layers

  ← {graph: {nodes: [...], edges: [...]}, chunks: [...], summary: {...}}

Frontend: React Flow renders graph with execution layers as columns
```

**Step 4: Migration starts**

```
User clicks "Migrate"
  → POST /api/graph-migrate/start/uuid-abc123

Backend asyncio.run(_convert_chunks_parallel()):

  Layer 0 (3 chunks, parallel):
    chunk_001 (MACRO: calc_bonus)    ─┐
    chunk_002 (LIBRARY + FILE_REF)   ─┼─ asyncio.gather → 3 concurrent LLM calls
    chunk_003 (MACRO_VARIABLE group) ─┘
    → execution_context.map_variable_name("employee_data", "employee_df")

  Layer 1 (2 chunks, parallel):
    chunk_004 (DATA_STEP: load_employees, ~2800 tokens → cAST split into 2)
      → cast_chunk 4a (lines 1-45): "DATA employee_data; SET raw_emp; ..."
      → cast_chunk 4b (lines 46-89): "/* transformation logic */"
      [Sequential within group, parallel with chunk_005]
    chunk_005 (PROC IMPORT → raw_emp)

  Layer 2 (2 chunks):
    chunk_006 (PROC MEANS: summary stats)
    chunk_007 (DATA_STEP: filter + merge)

  Layer 3 (1 chunk):
    chunk_008 (PROC PRINT: final report)
```

**Step 5: Reconciliation**

```
CodeReconciler.reconcile_chunks_with_report(converted_chunks, execution_context):

  Step 0: Reassemble cAST sub-chunks:
    4a + 4b → chunk_004_reassembled (dedup imports)
    "Reassembled 2 cAST sub-chunks into parent chunks"

  Step 2: Dedup imports:
    8 chunks had "from pyspark.sql import functions as F"
    → 1 unique import line

  Step 3: Variable mapping:
    "employee_data" → "employee_df" (from execution_context)

  Steps 6-7: Remove duplicate `employee_df = ...` from chunk_004_reassembled, reorder

  Step 10: LLM cleanup (code is 180 lines → single call)
    → final clean PySpark script

ValidationReport:
  Total Issues: 4
    Errors: 0
    Warnings: 2 (duplicate definition of dept_summary_df at lines 45, 87)
    Info: 2 (unused variable temp_counts)
```

**Step 6: Results available**

```
Frontend polls GET /api/graph-migrate/status/uuid-abc123
  ← {status: "complete", progress: 100}

Frontend fetches GET /api/graph-migrate/result/uuid-abc123
  ← {success: true, pyspark_code: "...", chunks_converted: 8, ...}

User downloads → GET /api/graph-migrate/download/uuid-abc123
  ← employee_analysis_output.zip containing:
      employee_analysis.py
      employee_analysis_mapping.txt
      employee_analysis_validation.txt
      employee_analysis_result.json
```

### Data Flow Diagram

```
employee_analysis.sas
        │
        │  (text)
        ▼
  SASParser          ──────────────────────────────────────────────┐
  (regex-based)                                                     │
        │  parsed_sas: {data_steps, proc_steps, macros}            │
        ▼                                                           │
  DependencyExtractor                                               │
  (DataStepDeps, ProcDeps, MacroDeps)                              │
        │                                                           │
        ▼                                                           │
  GraphBuilder                                                      │
  (DependencyGraph: 24 nodes, 31 edges)                            │
        │                                                           │
        ├──────────────────────────────────────┐                   │
        │ (topological sort)                   │ (to_react_flow)   │
        ▼                                      ▼                   │
  ChunkOptimizer                         GraphExporter            │
  (8 chunks, 4 layers)                   (→ Frontend)             │
        │                                                           │
        │ (large nodes)                                             │
        ▼                                                           │
  CASTChunker                                                       │
  (splits chunk_004 → 2 sub-chunks)                                │
        │                                                           │
        │ (per chunk, async)                                        │
        ▼                                                           │
  ContextEnricher ←── ExecutionContext ←── SchemaInferencer        │
  (EnrichedContext     (variable_name_map,    (type inference)     │
   + LLM prompt)       schemas)                                    │
        │                                                           │
        ▼                                                           │
  Azure OpenAI                                                      │
  (async, 5 concurrent)                                            │
        │  {pyspark_code, mapping, variables_created}              │
        ▼                                                           │
  CodeReconciler                                                    │
  (reassemble → dedup → remap → reorder → LLM cleanup)            │
        │                                                           │
        ▼                                                           │
  ExecutionOrderOptimizer                                           │
  (final topological sort of code blocks)                          │
        │                                                           │
        ▼                                                           │
  employee_analysis.py ─────────────────────────────────────────────┘
  (production PySpark)
```

---

*Generated 2026-02-19. Source: SAS Accelerator project at `/Users/ameya/Documents/Projects/SAS Accelerator`.*
