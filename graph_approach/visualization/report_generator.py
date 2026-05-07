"""
Report Generator

Generates comprehensive migration reports in various formats.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from graph_approach.core.dependency_graph import DependencyGraph, NodeType
from graph_approach.core.chunk_optimizer import Chunk


class ReportGenerator:
    """
    Generate migration reports

    Supports HTML and Markdown formats with embedded visualizations,
    statistics, and migration details.
    """

    def __init__(self):
        """Initialize report generator"""
        pass

    def generate_migration_report(
        self,
        graph: DependencyGraph,
        chunks: List[Chunk],
        migration_result: Dict[str, Any],
        output_path: str,
        format: str = "markdown",
    ) -> bool:
        """
        Generate comprehensive migration report

        Args:
            graph: Dependency graph
            chunks: List of chunks
            migration_result: Migration result dictionary
            output_path: Output file path
            format: Report format (markdown, html)

        Returns:
            True if successful
        """
        try:
            if format == "html":
                content = self._generate_html_report(graph, chunks, migration_result)
            else:
                content = self._generate_markdown_report(
                    graph, chunks, migration_result
                )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error generating report: {e}")
            return False

    def _generate_markdown_report(
        self, graph: DependencyGraph, chunks: List[Chunk], result: Dict[str, Any]
    ) -> str:
        """Generate Markdown report"""
        lines = []

        # Header
        lines.append("# SAS to PySpark Migration Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Source File:** {result.get('sas_file', 'Unknown')}")
        lines.append(f"**Migration Method:** Graph-Based Dependency Analysis")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            f"- **Status:** {'✅ Success' if result.get('success') else '❌ Failed'}"
        )
        lines.append(
            f"- **Chunks Converted:** {result.get('chunks_converted', 0)}/{result.get('total_chunks', 0)}"
        )
        lines.append(
            f"- **Execution Time:** {result.get('execution_time', 0):.2f} seconds"
        )
        lines.append(f"- **Errors:** {len(result.get('errors', []))}")
        lines.append(f"- **Warnings:** {len(result.get('warnings', []))}")
        lines.append("")

        # Graph Statistics
        lines.append("## Dependency Graph Statistics")
        lines.append("")
        lines.append(f"- **Total Nodes:** {graph.node_count()}")
        lines.append(f"- **Total Edges:** {graph.edge_count()}")
        lines.append(f"- **Has Cycles:** {'Yes ⚠️' if graph.has_cycles() else 'No ✓'}")
        lines.append(f"- **Root Nodes:** {len(graph.get_root_nodes())}")
        lines.append(f"- **Leaf Nodes:** {len(graph.get_leaf_nodes())}")
        lines.append("")

        # Node Breakdown
        lines.append("### Node Type Breakdown")
        lines.append("")
        for node_type in NodeType:
            count = len(graph.get_nodes_by_type(node_type))
            if count > 0:
                lines.append(f"- **{node_type.value}:** {count}")
        lines.append("")

        # Chunk Statistics
        lines.append("## Chunk Statistics")
        lines.append("")
        lines.append(f"- **Total Chunks:** {len(chunks)}")
        if chunks:
            total_tokens = sum(c.estimated_tokens for c in chunks)
            avg_tokens = total_tokens / len(chunks)
            lines.append(f"- **Total Tokens:** {total_tokens}")
            lines.append(f"- **Average Tokens/Chunk:** {avg_tokens:.0f}")
            lines.append(f"- **Min Tokens:** {min(c.estimated_tokens for c in chunks)}")
            lines.append(f"- **Max Tokens:** {max(c.estimated_tokens for c in chunks)}")
        lines.append("")

        # Execution Order
        if not graph.has_cycles():
            lines.append("## Execution Order")
            lines.append("")
            try:
                execution_order = graph.topological_sort()
                for i, node in enumerate(execution_order[:20], 1):  # Show first 20
                    lines.append(f"{i}. `{node.name}` ({node.node_type.value})")
                if len(execution_order) > 20:
                    lines.append(f"... and {len(execution_order) - 20} more")
                lines.append("")
            except:
                lines.append("Could not determine execution order")
                lines.append("")

        # Errors and Warnings
        if result.get("errors"):
            lines.append("## Errors")
            lines.append("")
            for error in result["errors"]:
                lines.append(f"- ❌ {error}")
            lines.append("")

        if result.get("warnings"):
            lines.append("## Warnings")
            lines.append("")
            for warning in result["warnings"]:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        # Metadata
        if result.get("metadata"):
            lines.append("## Metadata")
            lines.append("")
            lines.append("```json")

            lines.append(json.dumps(result["metadata"], indent=2))
            lines.append("```")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Generated by Graph-Based SAS to PySpark Migration Tool*")

        return "\n".join(lines)

    def _generate_html_report(
        self, graph: DependencyGraph, chunks: List[Chunk], result: Dict[str, Any]
    ) -> str:
        """Generate HTML report"""
        # Convert markdown to HTML-friendly format
        md_content = self._generate_markdown_report(graph, chunks, result)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SAS to PySpark Migration Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f6f8fa;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #24292e;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #24292e;
            margin-top: 30px;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #586069;
        }}
        .success {{ color: #28a745; }}
        .error {{ color: #d73a49; }}
        .warning {{ color: #f66a0a; }}
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 85%;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        ul {{
            margin-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #0366d6;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #24292e;
        }}
        .stat-label {{
            color: #586069;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 SAS to PySpark Migration Report</h1>

        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Source File:</strong> {result.get("sas_file", "Unknown")}</p>
        <p><strong>Migration Method:</strong> Graph-Based Dependency Analysis</p>

        <h2>Executive Summary</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value {"success" if result.get("success") else "error"}">
                    {"✅ Success" if result.get("success") else "❌ Failed"}
                </div>
                <div class="stat-label">Status</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result.get("chunks_converted", 0)}/{result.get("total_chunks", 0)}</div>
                <div class="stat-label">Chunks Converted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{result.get("execution_time", 0):.2f}s</div>
                <div class="stat-label">Execution Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(result.get("errors", []))}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>

        <h2>Dependency Graph Statistics</h2>
        <ul>
            <li><strong>Total Nodes:</strong> {graph.node_count()}</li>
            <li><strong>Total Edges:</strong> {graph.edge_count()}</li>
            <li><strong>Has Cycles:</strong> {'<span class="warning">Yes ⚠️</span>' if graph.has_cycles() else '<span class="success">No ✓</span>'}</li>
        </ul>

        <hr>
        <p style="text-align: center; color: #586069;">
            <em>Generated by Graph-Based SAS to PySpark Migration Tool</em>
        </p>
    </div>
</body>
</html>
"""
        return html

    def generate_summary_report(
        self, results: List[Dict[str, Any]], output_path: str
    ) -> bool:
        """
        Generate summary report for multiple migrations

        Args:
            results: List of migration results
            output_path: Output path

        Returns:
            True if successful
        """
        try:
            lines = []
            lines.append("# Migration Summary Report")
            lines.append("")
            lines.append(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append(f"**Total Files Migrated:** {len(results)}")
            lines.append("")

            # Overall statistics
            total_success = sum(1 for r in results if r.get("success"))
            total_chunks = sum(r.get("total_chunks", 0) for r in results)
            total_converted = sum(r.get("chunks_converted", 0) for r in results)
            total_time = sum(r.get("execution_time", 0) for r in results)

            lines.append("## Overall Statistics")
            lines.append("")
            lines.append(
                f"- **Success Rate:** {total_success}/{len(results)} ({100 * total_success / len(results) if results else 0:.1f}%)"
            )
            lines.append(f"- **Total Chunks:** {total_chunks}")
            lines.append(f"- **Chunks Converted:** {total_converted}")
            lines.append(f"- **Total Time:** {total_time:.2f} seconds")
            lines.append("")

            # Individual results
            lines.append("## Individual Results")
            lines.append("")
            for i, result in enumerate(results, 1):
                status = "✅" if result.get("success") else "❌"
                lines.append(
                    f"{i}. {status} **{Path(result.get('sas_file', 'Unknown')).name}**"
                )
                lines.append(
                    f"   - Chunks: {result.get('chunks_converted', 0)}/{result.get('total_chunks', 0)}"
                )
                lines.append(f"   - Time: {result.get('execution_time', 0):.2f}s")
                if result.get("errors"):
                    lines.append(f"   - Errors: {len(result['errors'])}")
                lines.append("")

            with open(output_path, "w") as f:
                f.write("\n".join(lines))

            return True

        except Exception as e:
            print(f"Error generating summary report: {e}")
            return False
