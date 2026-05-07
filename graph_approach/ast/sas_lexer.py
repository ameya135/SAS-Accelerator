"""
SAS Lexer

Tokenizes SAS code into a stream of tokens for AST parsing.
Handles SAS-specific syntax including macro variables, formats, and labels.
"""

import re
from typing import List, Optional, Generator, Tuple
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Types of tokens in SAS code"""
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    DATE_LITERAL = auto()
    TIME_LITERAL = auto()
    DATETIME_LITERAL = auto()
    
    # Identifiers and keywords
    IDENTIFIER = auto()
    KEYWORD = auto()
    PROC_NAME = auto()
    FORMAT = auto()
    INFORMAT = auto()
    LABEL = auto()
    
    # Macro-related
    MACRO_VAR = auto()          # &varname
    MACRO_FUNC = auto()         # %function
    MACRO_KEYWORD = auto()      # %let, %macro, %mend, etc.
    
    # Operators
    ASSIGN = auto()             # =
    PLUS = auto()               # +
    MINUS = auto()              # -
    MULTIPLY = auto()           # *
    DIVIDE = auto()             # /
    POWER = auto()              # **
    EQ = auto()                 # eq or =
    NE = auto()                 # ne or ^= or ~=
    LT = auto()                 # lt or <
    LE = auto()                 # le or <=
    GT = auto()                 # gt or >
    GE = auto()                 # ge or >=
    AND = auto()                # and or &
    OR = auto()                 # or or |
    NOT = auto()                # not or ^ or ~
    IN = auto()                 # in
    CONCAT = auto()             # ||
    
    # Punctuation
    SEMICOLON = auto()          # ;
    COMMA = auto()              # ,
    DOT = auto()                # .
    COLON = auto()              # :
    LPAREN = auto()             # (
    RPAREN = auto()             # )
    LBRACKET = auto()           # [
    RBRACKET = auto()           # ]
    LBRACE = auto()             # {
    RBRACE = auto()             # }
    
    # Special
    COMMENT = auto()
    NEWLINE = auto()
    WHITESPACE = auto()
    EOF = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    """Represents a single token"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class SASLexer:
    """
    Lexer for SAS code
    
    Tokenizes SAS source code into a stream of tokens.
    Handles:
    - SAS keywords and identifiers
    - Numeric and string literals
    - Macro variables and functions
    - Comments (block and line)
    - Date/time literals
    - Formats and informats
    """
    
    # SAS keywords
    KEYWORDS = {
        # Control flow
        'if', 'then', 'else', 'do', 'end', 'while', 'until', 'to', 'by',
        'select', 'when', 'otherwise', 'leave', 'continue', 'goto', 'link',
        'return', 'stop', 'abort',
        
        # DATA step
        'data', 'set', 'merge', 'update', 'modify', 'run', 'output', 'delete',
        'keep', 'drop', 'rename', 'where', 'firstobs', 'obs', 'in', 'out',
        'input', 'infile', 'file', 'put', 'cards', 'datalines', 'lines',
        'length', 'format', 'informat', 'label', 'attrib', 'array', 'retain',
        'call', 'missing', 'error', 'list', 'lostcard',
        
        # PROC statements
        'proc', 'quit', 'title', 'footnote', 'options', 'libname', 'filename',
        'by', 'class', 'var', 'model', 'tables', 'table', 'freq', 'weight',
        'id', 'ods', 'create', 'insert', 'values', 'from', 'order', 'group',
        'having', 'union', 'join', 'left', 'right', 'inner', 'outer', 'full',
        'on', 'as', 'distinct', 'all', 'case', 'between', 'like', 'null',
        'exists', 'any', 'some', 'desc', 'asc',
        
        # Functions (common)
        'sum', 'mean', 'min', 'max', 'n', 'nmiss', 'std', 'var', 'range',
        'substr', 'scan', 'index', 'trim', 'left', 'right', 'upcase', 'lowcase',
        'compress', 'tranwrd', 'translate', 'reverse', 'length', 'cat', 'cats',
        'catx', 'catt', 'input', 'put', 'int', 'round', 'floor', 'ceil', 'abs',
        'sqrt', 'exp', 'log', 'log10', 'sin', 'cos', 'tan', 'date', 'today',
        'time', 'datetime', 'mdy', 'yrdif', 'intck', 'intnx', 'datepart', 'timepart',
        'lag', 'dif', 'first', 'last', 'coalesce', 'ifn', 'ifc', 'missing',
        'nmiss', 'cmiss', 'count', 'countw', 'verify'
    }
    
    # Macro keywords
    MACRO_KEYWORDS = {
        '%macro', '%mend', '%let', '%if', '%then', '%else', '%do', '%end',
        '%while', '%until', '%to', '%by', '%goto', '%global', '%local',
        '%put', '%include', '%symdel', '%symexist', '%symglobl', '%sysevalf',
        '%eval', '%str', '%nrstr', '%quote', '%nrquote', '%bquote', '%nrbquote',
        '%unquote', '%superq', '%scan', '%substr', '%upcase', '%lowcase',
        '%length', '%index', '%verify', '%compress', '%left', '%trim', '%cmpres',
        '%sysfunc', '%qsysfunc', '%syscall'
    }
    
    # PROC names
    PROC_NAMES = {
        'print', 'sort', 'means', 'freq', 'univariate', 'summary', 'tabulate',
        'report', 'sql', 'transpose', 'append', 'compare', 'contents', 'copy',
        'datasets', 'delete', 'format', 'import', 'export', 'reg', 'glm',
        'logistic', 'mixed', 'genmod', 'phreg', 'lifetest', 'corr', 'factor',
        'princomp', 'cluster', 'fastclus', 'tree', 'varclus', 'sgplot',
        'sgpanel', 'gplot', 'gchart', 'template', 'odstext', 'odstable'
    }
    
    def __init__(self, code: str):
        """
        Initialize lexer with source code
        
        Args:
            code: SAS source code to tokenize
        """
        self.code = code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
        # Build regex patterns
        self._build_patterns()
    
    def _build_patterns(self) -> None:
        """Build compiled regex patterns for tokenization"""
        self.patterns = [
            # Block comments /* ... */
            (re.compile(r'/\*.*?\*/', re.DOTALL), TokenType.COMMENT),
            
            # Line comments * ... ;
            (re.compile(r'^\s*\*[^;]*;', re.MULTILINE), TokenType.COMMENT),
            
            # Macro keywords
            (re.compile(r'%[a-zA-Z_][a-zA-Z0-9_]*'), self._classify_macro_token),
            
            # Macro variables
            (re.compile(r'&[a-zA-Z_][a-zA-Z0-9_]*\.?'), TokenType.MACRO_VAR),
            
            # Date/time/datetime literals
            (re.compile(r"'[^']*'d", re.IGNORECASE), TokenType.DATE_LITERAL),
            (re.compile(r'"[^"]*"d', re.IGNORECASE), TokenType.DATE_LITERAL),
            (re.compile(r"'[^']*'t", re.IGNORECASE), TokenType.TIME_LITERAL),
            (re.compile(r'"[^"]*"t', re.IGNORECASE), TokenType.TIME_LITERAL),
            (re.compile(r"'[^']*'dt", re.IGNORECASE), TokenType.DATETIME_LITERAL),
            (re.compile(r'"[^"]*"dt', re.IGNORECASE), TokenType.DATETIME_LITERAL),
            
            # String literals
            (re.compile(r"'[^']*'"), TokenType.STRING),
            (re.compile(r'"[^"]*"'), TokenType.STRING),
            
            # Numbers
            (re.compile(r'\d+\.\d*([eE][+-]?\d+)?'), TokenType.FLOAT),
            (re.compile(r'\.\d+([eE][+-]?\d+)?'), TokenType.FLOAT),
            (re.compile(r'\d+[eE][+-]?\d+'), TokenType.FLOAT),
            (re.compile(r'\d+'), TokenType.INTEGER),
            
            # Operators (multi-char first)
            (re.compile(r'\*\*'), TokenType.POWER),
            (re.compile(r'\|\|'), TokenType.CONCAT),
            (re.compile(r'<='), TokenType.LE),
            (re.compile(r'>='), TokenType.GE),
            (re.compile(r'\^='), TokenType.NE),
            (re.compile(r'~='), TokenType.NE),
            (re.compile(r'<>'), TokenType.NE),
            
            # Single-char operators
            (re.compile(r'='), TokenType.ASSIGN),
            (re.compile(r'\+'), TokenType.PLUS),
            (re.compile(r'-'), TokenType.MINUS),
            (re.compile(r'\*'), TokenType.MULTIPLY),
            (re.compile(r'/'), TokenType.DIVIDE),
            (re.compile(r'<'), TokenType.LT),
            (re.compile(r'>'), TokenType.GT),
            (re.compile(r'&'), TokenType.AND),
            (re.compile(r'\|'), TokenType.OR),
            (re.compile(r'\^'), TokenType.NOT),
            (re.compile(r'~'), TokenType.NOT),
            
            # Punctuation
            (re.compile(r';'), TokenType.SEMICOLON),
            (re.compile(r','), TokenType.COMMA),
            (re.compile(r'\.'), TokenType.DOT),
            (re.compile(r':'), TokenType.COLON),
            (re.compile(r'\('), TokenType.LPAREN),
            (re.compile(r'\)'), TokenType.RPAREN),
            (re.compile(r'\['), TokenType.LBRACKET),
            (re.compile(r'\]'), TokenType.RBRACKET),
            (re.compile(r'\{'), TokenType.LBRACE),
            (re.compile(r'\}'), TokenType.RBRACE),
            
            # Identifiers (must be after operators)
            (re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'), self._classify_identifier),
            
            # Whitespace
            (re.compile(r'[ \t]+'), TokenType.WHITESPACE),
            (re.compile(r'\n'), TokenType.NEWLINE),
            (re.compile(r'\r\n?'), TokenType.NEWLINE),
        ]
    
    def _classify_identifier(self, value: str) -> TokenType:
        """Classify an identifier as keyword, proc name, or identifier"""
        lower = value.lower()
        
        if lower in self.KEYWORDS:
            return TokenType.KEYWORD
        elif lower in self.PROC_NAMES:
            return TokenType.PROC_NAME
        else:
            return TokenType.IDENTIFIER
    
    def _classify_macro_token(self, value: str) -> TokenType:
        """Classify a macro token"""
        lower = value.lower()
        
        if lower in self.MACRO_KEYWORDS:
            return TokenType.MACRO_KEYWORD
        else:
            return TokenType.MACRO_FUNC
    
    def tokenize(self, include_whitespace: bool = False, include_comments: bool = False) -> List[Token]:
        """
        Tokenize the entire source code
        
        Args:
            include_whitespace: Whether to include whitespace tokens
            include_comments: Whether to include comment tokens
            
        Returns:
            List of tokens
        """
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1
        
        while self.pos < len(self.code):
            token = self._next_token()
            
            if token is None:
                # Unknown character, skip it
                self._advance()
                continue
            
            # Filter tokens based on options
            if token.type == TokenType.WHITESPACE and not include_whitespace:
                continue
            if token.type == TokenType.NEWLINE and not include_whitespace:
                continue
            if token.type == TokenType.COMMENT and not include_comments:
                continue
            
            self.tokens.append(token)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
        return self.tokens
    
    def _next_token(self) -> Optional[Token]:
        """Get the next token from source"""
        if self.pos >= len(self.code):
            return None
        
        for pattern, token_type in self.patterns:
            match = pattern.match(self.code, self.pos)
            if match:
                value = match.group(0)
                
                # Determine actual token type
                if callable(token_type):
                    actual_type = token_type(value)
                else:
                    actual_type = token_type
                
                token = Token(actual_type, value, self.line, self.column)
                
                # Update position
                self._advance(len(value))
                
                return token
        
        # No pattern matched - return unknown token
        char = self.code[self.pos]
        token = Token(TokenType.UNKNOWN, char, self.line, self.column)
        self._advance()
        return token
    
    def _advance(self, count: int = 1) -> None:
        """Advance position in source code"""
        for _ in range(count):
            if self.pos < len(self.code):
                if self.code[self.pos] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.pos += 1
    
    def get_token_stream(self) -> Generator[Token, None, None]:
        """
        Generate tokens one at a time
        
        Yields:
            Token objects
        """
        self.pos = 0
        self.line = 1
        self.column = 1
        
        while self.pos < len(self.code):
            token = self._next_token()
            if token and token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                yield token
        
        yield Token(TokenType.EOF, '', self.line, self.column)
    
    def peek_token(self, offset: int = 0) -> Optional[Token]:
        """
        Peek at a token without consuming it
        
        Args:
            offset: How many tokens ahead to peek
            
        Returns:
            Token at the specified offset, or None
        """
        # Save state
        saved_pos = self.pos
        saved_line = self.line
        saved_col = self.column
        
        # Skip to offset
        token = None
        for _ in range(offset + 1):
            token = self._next_token()
            while token and token.type in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT):
                token = self._next_token()
        
        # Restore state
        self.pos = saved_pos
        self.line = saved_line
        self.column = saved_col
        
        return token
    
    @staticmethod
    def format_tokens(tokens: List[Token]) -> str:
        """
        Format a list of tokens for display
        
        Args:
            tokens: List of tokens to format
            
        Returns:
            Formatted string representation
        """
        lines = []
        current_line = 1
        
        for token in tokens:
            if token.line != current_line:
                lines.append(f"\n--- Line {token.line} ---")
                current_line = token.line
            
            lines.append(f"  {token.type.name:15} | {repr(token.value)}")
        
        return '\n'.join(lines)

