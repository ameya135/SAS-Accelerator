"""
CLI Tool: Visualize SAS Dependency Graph

Generates visualizations of SAS code dependency graphs.
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.visualization.graph_renderer import GraphRenderer


console = Console()


def visualize_sas_file(
    sas_file: str,
    output_path: str,
    format: str = "png",
    title: Optional[str] = None,
    show_layers: bool = True
) -> bool:
    """
    Generate dependency graph visualization for a SAS file

    Args:
        sas_file: Path to SAS file
        output_path: Output path for visualization
        format: Output format (png, svg, pdf, dot)
        title: Graph title
        show_layers: Show execution layers

    Returns:
        True if successful
    """
    console.print(f"\n[bold cyan]📊 Generating Dependency Graph Visualization[/bold cyan]")
    console.print(f"[cyan]Source:[/cyan] {sas_file}")
    console.print(f"[cyan]Output:[/cyan] {output_path}")
    console.print(f"[cyan]Format:[/cyan] {format}\n")

    try:
        # Build graph
        console.print("[cyan]Building dependency graph...[/cyan]")
        builder = GraphBuilder.from_file(sas_file)
        graph = builder.build_graph()
        summary = builder.get_summary()

        console.print(f"  [green]✓[/green] Graph built: {summary['total_nodes']} nodes, {summary['total_edges']} edges")

        # Render visualization
        console.print("\n[cyan]Rendering visualization...[/cyan]")
        renderer = GraphRenderer()

        if title is None:
            title = f"Dependency Graph: {Path(sas_file).name}"

        success = renderer.render_to_file(
            graph=graph,
            output_path=output_path,
            format=format,
            title=title
        )

        if success:
            console.print(f"  [green]✓[/green] Visualization saved to: {output_path}")
            return True
        else:
            console.print(f"  [red]✗[/red] Failed to render visualization")
            return False

    except Exception as e:
        console.print(f"\n[bold red]✗ Visualization failed:[/bold red]")
        console.print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate dependency graph visualization for SAS code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PNG visualization
  python -m graph_approach.cli.visualize input.sas --output graph.png

  # Generate SVG (vector)
  python -m graph_approach.cli.visualize input.sas -o graph.svg --format svg

  # Generate DOT file for custom processing
  python -m graph_approach.cli.visualize input.sas -o graph.dot --format dot

Supported formats:
  - png: Portable Network Graphics (default)
  - svg: Scalable Vector Graphics
  - pdf: Portable Document Format
  - dot: Graphviz DOT format (text)
        """
    )

    parser.add_argument(
        "sas_file",
        help="Path to SAS file to visualize"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output path for visualization"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["png", "svg", "pdf", "dot"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument(
        "-t", "--title",
        help="Graph title (default: auto-generated from filename)"
    )
    parser.add_argument(
        "--no-layers",
        action="store_true",
        help="Don't show execution layers"
    )

    args = parser.parse_args()

    # Check if SAS file exists
    if not Path(args.sas_file).exists():
        console.print(f"[bold red]Error:[/bold red] SAS file not found: {args.sas_file}")
        sys.exit(1)

    # Visualize
    success = visualize_sas_file(
        sas_file=args.sas_file,
        output_path=args.output,
        format=args.format,
        title=args.title,
        show_layers=not args.no_layers
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
