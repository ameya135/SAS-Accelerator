"""
Execution Order Optimizer

Analyzes PySpark code to determine optimal execution order based on
variable dependencies. Uses topological sorting to ensure variables
are defined before they are used.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class BlockType(Enum):
    """Type of code block"""
    IMPORT = "import"
    SPARK_INIT = "spark_init"
    MACRO_VAR = "macro_var"
    DATA_LOAD = "data_load"
    TRANSFORM = "transform"
    AGGREGATION = "aggregation"
    OUTPUT = "output"
    COMMENT = "comment"
    OTHER = "other"


@dataclass
class ExecutionBlock:
    """A block of code with execution metadata"""
    block_id: str
    code: str
    block_type: BlockType
    line_start: int
    line_end: int
    defines: Set[str] = field(default_factory=set)      # Variables defined
    uses: Set[str] = field(default_factory=set)         # Variables used
    dependencies: Set[str] = field(default_factory=set) # Block IDs this depends on
    
    def __hash__(self):
        return hash(self.block_id)
    
    def __eq__(self, other):
        if isinstance(other, ExecutionBlock):
            return self.block_id == other.block_id
        return False


@dataclass
class DependencyIssue:
    """Records a dependency issue"""
    issue_type: str  # 'circular', 'missing', 'order'
    description: str
    blocks_involved: List[str]
    suggested_fix: str = ""


@dataclass
class ExecutionOrderResult:
    """Result of execution order analysis"""
    ordered_blocks: List[ExecutionBlock]
    issues: List[DependencyIssue]
    reordered: bool
    original_order: List[str]
    new_order: List[str]


class ExecutionOrderOptimizer:
    """
    Optimize execution order of PySpark code blocks
    
    Ensures:
    - Variables are defined before use
    - Proper dependency chain
    - Handles circular dependencies gracefully
    """
    
    def __init__(self):
        """Initialize optimizer"""
        self.blocks: List[ExecutionBlock] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.issues: List[DependencyIssue] = []
        
        # Patterns for code analysis
        self.patterns = {
            'import': re.compile(r'^(?:from\s+\S+\s+)?import\s+', re.MULTILINE),
            'spark_init': re.compile(r'SparkSession\.builder', re.MULTILINE),
            'df_assignment': re.compile(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*', re.MULTILINE),
            'df_method': re.compile(r'\.(?:select|filter|join|groupBy|agg|withColumn|orderBy|union)', re.MULTILINE),
            'df_read': re.compile(r'spark\.(?:read|table|createDataFrame)', re.MULTILINE),
            'df_write': re.compile(r'\.(?:write|save|show|collect|toPandas)', re.MULTILINE),
            'comment_block': re.compile(r'^\s*#', re.MULTILINE),
        }
        
        # Known system variables and keywords to ignore
        self.system_vars = {
            # PySpark
            'spark', 'F', 'T', 'Window', 'Row', 'SparkSession',
            'StructType', 'StructField', 'StringType', 'IntegerType',
            'DoubleType', 'DateType', 'TimestampType', 'BooleanType',
            'ArrayType', 'MapType', 'DataFrame', 'Column',
            # Python builtins
            'datetime', 'date', 'time', 'print', 'len', 'str', 'int', 'float',
            'list', 'dict', 'set', 'tuple', 'range', 'True', 'False', 'None',
            'abs', 'min', 'max', 'sum', 'round', 'sorted', 'enumerate', 'zip',
            # Keywords
            'if', 'else', 'elif', 'for', 'while', 'in', 'and', 'or', 'not',
            'return', 'def', 'class', 'import', 'from', 'as', 'with',
            'try', 'except', 'finally', 'raise', 'pass', 'break', 'continue',
            'lambda', 'yield', 'global', 'nonlocal', 'assert', 'del', 'is',
            # Common words that appear in comments
            'This', 'The', 'A', 'An', 'It', 'uses', 'creates', 'before', 'after',
            'defined', 'used', 'data', 'code', 'step', 'block', 'function',
            # Module names
            'pyspark', 'sql', 'functions', 'types', 're', 'os', 'sys', 'json',
            # PySpark functions
            'col', 'lit', 'when', 'otherwise', 'agg', 'count', 'mean', 'avg',
            'first', 'last', 'floor', 'ceil', 'sqrt', 'log', 'exp', 'pow',
            'coalesce', 'concat', 'substring', 'trim', 'lower', 'upper',
            'to_date', 'to_timestamp', 'date_format', 'current_date', 'current_timestamp',
            'read', 'write', 'parquet', 'csv', 'json', 'table', 'builder', 'getOrCreate',
            'select', 'filter', 'where', 'groupBy', 'orderBy', 'join', 'union',
            'withColumn', 'drop', 'alias', 'show', 'collect', 'cache', 'persist'
        }
    
    def analyze_and_optimize(self, code: str) -> ExecutionOrderResult:
        """
        Analyze code and return optimized execution order
        
        Args:
            code: PySpark code to analyze
            
        Returns:
            ExecutionOrderResult with optimized block order
        """
        self.blocks = []
        self.dependency_graph = {}
        self.issues = []
        
        # Step 1: Parse code into blocks
        self._parse_code_blocks(code)
        
        # Step 2: Analyze dependencies
        self._analyze_dependencies()
        
        # Step 3: Build dependency graph
        self._build_dependency_graph()
        
        # Step 4: Detect issues (circular deps, missing vars)
        self._detect_issues()
        
        # Step 5: Topologically sort blocks
        original_order = [b.block_id for b in self.blocks]
        ordered_blocks = self._topological_sort()
        new_order = [b.block_id for b in ordered_blocks]
        
        reordered = original_order != new_order
        
        return ExecutionOrderResult(
            ordered_blocks=ordered_blocks,
            issues=self.issues,
            reordered=reordered,
            original_order=original_order,
            new_order=new_order
        )
    
    def optimize_code(self, code: str) -> Tuple[str, List[str]]:
        """
        Optimize code and return reordered code string
        
        Args:
            code: PySpark code to optimize
            
        Returns:
            Tuple of (optimized_code, list_of_changes)
        """
        result = self.analyze_and_optimize(code)
        
        if not result.reordered:
            return code, ["No reordering needed - code is already in optimal order"]
        
        # Reassemble code from ordered blocks
        changes = []
        
        # Keep imports at top
        import_blocks = [b for b in result.ordered_blocks if b.block_type == BlockType.IMPORT]
        spark_init_blocks = [b for b in result.ordered_blocks if b.block_type == BlockType.SPARK_INIT]
        macro_var_blocks = [b for b in result.ordered_blocks if b.block_type == BlockType.MACRO_VAR]
        other_blocks = [b for b in result.ordered_blocks 
                       if b.block_type not in [BlockType.IMPORT, BlockType.SPARK_INIT, BlockType.MACRO_VAR]]
        
        parts = []
        
        # Header
        parts.append("# Generated PySpark code from SAS migration")
        parts.append("# Execution order optimized by ExecutionOrderOptimizer")
        parts.append("")
        
        # Imports
        for block in import_blocks:
            parts.append(block.code)
        if import_blocks:
            parts.append("")
        
        # Spark init
        for block in spark_init_blocks:
            parts.append(block.code)
        if spark_init_blocks:
            parts.append("")
        
        # Macro variables
        for block in macro_var_blocks:
            parts.append(block.code)
        if macro_var_blocks:
            parts.append("")
        
        # Other blocks in optimized order
        for block in other_blocks:
            parts.append(block.code)
            parts.append("")
        
        changes.append(f"Reordered {len(self.blocks)} code blocks for optimal execution")
        
        if result.issues:
            for issue in result.issues:
                changes.append(f"Warning: {issue.description}")
        
        return '\n'.join(parts), changes
    
    def _parse_code_blocks(self, code: str) -> None:
        """Parse code into logical blocks"""
        lines = code.split('\n')
        current_block_lines = []
        current_block_start = 0
        block_counter = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for block boundaries
            is_boundary = (
                not stripped or  # Empty line
                stripped.startswith('#') and not current_block_lines or  # Comment at start
                self._is_new_statement_start(stripped, current_block_lines)
            )
            
            if is_boundary and current_block_lines:
                # Save current block
                block_code = '\n'.join(current_block_lines)
                if block_code.strip():
                    block = ExecutionBlock(
                        block_id=f"block_{block_counter}",
                        code=block_code,
                        block_type=self._classify_block(block_code),
                        line_start=current_block_start + 1,
                        line_end=i
                    )
                    self.blocks.append(block)
                    block_counter += 1
                
                current_block_lines = []
                current_block_start = i
            
            if stripped:
                current_block_lines.append(line)
            
            i += 1
        
        # Don't forget the last block
        if current_block_lines:
            block_code = '\n'.join(current_block_lines)
            if block_code.strip():
                block = ExecutionBlock(
                    block_id=f"block_{block_counter}",
                    code=block_code,
                    block_type=self._classify_block(block_code),
                    line_start=current_block_start + 1,
                    line_end=len(lines)
                )
                self.blocks.append(block)
    
    def _is_new_statement_start(self, line: str, current_lines: List[str]) -> bool:
        """Check if line starts a new logical statement"""
        if not current_lines:
            return False
        
        # New assignment at start of line (not continuation)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*', line):
            # Check if previous lines look complete
            last_line = current_lines[-1].strip()
            if not last_line.endswith(('\\', ',', '(', '[', '{')):
                return True
        
        # New function def
        if line.startswith('def ') or line.startswith('class '):
            return True
        
        return False
    
    def _classify_block(self, code: str) -> BlockType:
        """Classify the type of code block"""
        stripped = code.strip()
        
        if self.patterns['import'].search(code):
            return BlockType.IMPORT
        
        if self.patterns['spark_init'].search(code):
            return BlockType.SPARK_INIT
        
        if stripped.startswith('#'):
            return BlockType.COMMENT
        
        # Check for macro variable initialization patterns
        macro_patterns = [
            r'^\s*unemployment_shock\s*=',
            r'^\s*gdp_decline\s*=',
            r'^\s*interest_rate_shock\s*=',
            r'^\s*report_date\s*=',
            r'# SAS Macro Variables'
        ]
        for pattern in macro_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return BlockType.MACRO_VAR
        
        if self.patterns['df_read'].search(code):
            return BlockType.DATA_LOAD
        
        if self.patterns['df_write'].search(code):
            return BlockType.OUTPUT
        
        if self.patterns['df_method'].search(code):
            # Check if it's aggregation
            if re.search(r'\.(?:groupBy|agg|count|sum|mean|avg)', code):
                return BlockType.AGGREGATION
            return BlockType.TRANSFORM
        
        return BlockType.OTHER
    
    def _analyze_dependencies(self) -> None:
        """Analyze variable definitions and usages for each block"""
        for block in self.blocks:
            # Find definitions (var = ...)
            def_pattern = r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]'
            for match in re.finditer(def_pattern, block.code, re.MULTILINE):
                var_name = match.group(2)
                if var_name not in self.system_vars:
                    block.defines.add(var_name)
            
            # Find usages (variable references that aren't definitions)
            # This is simplified - looks for word patterns
            words = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', block.code))
            for word in words:
                if (word not in self.system_vars and 
                    word not in block.defines and
                    not word.startswith('_')):
                    # Check if it's likely a variable reference
                    if re.search(rf'\b{word}\s*\.', block.code) or \
                       re.search(rf'[=,(\s]{word}[,)\s]', block.code):
                        block.uses.add(word)
    
    def _build_dependency_graph(self) -> None:
        """Build dependency graph between blocks"""
        # Map variable -> block that defines it
        var_to_block: Dict[str, str] = {}
        
        for block in self.blocks:
            for var in block.defines:
                if var not in var_to_block:
                    var_to_block[var] = block.block_id
        
        # Build dependencies
        self.dependency_graph = {block.block_id: set() for block in self.blocks}
        
        for block in self.blocks:
            for var in block.uses:
                if var in var_to_block:
                    defining_block = var_to_block[var]
                    if defining_block != block.block_id:
                        block.dependencies.add(defining_block)
                        self.dependency_graph[block.block_id].add(defining_block)
    
    def _detect_issues(self) -> None:
        """Detect dependency issues"""
        # Check for circular dependencies
        cycles = self._find_cycles()
        for cycle in cycles:
            self.issues.append(DependencyIssue(
                issue_type='circular',
                description=f"Circular dependency detected: {' -> '.join(cycle)}",
                blocks_involved=cycle,
                suggested_fix="Review and break the circular dependency by redefining variables"
            ))
        
        # Check for undefined variables
        all_defined = set()
        for block in self.blocks:
            all_defined.update(block.defines)
        
        for block in self.blocks:
            undefined = block.uses - all_defined - self.system_vars
            if undefined:
                self.issues.append(DependencyIssue(
                    issue_type='missing',
                    description=f"Block {block.block_id} uses undefined variables: {undefined}",
                    blocks_involved=[block.block_id],
                    suggested_fix=f"Define or initialize: {', '.join(undefined)}"
                ))
    
    def _find_cycles(self) -> List[List[str]]:
        """Find cycles in dependency graph using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _topological_sort(self) -> List[ExecutionBlock]:
        """Topologically sort blocks based on dependencies"""
        # Create a copy of the graph
        in_degree = {block.block_id: 0 for block in self.blocks}
        graph = {block.block_id: set() for block in self.blocks}
        
        for block in self.blocks:
            for dep in block.dependencies:
                if dep in graph:
                    graph[dep].add(block.block_id)
                    in_degree[block.block_id] += 1
        
        # Kahn's algorithm
        queue = [block_id for block_id, degree in in_degree.items() if degree == 0]
        result_order = []
        
        while queue:
            # Sort queue to maintain stable order when possible
            queue.sort()
            node = queue.pop(0)
            result_order.append(node)
            
            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If not all nodes are in result, there's a cycle
        if len(result_order) != len(self.blocks):
            # Fall back to original order with cycle warning
            self.issues.append(DependencyIssue(
                issue_type='circular',
                description="Could not fully resolve dependencies due to cycles",
                blocks_involved=[b.block_id for b in self.blocks if b.block_id not in result_order],
                suggested_fix="Manual intervention required to break cycles"
            ))
            # Add remaining blocks at the end
            remaining = [b.block_id for b in self.blocks if b.block_id not in result_order]
            result_order.extend(remaining)
        
        # Map back to blocks
        block_map = {b.block_id: b for b in self.blocks}
        return [block_map[block_id] for block_id in result_order]
    
    def generate_report(self) -> str:
        """Generate a report of the execution order analysis"""
        lines = []
        lines.append("=" * 60)
        lines.append("EXECUTION ORDER ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"Total Blocks: {len(self.blocks)}")
        lines.append("")
        
        # Block summary
        lines.append("BLOCK SUMMARY:")
        lines.append("-" * 40)
        for block in self.blocks:
            lines.append(f"  {block.block_id} ({block.block_type.value})")
            lines.append(f"    Lines: {block.line_start}-{block.line_end}")
            if block.defines:
                lines.append(f"    Defines: {', '.join(block.defines)}")
            if block.uses:
                lines.append(f"    Uses: {', '.join(block.uses)}")
            if block.dependencies:
                lines.append(f"    Depends on: {', '.join(block.dependencies)}")
        lines.append("")
        
        # Issues
        if self.issues:
            lines.append("ISSUES DETECTED:")
            lines.append("-" * 40)
            for issue in self.issues:
                lines.append(f"  [{issue.issue_type.upper()}] {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"    Fix: {issue.suggested_fix}")
        else:
            lines.append("No issues detected.")
        
        lines.append("")
        lines.append("=" * 60)
        
        return '\n'.join(lines)

