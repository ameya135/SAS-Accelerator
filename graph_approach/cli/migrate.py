"""
CLI Tool: Migrate SAS to PySpark

Performs graph-based migration of SAS files to PySpark.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph_approach.migration.graph_migrator import GraphMigrator
from graph_approach.visualization.graph_renderer import GraphRenderer
from graph_approach.visualization.report_generator import ReportGenerator


console = Console()


def migrate_sas_file(
    sas_file: str,
    output_dir: str,
    model: Optional[str] = None,
    visualize: bool = False,
    generate_report: bool = True,
    use_rag: bool = True,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    max_concurrent: int = 5,
    max_retries: int = 3,
    max_tokens: Optional[int] = None,
    allow_partial_output: bool = True,
) -> bool:
    """
    Migrate a SAS file to PySpark using graph-based approach

    Args:
        sas_file: Path to SAS file
        output_dir: Output directory
        model: LLM model, or Azure deployment name
        visualize: Generate graph visualization
        generate_report: Generate migration report
        use_rag: Use RAG for examples
        api_key: LLM API key
        endpoint: Azure OpenAI endpoint, or OpenAI-compatible base URL
        provider: LLM provider
        base_url: OpenAI-compatible base URL
        max_concurrent: Maximum concurrent chunk-level LLM calls
        max_retries: Maximum retry attempts for transient LLM failures
        max_tokens: Maximum completion tokens for chunk conversion calls
        allow_partial_output: Write .py output when some chunks fail

    Returns:
        True if successful
    """
    console.print(f"\n[bold cyan]🔄 Graph-Based SAS to PySpark Migration[/bold cyan]")
    console.print(f"[cyan]Source:[/cyan] {sas_file}")
    console.print(f"[cyan]Output:[/cyan] {output_dir}")
    console.print(f"[cyan]Provider:[/cyan] {provider or 'azure'}")
    console.print(f"[cyan]Model:[/cyan] {model or '(provider default)'}")
    console.print(f"[cyan]Max Chunk LLM Calls:[/cyan] {max_concurrent}")
    console.print(f"[cyan]Max LLM Retries:[/cyan] {max_retries}")
    console.print(f"[cyan]Max Completion Tokens:[/cyan] {max_tokens or '(env/default)'}")
    console.print(f"[cyan]Use RAG:[/cyan] {use_rag}\n")

    try:
        # Initialize migrator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing migrator...", total=None)

            migrator = GraphMigrator(
                api_key=api_key,
                azure_endpoint=endpoint,
                model=model,
                use_rag=use_rag,
                provider=provider,
                base_url=base_url,
                max_concurrent=max_concurrent,
                max_retries=max_retries,
                max_tokens=max_tokens,
                allow_partial_output=allow_partial_output,
            )

            progress.update(task, description="✓ Migrator initialized")

        # Perform migration
        result = migrator.migrate_file(
            sas_file_path=sas_file,
            output_dir=output_dir,
            visualize=visualize
        )

        # Display results
        if result.success:
            console.print(f"\n[bold green]✓ Migration Successful![/bold green]")
            console.print(f"  Chunks converted: {result.chunks_converted}/{result.total_chunks}")
            console.print(f"  Execution time: {result.execution_time:.2f}s")

            # Generate visualization if requested
            if visualize:
                console.print("\n[cyan]Generating visualization...[/cyan]")
                try:
                    from graph_approach.core.graph_builder import GraphBuilder

                    builder = GraphBuilder.from_file(sas_file)
                    graph = builder.build_graph()

                    renderer = GraphRenderer()
                    graph_file = Path(output_dir) / f"{Path(sas_file).stem}_graph.png"

                    if renderer.render_to_file(
                        graph=graph,
                        output_path=str(graph_file),
                        format="png",
                        title=f"Dependency Graph: {Path(sas_file).name}"
                    ):
                        console.print(f"  [green]✓[/green] Graph saved to: {graph_file}")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] Could not generate graph visualization")

                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] Visualization error: {e}")

            # Generate report if requested
            if generate_report:
                console.print("\n[cyan]Generating migration report...[/cyan]")
                try:
                    from graph_approach.core.graph_builder import GraphBuilder
                    from graph_approach.core.chunk_optimizer import ChunkOptimizer

                    builder = GraphBuilder.from_file(sas_file)
                    graph = builder.build_graph()
                    optimizer = ChunkOptimizer(graph)
                    chunks = optimizer.generate_chunks()

                    report_gen = ReportGenerator()
                    report_file = Path(output_dir) / f"{Path(sas_file).stem}_report.md"

                    if report_gen.generate_migration_report(
                        graph=graph,
                        chunks=chunks,
                        migration_result=result.to_dict(),
                        output_path=str(report_file),
                        format="markdown"
                    ):
                        console.print(f"  [green]✓[/green] Report saved to: {report_file}")
                    else:
                        console.print(f"  [yellow]⚠[/yellow] Could not generate report")

                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] Report generation error: {e}")

            return True

        else:
            console.print(f"\n[bold red]✗ Migration Failed[/bold red]")
            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  - {error}")
            return False

    except Exception as e:
        console.print(f"\n[bold red]✗ Migration failed with error:[/bold red]")
        console.print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate SAS code to PySpark using graph-based dependency analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python -m graph_approach.cli.migrate input.sas --output-dir ./output

  # With visualization and specific model
  python -m graph_approach.cli.migrate input.sas -o ./output --model gpt-4 --visualize

  # Without RAG (faster but less context)
  python -m graph_approach.cli.migrate input.sas -o ./output --no-rag

  # OpenRouter
  python -m graph_approach.cli.migrate input.sas -o ./output \\
      --provider openrouter --model qwen/qwen-2.5-coder-32b-instruct

Environment Variables:
  LLM_PROVIDER             azure or openrouter
  AZURE_OPENAI_API_KEY     Azure OpenAI API key
  AZURE_OPENAI_ENDPOINT    Azure OpenAI endpoint URL
  OPENROUTER_API_KEY       OpenRouter API key
  OPENROUTER_MODEL         OpenRouter model id
  OPENROUTER_BASE_URL      OpenRouter API base URL
        """
    )

    parser.add_argument(
        "sas_file",
        help="Path to SAS file to migrate"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="./output",
        help="Output directory for converted files (default: ./output)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model or Azure deployment name (default: provider-specific)"
    )
    parser.add_argument(
        "--provider",
        choices=["azure", "openrouter"],
        help="LLM provider (default: LLM_PROVIDER env var, then azure)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate dependency graph visualization"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't generate migration report"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Don't use RAG for examples (faster)"
    )
    parser.add_argument(
        "--api-key",
        help="LLM API key (Azure: AZURE_OPENAI_API_KEY, OpenRouter: OPENROUTER_API_KEY)"
    )
    parser.add_argument(
        "--endpoint",
        help="Azure endpoint; for OpenRouter, also accepted as OpenAI-compatible base URL"
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible base URL for OpenRouter (default: OPENROUTER_BASE_URL)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent chunk-level LLM calls (default: 5)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retry attempts for transient LLM failures like 429/504 (default: 3)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum completion tokens for chunk conversion calls (default: LLM_MAX_TOKENS or 12000)"
    )
    parser.add_argument(
        "--no-partial-output",
        action="store_true",
        help="Do not write .py output when any chunk fails"
    )

    args = parser.parse_args()

    # Check if SAS file exists
    if not Path(args.sas_file).exists():
        console.print(f"[bold red]Error:[/bold red] SAS file not found: {args.sas_file}")
        sys.exit(1)

    # Migrate
    success = migrate_sas_file(
        sas_file=args.sas_file,
        output_dir=args.output_dir,
        model=args.model,
        visualize=args.visualize,
        generate_report=not args.no_report,
        use_rag=not args.no_rag,
        api_key=args.api_key,
        endpoint=args.endpoint,
        provider=args.provider,
        base_url=args.base_url,
        max_concurrent=args.max_concurrent,
        max_retries=args.max_retries,
        max_tokens=args.max_tokens,
        allow_partial_output=not args.no_partial_output,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
