"""
SAS AST Parser

Parses tokenized SAS code into an Abstract Syntax Tree.
Defines AST node types for all major SAS constructs.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from graph_approach.ast.sas_lexer import SASLexer, Token, TokenType


class NodeType(Enum):
    """Types of AST nodes"""
    PROGRAM = auto()
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
    
    # PROC body statements
    PROC_STATEMENT = auto()
    PROC_SQL_STATEMENT = auto()

    # Other
    COMMENT = auto()
    OPTIONS = auto()
    LIBNAME = auto()
    FILENAME = auto()
    TITLE = auto()


@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    node_type: NodeType
    line_start: int = 0
    line_end: int = 0
    children: List['ASTNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: 'ASTNode') -> None:
        """Add a child node"""
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': self.node_type.name,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'metadata': self.metadata,
            'children': [c.to_dict() for c in self.children]
        }


@dataclass
class ProgramNode(ASTNode):
    """Root node representing entire SAS program"""
    data_steps: List['DataStepNode'] = field(default_factory=list)
    proc_steps: List['ProcNode'] = field(default_factory=list)
    macros: List['MacroNode'] = field(default_factory=list)
    global_statements: List[ASTNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.PROGRAM


@dataclass
class DataStepNode(ASTNode):
    """Represents a DATA step"""
    output_datasets: List[str] = field(default_factory=list)
    input_datasets: List[str] = field(default_factory=list)
    statements: List[ASTNode] = field(default_factory=list)
    variables_defined: List[str] = field(default_factory=list)
    variables_used: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.DATA_STEP


@dataclass
class ProcNode(ASTNode):
    """Represents a PROC step"""
    proc_name: str = ""
    options: Dict[str, Any] = field(default_factory=dict)
    input_datasets: List[str] = field(default_factory=list)
    output_datasets: List[str] = field(default_factory=list)
    statements: List[ASTNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.PROC_STEP


@dataclass
class MacroNode(ASTNode):
    """Represents a macro definition"""
    name: str = ""
    parameters: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
    local_vars: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.MACRO_DEF


@dataclass
class AssignmentNode(ASTNode):
    """Represents an assignment statement"""
    target: str = ""
    expression: Optional['ExpressionNode'] = None
    
    def __post_init__(self):
        self.node_type = NodeType.ASSIGNMENT


@dataclass
class ExpressionNode(ASTNode):
    """Represents an expression"""
    pass


@dataclass
class BinaryOpNode(ExpressionNode):
    """Represents a binary operation"""
    operator: str = ""
    left: Optional[ExpressionNode] = None
    right: Optional[ExpressionNode] = None
    
    def __post_init__(self):
        self.node_type = NodeType.BINARY_OP


@dataclass
class UnaryOpNode(ExpressionNode):
    """Represents a unary operation"""
    operator: str = ""
    operand: Optional[ExpressionNode] = None
    
    def __post_init__(self):
        self.node_type = NodeType.UNARY_OP


@dataclass
class FunctionCallNode(ExpressionNode):
    """Represents a function call"""
    function_name: str = ""
    arguments: List[ExpressionNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.FUNCTION_CALL


@dataclass
class VariableNode(ExpressionNode):
    """Represents a variable reference"""
    name: str = ""
    dataset_prefix: Optional[str] = None  # For lib.dataset.var
    
    def __post_init__(self):
        self.node_type = NodeType.VARIABLE


@dataclass
class LiteralNode(ExpressionNode):
    """Represents a literal value"""
    value: Any = None
    literal_type: str = ""  # 'string', 'integer', 'float', 'date', etc.
    
    def __post_init__(self):
        self.node_type = NodeType.LITERAL


@dataclass
class MacroVarRefNode(ExpressionNode):
    """Represents a macro variable reference"""
    var_name: str = ""
    
    def __post_init__(self):
        self.node_type = NodeType.MACRO_VAR_REF


@dataclass
class IfStatementNode(ASTNode):
    """Represents an IF statement"""
    condition: Optional[ExpressionNode] = None
    then_branch: List[ASTNode] = field(default_factory=list)
    else_branch: List[ASTNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.IF_STATEMENT


@dataclass
class DoLoopNode(ASTNode):
    """Represents a DO loop"""
    loop_var: Optional[str] = None
    start_expr: Optional[ExpressionNode] = None
    end_expr: Optional[ExpressionNode] = None
    by_expr: Optional[ExpressionNode] = None
    while_condition: Optional[ExpressionNode] = None
    until_condition: Optional[ExpressionNode] = None
    body: List[ASTNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.DO_LOOP


@dataclass
class SetStatementNode(ASTNode):
    """Represents a SET statement"""
    datasets: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.node_type = NodeType.SET_STATEMENT


@dataclass
class MergeStatementNode(ASTNode):
    """Represents a MERGE statement"""
    datasets: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.MERGE_STATEMENT


@dataclass
class ProcStatementNode(ASTNode):
    """Represents a generic statement within a PROC body"""
    statement_type: str = ""  # e.g., 'BY', 'VAR', 'TABLE', 'CLASS', 'OUTPUT', 'WHERE'
    raw_text: str = ""

    def __post_init__(self):
        self.node_type = NodeType.PROC_STATEMENT


@dataclass
class ProcSQLStatementNode(ASTNode):
    """Represents a SQL statement within PROC SQL"""
    sql_type: str = ""  # e.g., 'CREATE TABLE', 'SELECT', 'INSERT', 'DELETE', 'UPDATE', 'DROP'
    raw_text: str = ""

    def __post_init__(self):
        self.node_type = NodeType.PROC_SQL_STATEMENT


class SASASTParser:
    """
    Parser for SAS code that builds an Abstract Syntax Tree
    
    Takes tokens from the lexer and constructs a hierarchical
    tree representation of the SAS program structure.
    """
    
    def __init__(self, code: str):
        """
        Initialize parser with SAS code
        
        Args:
            code: SAS source code to parse
        """
        self.lexer = SASLexer(code)
        self.tokens: List[Token] = []
        self.pos = 0
        self.current_token: Optional[Token] = None
    
    def parse(self) -> ProgramNode:
        """
        Parse the SAS code into an AST
        
        Returns:
            ProgramNode representing the entire program
        """
        # Tokenize
        self.tokens = self.lexer.tokenize(include_whitespace=False, include_comments=True)
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        # Create program node
        program = ProgramNode(
            node_type=NodeType.PROGRAM,
            line_start=1,
            line_end=self.lexer.line
        )
        
        # Parse top-level constructs
        while not self._is_eof():
            node = self._parse_top_level()
            if node:
                if isinstance(node, DataStepNode):
                    program.data_steps.append(node)
                elif isinstance(node, ProcNode):
                    program.proc_steps.append(node)
                elif isinstance(node, MacroNode):
                    program.macros.append(node)
                else:
                    program.global_statements.append(node)
                program.children.append(node)
        
        return program
    
    def _parse_top_level(self) -> Optional[ASTNode]:
        """Parse a top-level construct"""
        if self._is_eof():
            return None
        
        token = self.current_token
        
        # Skip comments
        if token.type == TokenType.COMMENT:
            node = ASTNode(
                node_type=NodeType.COMMENT,
                line_start=token.line,
                line_end=token.line,
                metadata={'text': token.value}
            )
            self._advance()
            return node
        
        # Check for DATA step
        if token.type == TokenType.KEYWORD and token.value.lower() == 'data':
            return self._parse_data_step()
        
        # Check for PROC step
        if token.type == TokenType.KEYWORD and token.value.lower() == 'proc':
            return self._parse_proc_step()
        
        # Check for macro definition
        if token.type == TokenType.MACRO_KEYWORD and token.value.lower() == '%macro':
            return self._parse_macro_def()
        
        # Check for global statements
        if token.type == TokenType.KEYWORD:
            lower = token.value.lower()
            if lower == 'libname':
                return self._parse_libname()
            elif lower == 'filename':
                return self._parse_filename()
            elif lower == 'options':
                return self._parse_options()
            elif lower == 'title':
                return self._parse_title()
        
        # Check for %LET
        if token.type == TokenType.MACRO_KEYWORD and token.value.lower() == '%let':
            return self._parse_macro_let()
        
        # Skip unknown tokens
        self._advance()
        return None
    
    def _parse_data_step(self) -> DataStepNode:
        """Parse a DATA step"""
        start_line = self.current_token.line
        self._advance()  # Skip 'data'
        
        # Parse output dataset names
        output_datasets = []
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type == TokenType.IDENTIFIER:
                output_datasets.append(self.current_token.value)
            self._advance()
        
        self._expect(TokenType.SEMICOLON)
        
        # Parse DATA step body
        statements = []
        input_datasets = []
        variables_defined = set()
        variables_used = set()
        
        while not self._is_eof():
            token = self.current_token
            
            # Check for end of DATA step
            if token.type == TokenType.KEYWORD and token.value.lower() == 'run':
                self._advance()
                self._consume_if(TokenType.SEMICOLON)
                break
            
            # Check for next DATA or PROC (implicit end)
            if token.type == TokenType.KEYWORD and token.value.lower() in ('data', 'proc'):
                break
            
            # Parse statement
            stmt = self._parse_data_step_statement()
            if stmt:
                statements.append(stmt)
                
                # Track input datasets from SET/MERGE
                if isinstance(stmt, SetStatementNode):
                    input_datasets.extend(stmt.datasets)
                elif isinstance(stmt, MergeStatementNode):
                    input_datasets.extend(stmt.datasets)
                
                # Track variables
                if isinstance(stmt, AssignmentNode):
                    variables_defined.add(stmt.target)
        
        return DataStepNode(
            node_type=NodeType.DATA_STEP,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            output_datasets=output_datasets,
            input_datasets=input_datasets,
            statements=statements,
            variables_defined=list(variables_defined),
            variables_used=list(variables_used)
        )
    
    def _parse_data_step_statement(self) -> Optional[ASTNode]:
        """Parse a statement within a DATA step"""
        if self._is_eof():
            return None
        
        token = self.current_token
        
        # Skip comments
        if token.type == TokenType.COMMENT:
            self._advance()
            return None
        
        # SET statement
        if token.type == TokenType.KEYWORD and token.value.lower() == 'set':
            return self._parse_set_statement()
        
        # MERGE statement
        if token.type == TokenType.KEYWORD and token.value.lower() == 'merge':
            return self._parse_merge_statement()
        
        # IF statement
        if token.type == TokenType.KEYWORD and token.value.lower() == 'if':
            return self._parse_if_statement()
        
        # DO loop
        if token.type == TokenType.KEYWORD and token.value.lower() == 'do':
            return self._parse_do_loop()
        
        # Assignment or other statement
        if token.type == TokenType.IDENTIFIER:
            # Look ahead for assignment
            next_token = self._peek()
            if next_token and next_token.type == TokenType.ASSIGN:
                return self._parse_assignment()
        
        # Skip to semicolon for unrecognized statements
        self._skip_to_semicolon()
        return None
    
    def _parse_set_statement(self) -> SetStatementNode:
        """Parse a SET statement"""
        start_line = self.current_token.line
        self._advance()  # Skip 'set'
        
        datasets = []
        options = {}
        
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type == TokenType.IDENTIFIER:
                # Could be dataset name or option
                name = self.current_token.value
                self._advance()
                
                # Check for dataset options in parentheses
                if self.current_token and self.current_token.type == TokenType.LPAREN:
                    self._skip_parentheses()
                
                datasets.append(name)
            else:
                self._advance()
        
        self._consume_if(TokenType.SEMICOLON)
        
        return SetStatementNode(
            node_type=NodeType.SET_STATEMENT,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            datasets=datasets,
            options=options
        )
    
    def _parse_merge_statement(self) -> MergeStatementNode:
        """Parse a MERGE statement"""
        start_line = self.current_token.line
        self._advance()  # Skip 'merge'
        
        datasets = []
        
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type == TokenType.IDENTIFIER:
                name = self.current_token.value
                self._advance()
                
                # Skip dataset options
                if self.current_token and self.current_token.type == TokenType.LPAREN:
                    self._skip_parentheses()
                
                datasets.append(name)
            else:
                self._advance()
        
        self._consume_if(TokenType.SEMICOLON)
        
        return MergeStatementNode(
            node_type=NodeType.MERGE_STATEMENT,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            datasets=datasets
        )
    
    def _parse_assignment(self) -> AssignmentNode:
        """Parse an assignment statement"""
        start_line = self.current_token.line
        target = self.current_token.value
        self._advance()  # Skip variable name
        self._advance()  # Skip '='
        
        # Parse expression (simplified - just collect tokens to semicolon)
        expr_tokens = []
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            expr_tokens.append(self.current_token)
            self._advance()
        
        self._consume_if(TokenType.SEMICOLON)
        
        # Create simple expression node
        expression = self._tokens_to_expression(expr_tokens)
        
        return AssignmentNode(
            node_type=NodeType.ASSIGNMENT,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            target=target,
            expression=expression
        )
    
    def _parse_if_statement(self) -> IfStatementNode:
        """Parse an IF statement"""
        start_line = self.current_token.line
        self._advance()  # Skip 'if'
        
        # Parse condition (until THEN)
        condition_tokens = []
        while not self._is_eof():
            if self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'then':
                break
            condition_tokens.append(self.current_token)
            self._advance()
        
        self._advance()  # Skip 'then'
        
        condition = self._tokens_to_expression(condition_tokens)
        then_branch = []
        else_branch = []
        
        # Parse THEN branch
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'do':
            # Block IF-THEN-DO
            then_branch.append(self._parse_do_loop())
        else:
            # Single statement IF
            stmt = self._parse_data_step_statement()
            if stmt:
                then_branch.append(stmt)
        
        # Check for ELSE
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'else':
            self._advance()  # Skip 'else'
            
            if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'if':
                # ELSE IF
                else_branch.append(self._parse_if_statement())
            elif self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'do':
                # ELSE DO
                else_branch.append(self._parse_do_loop())
            else:
                # Single statement ELSE
                stmt = self._parse_data_step_statement()
                if stmt:
                    else_branch.append(stmt)
        
        return IfStatementNode(
            node_type=NodeType.IF_STATEMENT,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch
        )
    
    def _parse_do_loop(self) -> DoLoopNode:
        """Parse a DO loop"""
        start_line = self.current_token.line
        self._advance()  # Skip 'do'
        
        loop_var = None
        start_expr = None
        end_expr = None
        by_expr = None
        while_condition = None
        until_condition = None
        body = []
        
        # Check for loop variable
        if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            next_token = self._peek()
            if next_token and next_token.type == TokenType.ASSIGN:
                loop_var = self.current_token.value
                self._advance()  # Skip var
                self._advance()  # Skip '='
                
                # Parse start expression
                start_tokens = []
                while not self._is_eof() and self.current_token.type != TokenType.KEYWORD:
                    start_tokens.append(self.current_token)
                    self._advance()
                
                start_expr = self._tokens_to_expression(start_tokens)
                
                # Check for TO
                if self.current_token and self.current_token.value.lower() == 'to':
                    self._advance()
                    
                    # Parse end expression
                    end_tokens = []
                    while not self._is_eof() and self.current_token.type not in (TokenType.SEMICOLON, TokenType.KEYWORD):
                        end_tokens.append(self.current_token)
                        self._advance()
                    
                    end_expr = self._tokens_to_expression(end_tokens)
        
        # Check for WHILE/UNTIL
        if self.current_token and self.current_token.type == TokenType.KEYWORD:
            if self.current_token.value.lower() == 'while':
                self._advance()
                self._expect(TokenType.LPAREN)
                while_tokens = []
                paren_depth = 1
                while not self._is_eof() and paren_depth > 0:
                    if self.current_token.type == TokenType.LPAREN:
                        paren_depth += 1
                    elif self.current_token.type == TokenType.RPAREN:
                        paren_depth -= 1
                        if paren_depth == 0:
                            break
                    while_tokens.append(self.current_token)
                    self._advance()
                self._consume_if(TokenType.RPAREN)
                while_condition = self._tokens_to_expression(while_tokens)
        
        self._consume_if(TokenType.SEMICOLON)
        
        # Parse body until END
        while not self._is_eof():
            if self.current_token.type == TokenType.KEYWORD and self.current_token.value.lower() == 'end':
                self._advance()
                self._consume_if(TokenType.SEMICOLON)
                break
            
            stmt = self._parse_data_step_statement()
            if stmt:
                body.append(stmt)
        
        return DoLoopNode(
            node_type=NodeType.DO_LOOP,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            loop_var=loop_var,
            start_expr=start_expr,
            end_expr=end_expr,
            by_expr=by_expr,
            while_condition=while_condition,
            until_condition=until_condition,
            body=body
        )
    
    def _parse_proc_step(self) -> ProcNode:
        """Parse a PROC step"""
        start_line = self.current_token.line
        self._advance()  # Skip 'proc'

        # Get procedure name
        proc_name = ""
        if self.current_token and self.current_token.type in (TokenType.IDENTIFIER, TokenType.PROC_NAME, TokenType.KEYWORD):
            proc_name = self.current_token.value.lower()
            self._advance()

        # Parse options until semicolon
        options = {}
        input_datasets = []
        output_datasets = []

        option_name_tokens = (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.PROC_NAME)
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type in option_name_tokens:
                opt_name = self.current_token.value.lower()
                self._advance()

                if self.current_token and self.current_token.type == TokenType.ASSIGN:
                    self._advance()
                    if self.current_token:
                        opt_value = self.current_token.value
                        self._advance()
                        options[opt_name] = opt_value

                        # Track DATA= and OUT= options
                        if opt_name == 'data':
                            input_datasets.append(opt_value)
                        elif opt_name == 'out':
                            output_datasets.append(opt_value)
            else:
                self._advance()

        self._consume_if(TokenType.SEMICOLON)

        # Parse PROC body using proc-type-specific logic
        if proc_name == 'sql':
            statements = self._parse_proc_sql_body()
        else:
            statements = self._parse_proc_generic_body()

        return ProcNode(
            node_type=NodeType.PROC_STEP,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            proc_name=proc_name,
            options=options,
            input_datasets=input_datasets,
            output_datasets=output_datasets,
            statements=statements
        )

    def _parse_proc_sql_body(self) -> List[ASTNode]:
        """Parse PROC SQL body into individual SQL statement nodes"""
        statements = []

        while not self._is_eof():
            if self.current_token.type == TokenType.KEYWORD:
                lower = self.current_token.value.lower()
                if lower in ('quit',):
                    self._advance()
                    self._consume_if(TokenType.SEMICOLON)
                    break
                if lower in ('data', 'proc'):
                    break

            if self.current_token.type == TokenType.COMMENT:
                self._advance()
                continue

            # Determine SQL statement type from leading keyword(s)
            sql_type = ""
            stmt_start_line = self.current_token.line

            if self.current_token.type in (TokenType.KEYWORD, TokenType.IDENTIFIER):
                first_word = self.current_token.value.lower()

                if first_word == 'create':
                    # Could be CREATE TABLE, CREATE VIEW, CREATE INDEX
                    next_tok = self._peek()
                    if next_tok and next_tok.value.lower() in ('table', 'view', 'index'):
                        sql_type = f"CREATE {next_tok.value.upper()}"
                    else:
                        sql_type = "CREATE"
                elif first_word == 'select':
                    sql_type = "SELECT"
                elif first_word == 'insert':
                    sql_type = "INSERT"
                elif first_word == 'update':
                    sql_type = "UPDATE"
                elif first_word == 'delete':
                    sql_type = "DELETE"
                elif first_word == 'drop':
                    sql_type = "DROP"
                elif first_word == 'alter':
                    sql_type = "ALTER"
                else:
                    sql_type = first_word.upper()

            # Collect tokens for this SQL statement until semicolon
            raw_parts = []
            while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
                raw_parts.append(self.current_token.value)
                self._advance()

            stmt_end_line = self.current_token.line if self.current_token else stmt_start_line
            self._consume_if(TokenType.SEMICOLON)

            raw_text = ' '.join(raw_parts)
            if raw_text.strip():
                statements.append(ProcSQLStatementNode(
                    node_type=NodeType.PROC_SQL_STATEMENT,
                    line_start=stmt_start_line,
                    line_end=stmt_end_line,
                    sql_type=sql_type,
                    raw_text=raw_text
                ))

        return statements

    def _parse_proc_generic_body(self) -> List[ASTNode]:
        """Parse generic PROC body into statement nodes (BY, VAR, TABLE, CLASS, etc.)"""
        statements = []

        while not self._is_eof():
            if self.current_token.type == TokenType.KEYWORD:
                lower = self.current_token.value.lower()
                if lower in ('run', 'quit'):
                    self._advance()
                    self._consume_if(TokenType.SEMICOLON)
                    break
                if lower in ('data', 'proc'):
                    break

            if self.current_token.type == TokenType.COMMENT:
                self._advance()
                continue

            # Determine statement type from the leading keyword/identifier
            stmt_start_line = self.current_token.line
            stmt_type = ""

            if self.current_token.type in (TokenType.KEYWORD, TokenType.IDENTIFIER):
                stmt_type = self.current_token.value.upper()

            # Collect tokens until semicolon
            raw_parts = []
            while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
                raw_parts.append(self.current_token.value)
                self._advance()

            stmt_end_line = self.current_token.line if self.current_token else stmt_start_line
            self._consume_if(TokenType.SEMICOLON)

            raw_text = ' '.join(raw_parts)
            if raw_text.strip():
                statements.append(ProcStatementNode(
                    node_type=NodeType.PROC_STATEMENT,
                    line_start=stmt_start_line,
                    line_end=stmt_end_line,
                    statement_type=stmt_type,
                    raw_text=raw_text
                ))

        return statements
    
    def _parse_macro_def(self) -> MacroNode:
        """Parse a macro definition"""
        start_line = self.current_token.line
        self._advance()  # Skip '%macro'
        
        # Get macro name
        name = ""
        if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            name = self.current_token.value
            self._advance()
        
        # Parse parameters
        parameters = []
        if self.current_token and self.current_token.type == TokenType.LPAREN:
            self._advance()
            while not self._is_eof() and self.current_token.type != TokenType.RPAREN:
                if self.current_token.type == TokenType.IDENTIFIER:
                    parameters.append(self.current_token.value)
                self._advance()
            self._consume_if(TokenType.RPAREN)
        
        self._consume_if(TokenType.SEMICOLON)
        
        # Parse macro body until %mend
        body = []
        while not self._is_eof():
            if self.current_token.type == TokenType.MACRO_KEYWORD and self.current_token.value.lower() == '%mend':
                self._advance()
                # Skip optional macro name after %mend
                if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
                    self._advance()
                self._consume_if(TokenType.SEMICOLON)
                break
            
            node = self._parse_top_level()
            if node:
                body.append(node)
        
        return MacroNode(
            node_type=NodeType.MACRO_DEF,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            name=name,
            parameters=parameters,
            body=body
        )
    
    def _parse_macro_let(self) -> ASTNode:
        """Parse a %LET statement"""
        start_line = self.current_token.line
        self._advance()  # Skip '%let'
        
        var_name = ""
        var_value = ""
        
        if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            var_name = self.current_token.value
            self._advance()
        
        if self.current_token and self.current_token.type == TokenType.ASSIGN:
            self._advance()
            
            # Collect value until semicolon
            value_parts = []
            while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
                value_parts.append(self.current_token.value)
                self._advance()
            var_value = ''.join(value_parts)
        
        self._consume_if(TokenType.SEMICOLON)
        
        return AssignmentNode(
            node_type=NodeType.ASSIGNMENT,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            target=var_name,
            metadata={'is_macro_var': True, 'value': var_value}
        )
    
    def _parse_libname(self) -> ASTNode:
        """Parse a LIBNAME statement"""
        start_line = self.current_token.line
        self._advance()  # Skip 'libname'
        
        libref = ""
        path = ""
        
        if self.current_token and self.current_token.type == TokenType.IDENTIFIER:
            libref = self.current_token.value
            self._advance()
        
        # Skip to semicolon, collecting path
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            if self.current_token.type == TokenType.STRING:
                path = self.current_token.value.strip("'\"")
            self._advance()
        
        self._consume_if(TokenType.SEMICOLON)
        
        return ASTNode(
            node_type=NodeType.LIBNAME,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line,
            metadata={'libref': libref, 'path': path}
        )
    
    def _parse_filename(self) -> ASTNode:
        """Parse a FILENAME statement"""
        start_line = self.current_token.line
        self._skip_to_semicolon()
        
        return ASTNode(
            node_type=NodeType.FILENAME,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line
        )
    
    def _parse_options(self) -> ASTNode:
        """Parse an OPTIONS statement"""
        start_line = self.current_token.line
        self._skip_to_semicolon()
        
        return ASTNode(
            node_type=NodeType.OPTIONS,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line
        )
    
    def _parse_title(self) -> ASTNode:
        """Parse a TITLE statement"""
        start_line = self.current_token.line
        self._skip_to_semicolon()
        
        return ASTNode(
            node_type=NodeType.TITLE,
            line_start=start_line,
            line_end=self.current_token.line if self.current_token else start_line
        )
    
    def _tokens_to_expression(self, tokens: List[Token]) -> Optional[ExpressionNode]:
        """Convert a list of tokens to an expression node (simplified)"""
        if not tokens:
            return None
        
        # For now, just wrap in a generic expression
        # A full implementation would build a proper expression tree
        
        # Check for simple cases
        if len(tokens) == 1:
            token = tokens[0]
            if token.type == TokenType.IDENTIFIER:
                return VariableNode(
                    node_type=NodeType.VARIABLE,
                    line_start=token.line,
                    line_end=token.line,
                    name=token.value
                )
            elif token.type in (TokenType.INTEGER, TokenType.FLOAT):
                return LiteralNode(
                    node_type=NodeType.LITERAL,
                    line_start=token.line,
                    line_end=token.line,
                    value=token.value,
                    literal_type='number'
                )
            elif token.type == TokenType.STRING:
                return LiteralNode(
                    node_type=NodeType.LITERAL,
                    line_start=token.line,
                    line_end=token.line,
                    value=token.value,
                    literal_type='string'
                )
            elif token.type == TokenType.MACRO_VAR:
                return MacroVarRefNode(
                    node_type=NodeType.MACRO_VAR_REF,
                    line_start=token.line,
                    line_end=token.line,
                    var_name=token.value.lstrip('&').rstrip('.')
                )
        
        # For complex expressions, return a generic expression
        return ExpressionNode(
            node_type=NodeType.BINARY_OP,
            line_start=tokens[0].line,
            line_end=tokens[-1].line,
            metadata={'raw_tokens': [t.value for t in tokens]}
        )
    
    # Helper methods
    
    def _advance(self) -> None:
        """Advance to next token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None
    
    def _peek(self, offset: int = 1) -> Optional[Token]:
        """Peek at a future token"""
        idx = self.pos + offset
        if 0 <= idx < len(self.tokens):
            return self.tokens[idx]
        return None
    
    def _is_eof(self) -> bool:
        """Check if at end of tokens"""
        return self.current_token is None or self.current_token.type == TokenType.EOF
    
    def _expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type"""
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self._advance()
            return token
        raise SyntaxError(f"Expected {token_type.name}, got {self.current_token}")
    
    def _consume_if(self, token_type: TokenType) -> bool:
        """Consume token if it matches"""
        if self.current_token and self.current_token.type == token_type:
            self._advance()
            return True
        return False
    
    def _skip_to_semicolon(self) -> None:
        """Skip tokens until semicolon"""
        while not self._is_eof() and self.current_token.type != TokenType.SEMICOLON:
            self._advance()
        self._consume_if(TokenType.SEMICOLON)
    
    def _skip_parentheses(self) -> None:
        """Skip balanced parentheses"""
        if not self.current_token or self.current_token.type != TokenType.LPAREN:
            return
        
        self._advance()
        depth = 1
        
        while not self._is_eof() and depth > 0:
            if self.current_token.type == TokenType.LPAREN:
                depth += 1
            elif self.current_token.type == TokenType.RPAREN:
                depth -= 1
            self._advance()
