"""
Semantic Analyzer

Performs semantic analysis on the SAS AST including:
- Variable scope tracking
- Type inference  
- Macro variable resolution
- Dependency analysis
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from graph_approach.ast.sas_ast import (
    ASTNode, ProgramNode, DataStepNode, ProcNode, MacroNode,
    AssignmentNode, ExpressionNode, VariableNode, LiteralNode,
    MacroVarRefNode, SetStatementNode, MergeStatementNode,
    IfStatementNode, DoLoopNode, FunctionCallNode, NodeType
)


class DataType(Enum):
    """SAS data types"""
    NUMERIC = auto()
    CHARACTER = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    UNKNOWN = auto()


class SymbolKind(Enum):
    """Types of symbols"""
    VARIABLE = auto()          # Regular variable
    DATASET = auto()           # Dataset name
    MACRO_VAR = auto()         # Macro variable
    MACRO = auto()             # Macro definition
    LIBRARY = auto()           # Library reference
    FILEREF = auto()           # File reference
    FORMAT = auto()            # Format
    INFORMAT = auto()          # Informat
    ARRAY = auto()             # Array


@dataclass
class Symbol:
    """Represents a symbol in the symbol table"""
    name: str
    kind: SymbolKind
    data_type: DataType = DataType.UNKNOWN
    scope: str = "global"       # Scope name (global, data_step_name, macro_name)
    line_defined: int = 0
    line_last_used: int = 0
    is_initialized: bool = False
    length: Optional[int] = None  # For character variables
    format: Optional[str] = None
    informat: Optional[str] = None
    label: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.name, self.kind, self.scope))


@dataclass 
class SymbolTable:
    """
    Symbol table for tracking variables and their properties
    
    Supports nested scopes for macro definitions and data steps.
    """
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    parent: Optional['SymbolTable'] = None
    scope_name: str = "global"
    
    def define(self, symbol: Symbol) -> None:
        """Define a new symbol in the current scope"""
        key = f"{symbol.name.lower()}:{symbol.kind.name}"
        symbol.scope = self.scope_name
        self.symbols[key] = symbol
    
    def lookup(self, name: str, kind: SymbolKind) -> Optional[Symbol]:
        """Look up a symbol, searching parent scopes if needed"""
        key = f"{name.lower()}:{kind.name}"
        
        if key in self.symbols:
            return self.symbols[key]
        
        if self.parent:
            return self.parent.lookup(name, kind)
        
        return None
    
    def lookup_variable(self, name: str) -> Optional[Symbol]:
        """Convenience method to look up a variable"""
        return self.lookup(name, SymbolKind.VARIABLE)
    
    def lookup_dataset(self, name: str) -> Optional[Symbol]:
        """Convenience method to look up a dataset"""
        return self.lookup(name, SymbolKind.DATASET)
    
    def lookup_macro_var(self, name: str) -> Optional[Symbol]:
        """Convenience method to look up a macro variable"""
        return self.lookup(name, SymbolKind.MACRO_VAR)
    
    def get_all_symbols(self, kind: Optional[SymbolKind] = None) -> List[Symbol]:
        """Get all symbols, optionally filtered by kind"""
        symbols = list(self.symbols.values())
        if kind:
            symbols = [s for s in symbols if s.kind == kind]
        return symbols
    
    def create_child_scope(self, name: str) -> 'SymbolTable':
        """Create a new child scope"""
        return SymbolTable(parent=self, scope_name=name)
    
    def merge_from_child(self, child: 'SymbolTable') -> None:
        """Merge symbols from a child scope (for macro variables)"""
        for symbol in child.symbols.values():
            if symbol.kind == SymbolKind.MACRO_VAR:
                # Macro variables bubble up to parent scope
                self.define(symbol)


@dataclass
class SemanticError:
    """Represents a semantic error"""
    message: str
    line: int
    severity: str = "error"  # error, warning, info
    node: Optional[ASTNode] = None


@dataclass
class DependencyInfo:
    """Information about dependencies"""
    datasets_read: Set[str] = field(default_factory=set)
    datasets_written: Set[str] = field(default_factory=set)
    macro_vars_used: Set[str] = field(default_factory=set)
    macro_vars_defined: Set[str] = field(default_factory=set)
    macros_called: Set[str] = field(default_factory=set)
    libraries_used: Set[str] = field(default_factory=set)


class SemanticAnalyzer:
    """
    Performs semantic analysis on SAS AST
    
    Responsibilities:
    - Build and manage symbol tables
    - Track variable scopes and lifetimes
    - Infer variable types
    - Resolve macro variables
    - Build dependency information
    - Detect semantic errors
    """
    
    def __init__(self):
        """Initialize the semantic analyzer"""
        self.global_scope = SymbolTable(scope_name="global")
        self.current_scope = self.global_scope
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticError] = []
        self.dependencies = DependencyInfo()
        
        # Initialize with known SAS system macro variables
        self._init_system_symbols()
    
    def _init_system_symbols(self) -> None:
        """Initialize known SAS system symbols"""
        # System macro variables
        system_macro_vars = [
            'sysdate', 'sysdate9', 'systime', 'sysday', 'syslast',
            'sysrc', 'sqlobs', 'sqlrc', 'syserr', 'sysmsg',
            'sysver', 'sysscp', 'sysscpl', 'sysuserid'
        ]
        
        for var in system_macro_vars:
            self.global_scope.define(Symbol(
                name=var,
                kind=SymbolKind.MACRO_VAR,
                is_initialized=True,
                attributes={'system': True}
            ))
    
    def analyze(self, program: ProgramNode) -> Tuple[SymbolTable, List[SemanticError], DependencyInfo]:
        """
        Perform semantic analysis on the AST
        
        Args:
            program: The program AST node
            
        Returns:
            Tuple of (symbol_table, errors, dependencies)
        """
        self.errors = []
        self.warnings = []
        self.dependencies = DependencyInfo()
        
        # First pass: collect macro definitions
        for macro in program.macros:
            self._analyze_macro_definition(macro)
        
        # Second pass: analyze global statements
        for stmt in program.global_statements:
            self._analyze_global_statement(stmt)
        
        # Third pass: analyze data steps and procs
        for data_step in program.data_steps:
            self._analyze_data_step(data_step)
        
        for proc in program.proc_steps:
            self._analyze_proc_step(proc)
        
        return self.global_scope, self.errors + self.warnings, self.dependencies
    
    def _analyze_macro_definition(self, macro: MacroNode) -> None:
        """Analyze a macro definition"""
        # Define the macro in global scope
        self.global_scope.define(Symbol(
            name=macro.name,
            kind=SymbolKind.MACRO,
            line_defined=macro.line_start
        ))
        
        # Create child scope for macro body
        macro_scope = self.current_scope.create_child_scope(f"macro_{macro.name}")
        old_scope = self.current_scope
        self.current_scope = macro_scope
        
        # Define parameters as local variables
        for param in macro.parameters:
            self.current_scope.define(Symbol(
                name=param,
                kind=SymbolKind.MACRO_VAR,
                line_defined=macro.line_start,
                is_initialized=True,  # Parameters are initialized by caller
                attributes={'is_parameter': True}
            ))
        
        # Analyze macro body (nested constructs)
        for node in macro.body:
            if isinstance(node, DataStepNode):
                self._analyze_data_step(node)
            elif isinstance(node, ProcNode):
                self._analyze_proc_step(node)
        
        # Restore scope
        self.current_scope = old_scope
        
        # Merge local macro variables to parent
        self.current_scope.merge_from_child(macro_scope)
    
    def _analyze_global_statement(self, stmt: ASTNode) -> None:
        """Analyze a global statement"""
        if stmt.node_type == NodeType.LIBNAME:
            libref = stmt.metadata.get('libref', '')
            if libref:
                self.global_scope.define(Symbol(
                    name=libref,
                    kind=SymbolKind.LIBRARY,
                    line_defined=stmt.line_start,
                    attributes={'path': stmt.metadata.get('path', '')}
                ))
                self.dependencies.libraries_used.add(libref)
        
        elif stmt.node_type == NodeType.ASSIGNMENT:
            # %LET statement
            if stmt.metadata.get('is_macro_var'):
                self.global_scope.define(Symbol(
                    name=stmt.target,
                    kind=SymbolKind.MACRO_VAR,
                    line_defined=stmt.line_start,
                    is_initialized=True,
                    attributes={'value': stmt.metadata.get('value', '')}
                ))
                self.dependencies.macro_vars_defined.add(stmt.target)
    
    def _analyze_data_step(self, data_step: DataStepNode) -> None:
        """Analyze a DATA step"""
        # Create scope for data step
        scope_name = f"data_{data_step.output_datasets[0] if data_step.output_datasets else 'unnamed'}"
        data_scope = self.current_scope.create_child_scope(scope_name)
        old_scope = self.current_scope
        self.current_scope = data_scope
        
        # Register output datasets
        for ds in data_step.output_datasets:
            ds_name = self._normalize_dataset_name(ds)
            self.global_scope.define(Symbol(
                name=ds_name,
                kind=SymbolKind.DATASET,
                line_defined=data_step.line_start
            ))
            self.dependencies.datasets_written.add(ds_name)
        
        # Analyze statements
        for stmt in data_step.statements:
            self._analyze_data_step_statement(stmt)
        
        # Check for undefined variables used
        self._check_undefined_variables(data_step)
        
        # Restore scope
        self.current_scope = old_scope
    
    def _analyze_data_step_statement(self, stmt: ASTNode) -> None:
        """Analyze a statement within a DATA step"""
        if isinstance(stmt, SetStatementNode):
            for ds in stmt.datasets:
                ds_name = self._normalize_dataset_name(ds)
                self.dependencies.datasets_read.add(ds_name)
                
                # Check if dataset exists
                if not self.global_scope.lookup_dataset(ds_name):
                    self.warnings.append(SemanticError(
                        message=f"Dataset '{ds}' may not exist",
                        line=stmt.line_start,
                        severity="warning",
                        node=stmt
                    ))
        
        elif isinstance(stmt, MergeStatementNode):
            for ds in stmt.datasets:
                ds_name = self._normalize_dataset_name(ds)
                self.dependencies.datasets_read.add(ds_name)
        
        elif isinstance(stmt, AssignmentNode):
            # Define the variable
            self.current_scope.define(Symbol(
                name=stmt.target,
                kind=SymbolKind.VARIABLE,
                line_defined=stmt.line_start,
                is_initialized=True
            ))
            
            # Analyze expression for variable usage
            if stmt.expression:
                self._analyze_expression(stmt.expression)
        
        elif isinstance(stmt, IfStatementNode):
            if stmt.condition:
                self._analyze_expression(stmt.condition)
            
            for s in stmt.then_branch:
                self._analyze_data_step_statement(s)
            
            for s in stmt.else_branch:
                self._analyze_data_step_statement(s)
        
        elif isinstance(stmt, DoLoopNode):
            # Define loop variable
            if stmt.loop_var:
                self.current_scope.define(Symbol(
                    name=stmt.loop_var,
                    kind=SymbolKind.VARIABLE,
                    line_defined=stmt.line_start,
                    is_initialized=True,
                    data_type=DataType.NUMERIC
                ))
            
            for s in stmt.body:
                self._analyze_data_step_statement(s)
    
    def _analyze_expression(self, expr: ExpressionNode) -> DataType:
        """
        Analyze an expression and infer its type
        
        Returns:
            Inferred data type
        """
        if isinstance(expr, VariableNode):
            # Look up variable and record usage
            symbol = self.current_scope.lookup_variable(expr.name)
            if symbol:
                symbol.line_last_used = expr.line_start
                return symbol.data_type
            else:
                # Variable not defined - could be from input dataset
                self.current_scope.define(Symbol(
                    name=expr.name,
                    kind=SymbolKind.VARIABLE,
                    line_defined=expr.line_start,
                    is_initialized=False,  # May come from SET
                    attributes={'implicit': True}
                ))
            return DataType.UNKNOWN
        
        elif isinstance(expr, LiteralNode):
            if expr.literal_type == 'number':
                return DataType.NUMERIC
            elif expr.literal_type == 'string':
                return DataType.CHARACTER
            elif expr.literal_type == 'date':
                return DataType.DATE
            return DataType.UNKNOWN
        
        elif isinstance(expr, MacroVarRefNode):
            # Record macro variable usage
            self.dependencies.macro_vars_used.add(expr.var_name)
            
            # Check if defined
            symbol = self.current_scope.lookup_macro_var(expr.var_name)
            if not symbol:
                self.warnings.append(SemanticError(
                    message=f"Macro variable '&{expr.var_name}' may not be defined",
                    line=expr.line_start,
                    severity="warning",
                    node=expr
                ))
            return DataType.UNKNOWN
        
        elif isinstance(expr, FunctionCallNode):
            # Analyze function arguments
            for arg in expr.arguments:
                self._analyze_expression(arg)
            
            # Infer return type based on function
            return self._infer_function_return_type(expr.function_name)
        
        # For complex expressions, recurse into children
        if hasattr(expr, 'children'):
            for child in expr.children:
                if isinstance(child, ExpressionNode):
                    self._analyze_expression(child)
        
        return DataType.UNKNOWN
    
    def _analyze_proc_step(self, proc: ProcNode) -> None:
        """Analyze a PROC step"""
        # Track input/output datasets
        for ds in proc.input_datasets:
            ds_name = self._normalize_dataset_name(ds)
            self.dependencies.datasets_read.add(ds_name)
        
        for ds in proc.output_datasets:
            ds_name = self._normalize_dataset_name(ds)
            self.dependencies.datasets_written.add(ds_name)
            self.global_scope.define(Symbol(
                name=ds_name,
                kind=SymbolKind.DATASET,
                line_defined=proc.line_start
            ))
    
    def _check_undefined_variables(self, data_step: DataStepNode) -> None:
        """Check for undefined variables in a data step"""
        # This would be more thorough with full expression analysis
        pass
    
    def _normalize_dataset_name(self, name: str) -> str:
        """Normalize a dataset name (handle libref.dataset format)"""
        # Remove any options in parentheses
        if '(' in name:
            name = name[:name.index('(')]
        return name.strip().lower()
    
    def _infer_function_return_type(self, func_name: str) -> DataType:
        """Infer the return type of a SAS function"""
        func_lower = func_name.lower()
        
        # Numeric functions
        numeric_funcs = {
            'sum', 'mean', 'min', 'max', 'n', 'nmiss', 'std', 'var', 'range',
            'abs', 'sqrt', 'exp', 'log', 'log10', 'sin', 'cos', 'tan',
            'int', 'round', 'floor', 'ceil', 'mod', 'sign',
            'lag', 'dif', 'length', 'count', 'countw', 'index', 'verify'
        }
        
        # Character functions
        char_funcs = {
            'substr', 'scan', 'trim', 'left', 'right', 'upcase', 'lowcase',
            'compress', 'tranwrd', 'translate', 'reverse', 'strip',
            'cat', 'cats', 'catx', 'catt', 'put'
        }
        
        # Date functions
        date_funcs = {
            'date', 'today', 'mdy', 'yymmdd', 'datepart', 'intnx'
        }
        
        # Time functions
        time_funcs = {'time', 'timepart', 'hms'}
        
        # Datetime functions
        datetime_funcs = {'datetime', 'dhms'}
        
        if func_lower in numeric_funcs:
            return DataType.NUMERIC
        elif func_lower in char_funcs:
            return DataType.CHARACTER
        elif func_lower in date_funcs:
            return DataType.DATE
        elif func_lower in time_funcs:
            return DataType.TIME
        elif func_lower in datetime_funcs:
            return DataType.DATETIME
        else:
            return DataType.UNKNOWN
    
    def get_variable_summary(self) -> Dict[str, Any]:
        """Get a summary of all variables found"""
        variables = self.global_scope.get_all_symbols(SymbolKind.VARIABLE)
        
        return {
            'total_variables': len(variables),
            'numeric': len([v for v in variables if v.data_type == DataType.NUMERIC]),
            'character': len([v for v in variables if v.data_type == DataType.CHARACTER]),
            'unknown': len([v for v in variables if v.data_type == DataType.UNKNOWN]),
            'variables': [
                {
                    'name': v.name,
                    'type': v.data_type.name,
                    'scope': v.scope,
                    'defined_line': v.line_defined,
                    'initialized': v.is_initialized
                }
                for v in variables
            ]
        }
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """Get a summary of dependencies"""
        return {
            'datasets_read': list(self.dependencies.datasets_read),
            'datasets_written': list(self.dependencies.datasets_written),
            'macro_vars_used': list(self.dependencies.macro_vars_used),
            'macro_vars_defined': list(self.dependencies.macro_vars_defined),
            'macros_called': list(self.dependencies.macros_called),
            'libraries_used': list(self.dependencies.libraries_used)
        }
    
    def generate_python_declarations(self) -> str:
        """
        Generate Python variable declarations for macro variables
        
        Returns:
            Python code string with variable declarations
        """
        lines = []
        lines.append("# SAS Macro Variables (from semantic analysis)")
        lines.append("# These variables were detected in the SAS code")
        lines.append("")
        
        macro_vars = self.global_scope.get_all_symbols(SymbolKind.MACRO_VAR)
        
        for var in macro_vars:
            if var.attributes.get('system'):
                continue  # Skip system variables
            
            value = var.attributes.get('value', 'None')
            if value is None:
                value = 'None'
            
            # Try to infer Python type
            python_value = self._sas_value_to_python(value)
            
            comment = f"  # Line {var.line_defined}" if var.line_defined > 0 else ""
            lines.append(f"{var.name} = {python_value}{comment}")
        
        return '\n'.join(lines)
    
    def _sas_value_to_python(self, value: str) -> str:
        """Convert a SAS value to Python representation"""
        if value is None or value == '':
            return 'None'
        
        # Try numeric
        try:
            float(value)
            return value
        except ValueError:
            pass
        
        # String
        if value.startswith(("'", '"')):
            return value
        
        # Default to string
        return f"'{value}'"

