"""
CLI Tool: Batch SAS to PySpark Migration

Migrates multiple SAS files with parallel processing and progress tracking.
"""

import sys
import os
import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import package generator
try:
    from graph_approach.core.package_generator import PackageGenerator
except ImportError:
    try:
        from backend.package_generator import PackageGenerator
    except ImportError:
        PackageGenerator = None


console = Console()


def _find_nested_sas_files(
    sas_directory: str,
    pattern: str = "*.sas",
    limit: int = 5
) -> tuple[int, list[Path]]:
    """
    Find nested SAS files for a helpful non-recursive empty-result hint.

    This intentionally does not change migration behavior; it only helps users
    diagnose directories where matching files exist below the top level.
    """
    directory_path = Path(sas_directory)
    nested_files = [
        f for f in directory_path.rglob(pattern)
        if f.is_file() and f.suffix.lower() == ".sas" and f.parent != directory_path
    ]

    return len(nested_files), sorted(nested_files)[:limit]


def migrate_batch(
    sas_directory: str,
    output_dir: str,
    pattern: str = "*.sas",
    recursive: bool = False,
    max_workers: int = 4,
    continue_on_error: bool = True,
    generate_summary: bool = True,
    model: Optional[str] = None,
    use_rag: bool = True,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    max_concurrent: int = 5,
    max_retries: int = 3,
    max_tokens: Optional[int] = None,
    allow_partial_output: bool = True,
    strict_exit_code: bool = False,
    create_package: bool = False,
    package_name: str = "sas_migration",
    output_layout: str = "flat",
) -> bool:
    """
    Migrate multiple SAS files in a directory

    Args:
        sas_directory: Directory containing SAS files
        output_dir: Output directory
        pattern: File pattern
        recursive: Search subdirectories
        max_workers: Number of parallel workers
        continue_on_error: Continue if files fail
        generate_summary: Generate batch summary report
        model: LLM model, or Azure deployment name
        use_rag: Use RAG for examples
        api_key: LLM API key
        endpoint: Azure OpenAI endpoint, or OpenAI-compatible base URL
        provider: LLM provider
        base_url: OpenAI-compatible base URL
        max_concurrent: Maximum concurrent chunk-level LLM calls per file
        max_retries: Maximum retry attempts for transient LLM failures
        max_tokens: Maximum completion tokens for chunk conversion calls
        allow_partial_output: Write .py output when some chunks fail
        strict_exit_code: Return False if any file fails or is partial
        output_layout: "flat" for legacy output or "project" for package layout

    Returns:
        True if successful
    """
    console.print(f"\n[bold cyan]🔄 Batch SAS to PySpark Migration[/bold cyan]")
    console.print(f"[cyan]Source Directory:[/cyan] {sas_directory}")
    console.print(f"[cyan]Output Directory:[/cyan] {output_dir}")
    console.print(f"[cyan]Pattern:[/cyan] {pattern}")
    console.print(f"[cyan]Recursive:[/cyan] {recursive}")
    console.print(f"[cyan]Max Workers:[/cyan] {max_workers}")
    console.print(f"[cyan]Provider:[/cyan] {provider or 'azure'}")
    console.print(f"[cyan]Model:[/cyan] {model or '(provider default)'}")
    console.print(f"[cyan]Max Chunk LLM Calls:[/cyan] {max_concurrent}")
    console.print(f"[cyan]Max LLM Retries:[/cyan] {max_retries}")
    console.print(f"[cyan]Max Completion Tokens:[/cyan] {max_tokens or '(env/default)'}")
    console.print(f"[cyan]Use RAG:[/cyan] {use_rag}\n")
    console.print(f"[cyan]Output Layout:[/cyan] {output_layout}\n")

    try:
        from graph_approach.migration.graph_migrator import GraphMigrator
        from graph_approach.migration.batch_migrator import BatchMigrator

        # Initialize migrator
        with console.status("[cyan]Initializing migrator...[/cyan]", spinner="dots"):
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
            batch_migrator = BatchMigrator(
                migrator=migrator,
                max_workers=max_workers,
                continue_on_error=continue_on_error
            )

        console.print("[green]✓[/green] Migrator initialized\n")

        # Discover files
        console.print("[cyan]Discovering SAS files...[/cyan]")
        sas_files = batch_migrator.discover_sas_files(
            sas_directory,
            pattern,
            recursive
        )

        if not sas_files:
            console.print(f"[yellow]⚠[/yellow] No SAS files found matching pattern: {pattern}")
            if not recursive:
                nested_count, nested_examples = _find_nested_sas_files(sas_directory, pattern)
                if nested_count:
                    console.print(
                        f"[yellow]ℹ[/yellow] Found {nested_count} matching SAS file(s) in subdirectories. "
                        "Use --recursive or point the command at the nested directory."
                    )
                    console.print("[cyan]Examples:[/cyan]")
                    for nested_file in nested_examples:
                        console.print(f"  {nested_file.relative_to(sas_directory)}")
            return False

        console.print(f"[green]✓[/green] Found {len(sas_files)} SAS file(s)\n")

        # List files
        console.print("[cyan]Files to migrate:[/cyan]")
        for i, sas_file in enumerate(sas_files, 1):
            relative_path = Path(sas_file).relative_to(sas_directory) if Path(sas_file).is_relative_to(sas_directory) else sas_file
            console.print(f"  {i}. {relative_path}")
        console.print("")

        # Migrate with progress bar
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]Starting Batch Migration[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Migrating files...",
                total=len(sas_files)
            )

            def progress_callback(file, index, total):
                progress.update(task, completed=index)

            batch_result = batch_migrator.migrate_batch(
                sas_directory=sas_directory,
                output_dir=output_dir,
                pattern=pattern,
                recursive=recursive,
                visualize=False,
                progress_callback=progress_callback,
                output_layout=output_layout,
                package_name=package_name,
            )

        # Display results
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]Batch Migration Complete[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

        # Statistics
        success_rate = 0
        if batch_result.total_files > 0:
            success_rate = (batch_result.successful_files / batch_result.total_files) * 100

        console.print(f"[cyan]Total Files:[/cyan] {batch_result.total_files}")
        console.print(f"[green]✓ Successful:[/green] {batch_result.successful_files}")

        if batch_result.failed_files > 0:
            console.print(f"[red]✗ Failed:[/red] {batch_result.failed_files}")

        console.print(f"[cyan]Success Rate:[/cyan] {success_rate:.1f}%")
        console.print(f"[cyan]Total Chunks:[/cyan] {batch_result.total_chunks_converted}/{batch_result.total_chunks}")
        console.print(f"[cyan]Total Time:[/cyan] {batch_result.total_execution_time:.2f}s\n")

        # Show errors
        if batch_result.failed_files > 0:
            console.print("[bold red]Failed Files:[/bold red]")
            for file_path, errors in batch_result.errors.items():
                console.print(f"  [red]✗[/red] {Path(file_path).name}")
                for error in errors[:2]:  # Show first 2 errors
                    console.print(f"    {error}")
            console.print("")

        # Generate summary report
        if generate_summary:
            console.print("[cyan]Generating batch summary report...[/cyan]")
            summary_path = Path(output_dir) / "batch_summary.md"
            batch_migrator.generate_batch_summary(batch_result, str(summary_path))
            console.print(f"[green]✓[/green] Summary saved: {summary_path}\n")

        # Generate Python package structure
        if (
            create_package
            and output_layout == "flat"
            and PackageGenerator
            and batch_result.successful_files > 0
        ):
            console.print("[cyan]Generating Python package structure...[/cyan]")
            try:
                # Get all directories that need __init__.py
                package_dirs = ["."]
                for root, dirs, files in os.walk(output_dir):
                    for d in dirs:
                        if d not in ["__pycache__", ".git"]:
                            rel_path = str(Path(root).relative_to(output_dir) / d)
                            package_dirs.append(rel_path)

                # Create package generator
                pkg_gen = PackageGenerator(package_name=package_name)

                # Generate package files
                migration_summary = {
                    "Total Files": batch_result.total_files,
                    "Successful": batch_result.successful_files,
                    "Failed": batch_result.failed_files,
                    "Total Chunks": batch_result.total_chunks,
                    "Chunks Converted": batch_result.total_chunks_converted,
                    "Execution Time": f"{batch_result.total_execution_time:.2f}s"
                }

                created_files = pkg_gen.generate_full_package(
                    output_dir,
                    package_dirs,
                    batch_result.total_files,
                    migration_summary
                )

                console.print(f"[green]✓[/green] Generated {len(created_files)} package files:")
                for file_type in list(created_files.keys())[:5]:  # Show first 5
                    console.print(f"    • {file_type}")
                if len(created_files) > 5:
                    console.print(f"    • ... and {len(created_files) - 5} more")
                console.print("")

            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Warning: Package generation failed: {e}\n")
        elif create_package and output_layout == "project":
            console.print(
                "[yellow]⚠[/yellow] --create-package is ignored for project layout; "
                "project layout already generates package metadata.\n"
            )

        # Final status
        if batch_result.failed_files == 0:
            console.print("[bold green]✓ All files migrated successfully![/bold green]")
            return True
        elif batch_result.successful_files > 0:
            console.print("[bold yellow]⚠ Batch completed with some failures[/bold yellow]")
            return not strict_exit_code
        else:
            console.print("[bold red]✗ Batch migration failed[/bold red]")
            return False

    except Exception as e:
        console.print(f"\n[bold red]✗ Batch migration failed:[/bold red]")
        console.print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Batch migrate multiple SAS files to PySpark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all SAS files in directory
  python -m graph_approach.cli.migrate_batch example_sas -o output

  # Recursive with 8 parallel workers
  python -m graph_approach.cli.migrate_batch ./src -o output --recursive --parallel 8

  # Custom pattern with error handling
  python -m graph_approach.cli.migrate_batch ./sas_files -o output \\
      --pattern "*.sas" --continue-on-error --summary

  # OpenRouter
  python -m graph_approach.cli.migrate_batch ./sas_files -o output \\
      --provider openrouter --model qwen/qwen-2.5-coder-32b-instruct

Features:
  - Parallel processing for faster migration
  - Progress tracking with rich progress bars
  - Aggregated summary reports
  - Error handling and recovery
        """
    )

    parser.add_argument(
        "sas_directory",
        help="Directory containing SAS files"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        required=True,
        help="Output directory for migrated files"
    )
    parser.add_argument(
        "-p", "--pattern",
        default="*.sas",
        help="File pattern to match (default: *.sas)"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search subdirectories recursively"
    )
    parser.add_argument(
        "-j", "--parallel",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=True,
        help="Continue if individual files fail (default: True)"
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop batch migration on first error"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=True,
        help="Generate batch summary report (default: True)"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip batch summary report"
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
        "--no-rag",
        action="store_true",
        help="Disable RAG (Retrieval-Augmented Generation)"
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
        help="Maximum concurrent chunk-level LLM calls per file (default: 5)"
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
        help="Do not write .py output for files with failed chunks"
    )
    parser.add_argument(
        "--strict-exit-code",
        action="store_true",
        help="Exit non-zero if any file fails or is partial"
    )
    parser.add_argument(
        "--create-package",
        action="store_true",
        help="Generate Python package structure (setup.py, __init__.py, etc.)"
    )
    parser.add_argument(
        "--output-layout",
        choices=["flat", "project"],
        default="flat",
        help="Output layout: flat legacy files or generated PySpark project (default: flat)",
    )
    parser.add_argument(
        "--package-name",
        default="sas_migration",
        help="Name of the Python package to generate (default: sas_migration)"
    )

    args = parser.parse_args()

    # Validate directory
    if not Path(args.sas_directory).exists():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {args.sas_directory}")
        sys.exit(1)

    # Handle stop-on-error override
    continue_on_error = not args.stop_on_error

    # Handle summary override
    generate_summary = not args.no_summary

    # Migrate
    success = migrate_batch(
        sas_directory=args.sas_directory,
        output_dir=args.output_dir,
        pattern=args.pattern,
        recursive=args.recursive,
        max_workers=args.parallel,
        continue_on_error=continue_on_error,
        generate_summary=generate_summary,
        model=args.model,
        use_rag=not args.no_rag,
        api_key=args.api_key,
        endpoint=args.endpoint,
        provider=args.provider,
        base_url=args.base_url,
        max_concurrent=args.max_concurrent,
        max_retries=args.max_retries,
        max_tokens=args.max_tokens,
        allow_partial_output=not args.no_partial_output,
        strict_exit_code=args.strict_exit_code,
        create_package=args.create_package,
        package_name=args.package_name,
        output_layout=args.output_layout,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
