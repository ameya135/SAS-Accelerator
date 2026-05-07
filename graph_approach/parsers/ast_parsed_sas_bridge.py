"""
Bridge from graph_approach AST (SASASTParser) to the dict shape expected by
DependencyExtractor / GraphBuilder — used when the external sas_code_parser
package is not installed.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from graph_approach.ast.sas_ast import (
    ASTNode,
    AssignmentNode,
    DataStepNode,
    DoLoopNode,
    IfStatementNode,
    MacroNode,
    MergeStatementNode,
    ProcNode,
    ProcSQLStatementNode,
    ProcStatementNode,
    ProgramNode,
    SASASTParser,
    SetStatementNode,
)


def program_to_parsed_sas_dict(sas_code: str) -> Dict[str, Any]:
    """Parse SAS source with the in-repo AST and return a parsed_sas dict."""
    program = SASASTParser(sas_code).parse()
    source_lines = sas_code.splitlines()
    return {
        "data_steps": [
            _data_step_to_step_dict(ds, source_lines) for ds in program.data_steps
        ],
        "proc_steps": [
            _proc_to_step_dict(p, source_lines) for p in program.proc_steps
        ],
        "macros": [_macro_to_step_dict(m, source_lines) for m in program.macros],
    }


def _data_step_to_step_dict(
    ds: DataStepNode, source_lines: Optional[List[str]] = None
) -> Dict[str, Any]:
    reconstructed_body = _stringify_data_step_body(ds)
    source_code = _extract_construct_source(source_lines, ds.line_start, "data")
    body = source_code or reconstructed_body
    if not body.strip() and ds.input_datasets:
        body = "SET " + " ".join(ds.input_datasets) + ";"
    return {
        "output_datasets": " ".join(ds.output_datasets),
        "body": body,
        "source_code": body,
        "start_line": ds.line_start,
        "end_line": ds.line_end,
    }


def _stringify_data_step_body(ds: DataStepNode) -> str:
    lines: List[str] = []
    for stmt in ds.statements:
        lines.extend(_stringify_data_statement(stmt))
    return "\n".join(lines)


def _stringify_data_statement(stmt: ASTNode) -> List[str]:
    if isinstance(stmt, SetStatementNode):
        return ["SET " + " ".join(stmt.datasets) + ";"]
    if isinstance(stmt, MergeStatementNode):
        return ["MERGE " + " ".join(stmt.datasets) + ";"]
    if isinstance(stmt, IfStatementNode):
        out: List[str] = []
        for s in stmt.then_branch:
            out.extend(_stringify_data_statement(s))
        for s in stmt.else_branch:
            out.extend(_stringify_data_statement(s))
        return out
    if isinstance(stmt, DoLoopNode):
        out = []
        for s in stmt.body:
            out.extend(_stringify_data_statement(s))
        return out
    if isinstance(stmt, AssignmentNode) and stmt.metadata.get("is_macro_var"):
        val = stmt.metadata.get("value", "")
        return [f"%LET {stmt.target} = {val};"]
    return []


def _proc_to_step_dict(
    p: ProcNode, source_lines: Optional[List[str]] = None
) -> Dict[str, Any]:
    options_str = " ".join(f"{k}={v}" for k, v in sorted(p.options.items()))
    body_lines: List[str] = []
    for st in p.statements:
        if isinstance(st, ProcSQLStatementNode):
            body_lines.append(st.raw_text.strip() + ";")
        elif isinstance(st, ProcStatementNode):
            body_lines.append(st.raw_text.strip() + ";")
    reconstructed_body = "\n".join(body_lines)
    source_code = _extract_construct_source(source_lines, p.line_start, "proc")
    return {
        "proc_name": p.proc_name,
        "options": options_str,
        "body": source_code or reconstructed_body,
        "source_code": source_code or reconstructed_body,
        "start_line": p.line_start,
        "end_line": p.line_end,
    }


def _macro_to_step_dict(
    m: MacroNode, source_lines: Optional[List[str]] = None
) -> Dict[str, Any]:
    body_chunks: List[str] = []
    for node in m.body:
        text = _stringify_top_level_for_macro_body(node)
        if text:
            body_chunks.append(text)
    reconstructed_body = "\n".join(body_chunks)
    source_code = _extract_construct_source(source_lines, m.line_start, "macro")
    return {
        "name": m.name,
        "body": source_code or reconstructed_body,
        "source_code": source_code or reconstructed_body,
        "parameters": list(m.parameters),
        "start_line": m.line_start,
        "end_line": m.line_end,
        "nesting_level": 0,
    }


def _stringify_top_level_for_macro_body(node: ASTNode) -> str:
    if isinstance(node, DataStepNode):
        inner = _stringify_data_step_body(node)
        header = "DATA " + " ".join(node.output_datasets) + ";"
        parts = [header]
        if inner.strip():
            parts.append(inner)
        parts.append("RUN;")
        return "\n".join(parts)
    if isinstance(node, ProcNode):
        pd = _proc_to_step_dict(node)
        opt = pd["options"]
        head = f"PROC {node.proc_name}"
        if opt:
            head += " " + opt
        head += ";"
        body = pd["body"]
        if body.strip():
            return head + "\n" + body + "\nRUN;"
        return head + "\nRUN;"
    if isinstance(node, MacroNode):
        params = ", ".join(node.parameters)
        header = (
            f"%MACRO {node.name}({params});"
            if node.parameters
            else f"%MACRO {node.name};"
        )
        inner_parts: List[str] = []
        for ch in node.body:
            t = _stringify_top_level_for_macro_body(ch)
            if t:
                inner_parts.append(t)
        return header + "\n" + "\n".join(inner_parts) + "\n%MEND;"
    if isinstance(node, AssignmentNode) and node.metadata.get("is_macro_var"):
        val = node.metadata.get("value", "")
        return f"%LET {node.target} = {val};"
    return ""


def _extract_construct_source(
    source_lines: Optional[List[str]],
    start_line: int,
    construct_type: str,
) -> str:
    """Extract original source for a DATA, PROC, or MACRO construct."""
    if not source_lines or start_line < 1 or start_line > len(source_lines):
        return ""

    terminator_patterns = {
        "data": re.compile(r"^\s*run\s*;", re.IGNORECASE),
        "proc": re.compile(r"^\s*(run|quit)\s*;", re.IGNORECASE),
        "macro": re.compile(r"^\s*%mend\b.*;", re.IGNORECASE),
    }
    terminator = terminator_patterns[construct_type]

    collected: List[str] = []
    for line in source_lines[start_line - 1 :]:
        collected.append(line)
        if terminator.search(line):
            break

    return "\n".join(collected).strip()
