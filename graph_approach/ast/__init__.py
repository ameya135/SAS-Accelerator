"""
AST-based SAS Parser

This module provides true Abstract Syntax Tree parsing for SAS code,
enabling precise variable scoping, type inference, and dependency analysis.
"""

import os as _os
import importlib.machinery

_stdlib_ast = None


def _get_stdlib_ast():
    global _stdlib_ast
    if _stdlib_ast is not None:
        return _stdlib_ast
    stdlib_path = _os.path.dirname(_os.__file__)
    ast_path = _os.path.join(stdlib_path, "ast.py")
    if _os.path.exists(ast_path):
        loader = importlib.machinery.SourceFileLoader("_stdlib_ast", ast_path)
        _stdlib_ast = loader.load_module()
        return _stdlib_ast
    return None


__all__ = [
    "SASLexer",
    "Token",
    "TokenType",
    "SASASTParser",
    "ASTNode",
    "ProgramNode",
    "DataStepNode",
    "ProcNode",
    "MacroNode",
    "AssignmentNode",
    "ExpressionNode",
    "VariableNode",
    "LiteralNode",
    "SemanticAnalyzer",
    "SymbolTable",
    "Symbol",
]


def __getattr__(name):
    """Lazy import of submodules, with fallback to stdlib ast"""
    if name in ("SASLexer", "Token", "TokenType"):
        from graph_approach.ast.sas_lexer import SASLexer, Token, TokenType

        return locals()[name]
    elif name in (
        "SASASTParser",
        "ASTNode",
        "ProgramNode",
        "DataStepNode",
        "ProcNode",
        "MacroNode",
        "AssignmentNode",
        "ExpressionNode",
        "VariableNode",
        "LiteralNode",
    ):
        from graph_approach.ast import sas_ast

        return getattr(sas_ast, name)
    elif name in ("SemanticAnalyzer", "SymbolTable", "Symbol"):
        from graph_approach.ast import semantic_analyzer

        return getattr(semantic_analyzer, name)
    stdlib = _get_stdlib_ast()
    if stdlib is not None:
        try:
            return getattr(stdlib, name)
        except AttributeError:
            pass
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
