"""
CLI Tool: Analyze SAS File Dependencies

Analyzes a SAS file and displays dependency graph information.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.core.dependency_graph import NodeType, EdgeType


console = Console()


def analyze_sas_file(
    file_path: str,
    output_format: str = "text",
    save_graph: Optional[str] = None,
    show_execution_order: bool = True,
    show_cycles: bool = True
) -> None:
    """
    Analyze a SAS file and display dependency information

    Args:
        file_path: Path to SAS file
        output_format: Output format (text, json)
        save_graph: Path to save graph JSON (optional)
        show_execution_order: Show execution order
        show_cycles: Show cycles if any
    """
    console.print(f"\n[bold cyan]Analyzing SAS file:[/bold cyan] {file_path}\n")

    try:
        # Build graph
        builder = GraphBuilder.from_file(file_path)
        graph = builder.build_graph()
        summary = builder.get_summary()

        if output_format == "json":
            _output_json(graph, summary, builder)
        else:
            _output_text(graph, summary, builder, show_execution_order, show_cycles)

        # Save graph if requested
        if save_graph:
            graph_data = graph.to_dict()
            with open(save_graph, 'w') as f:
                json.dump(graph_data, f, indent=2)
            console.print(f"\n[green]✓[/green] Graph saved to: {save_graph}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _output_text(graph, summary, builder, show_execution_order, show_cycles):
    """Output in text format with rich formatting"""

    # Summary panel
    summary_text = Text()
    summary_text.append(f"Total Nodes: {summary['total_nodes']}\n", style="bold")
    summary_text.append(f"Total Edges: {summary['total_edges']}\n", style="bold")
    summary_text.append(f"Has Cycles: {'Yes ⚠️' if summary['has_cycles'] else 'No ✓'}\n",
                        style="red" if summary['has_cycles'] else "green")

    console.print(Panel(summary_text, title="📊 Graph Summary", border_style="cyan"))

    # Node counts by type
    node_table = Table(title="Node Counts by Type", show_header=True)
    node_table.add_column("Node Type", style="cyan")
    node_table.add_column("Count", justify="right", style="green")

    for node_type, count in summary['node_counts_by_type'].items():
        if count > 0:
            node_table.add_row(node_type, str(count))

    console.print(node_table)

    # Show cycles if requested and they exist
    if show_cycles and summary['has_cycles']:
        console.print("\n[bold red]⚠️  Cycles Detected:[/bold red]")
        cycles = graph.find_cycles()
        for i, cycle in enumerate(cycles, 1):
            console.print(f"  Cycle {i}: {' → '.join(cycle)} → {cycle[0]}")

    # Show execution order if requested
    if show_execution_order and not summary['has_cycles']:
        console.print("\n[bold cyan]Execution Order:[/bold cyan]")

        try:
            execution_order = builder.get_execution_order()

            # Group by type for better readability
            for i, node in enumerate(execution_order, 1):
                type_emoji = {
                    NodeType.DATASET: "📊",
                    NodeType.DATA_STEP: "🔄",
                    NodeType.PROC: "⚙️",
                    NodeType.MACRO: "🔧",
                    NodeType.MACRO_VARIABLE: "📝",
                    NodeType.LIBRARY: "📚",
                    NodeType.FILE_REF: "📁"
                }.get(node.node_type, "•")

                console.print(f"  {i:2d}. {type_emoji} [{node.node_type.value}] {node.name}")

        except ValueError as e:
            console.print(f"[red]Cannot determine execution order: {e}[/red]")

    # Show dependencies for key nodes
    console.print("\n[bold cyan]Key Dependencies:[/bold cyan]")

    # Show DATA steps and their dependencies
    data_steps = graph.get_nodes_by_type(NodeType.DATA_STEP)
    if data_steps:
        console.print("\n  [yellow]DATA Steps:[/yellow]")
        for step in data_steps[:5]:  # Show first 5
            deps = graph.get_dependencies(step.node_id)
            dep_names = [d.name for d in deps]
            console.print(f"    • {step.name}")
            if dep_names:
                console.print(f"      Depends on: {', '.join(dep_names)}")

    # Show PROCs and their dependencies
    procs = graph.get_nodes_by_type(NodeType.PROC)
    if procs:
        console.print("\n  [yellow]PROC Steps:[/yellow]")
        for proc in procs[:5]:  # Show first 5
            deps = graph.get_dependencies(proc.node_id)
            dep_names = [d.name for d in deps]
            console.print(f"    • {proc.metadata.get('proc_name', 'UNKNOWN')} ({proc.name})")
            if dep_names:
                console.print(f"      Depends on: {', '.join(dep_names)}")


def _output_json(graph, summary, builder):
    """Output in JSON format"""
    output = {
        "summary": summary,
        "graph": graph.to_dict()
    }

    # Add execution order if no cycles
    if not summary['has_cycles']:
        try:
            execution_order = builder.get_execution_order()
            output["execution_order"] = [
                {
                    "node_id": node.node_id,
                    "type": node.node_type.value,
                    "name": node.name
                }
                for node in execution_order
            ]
        except:
            pass

    print(json.dumps(output, indent=2))


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze SAS file dependencies and generate dependency graph"
    )
    parser.add_argument("file", help="Path to SAS file to analyze")
    parser.add_argument(
        "-f", "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Save graph to JSON file"
    )
    parser.add_argument(
        "--no-execution-order",
        action="store_true",
        help="Don't show execution order"
    )
    parser.add_argument(
        "--no-cycles",
        action="store_true",
        help="Don't show cycle information"
    )

    args = parser.parse_args()

    analyze_sas_file(
        file_path=args.file,
        output_format=args.format,
        save_graph=args.output,
        show_execution_order=not args.no_execution_order,
        show_cycles=not args.no_cycles
    )


if __name__ == "__main__":
    main()
