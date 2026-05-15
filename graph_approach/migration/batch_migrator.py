"""
Batch Migrator

Handles migration of multiple SAS files with parallel processing,
progress tracking, and aggregated reporting.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from graph_approach.migration.graph_migrator import GraphMigrator, MigrationResult
from graph_approach.core.project_output import ProjectOutputGenerator, ProjectFilePlan


@dataclass
class BatchMigrationResult:
    """Result of a batch migration"""
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_chunks_converted: int = 0
    total_chunks: int = 0
    total_execution_time: float = 0.0
    start_time: str = ""
    end_time: str = ""
    file_results: List[MigrationResult] = field(default_factory=list)
    errors: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "success_rate": f"{(self.successful_files/self.total_files*100):.1f}%" if self.total_files > 0 else "0%",
            "total_chunks_converted": self.total_chunks_converted,
            "total_chunks": self.total_chunks,
            "total_execution_time": self.total_execution_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "file_results": [r.to_dict() for r in self.file_results],
            "errors": self.errors
        }


class BatchMigrator:
    """
    Batch migrator for multiple SAS files

    Features:
    - File discovery with glob patterns
    - Parallel processing
    - Progress tracking
    - Aggregated reporting
    """

    def __init__(
        self,
        migrator: GraphMigrator,
        max_workers: int = 4,
        continue_on_error: bool = True
    ):
        """
        Initialize batch migrator

        Args:
            migrator: GraphMigrator instance
            max_workers: Number of parallel workers
            continue_on_error: Continue if individual files fail
        """
        self.migrator = migrator
        self.max_workers = max_workers
        self.continue_on_error = continue_on_error
        self._lock = threading.Lock()

    def discover_sas_files(
        self,
        directory: str,
        pattern: str = "*.sas",
        recursive: bool = False
    ) -> List[Path]:
        """
        Discover all SAS files in directory

        Args:
            directory: Directory to search
            pattern: File pattern (e.g., "*.sas")
            recursive: Search subdirectories recursively

        Returns:
            List of Path objects for SAS files
        """
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        if not directory_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Search for files
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))

        # Filter to only .sas files
        sas_files = [f for f in files if f.suffix.lower() == '.sas' and f.is_file()]

        return sorted(sas_files)

    def migrate_file_safe(
        self,
        sas_file: Path,
        output_dir: str,
        visualize: bool = False,
        artifact_dir: Optional[str] = None,
    ) -> MigrationResult:
        """
        Migrate a single file with error handling

        Args:
            sas_file: Path to SAS file
            output_dir: Output directory
            visualize: Whether to generate visualizations
            artifact_dir: Optional directory for non-code artifacts

        Returns:
            MigrationResult
        """
        try:
            result = self.migrator.migrate_file(
                sas_file_path=str(sas_file),
                output_dir=output_dir,
                visualize=visualize,
                artifact_dir=artifact_dir,
            )
            return result

        except Exception as e:
            # Create failed result
            result = MigrationResult(
                success=False,
                sas_file=str(sas_file),
                errors=[str(e)]
            )
            return result

    def migrate_batch(
        self,
        sas_directory: str,
        output_dir: str,
        pattern: str = "*.sas",
        recursive: bool = False,
        visualize: bool = False,
        progress_callback: Optional[callable] = None,
        output_layout: str = "flat",
        package_name: str = "sas_migrator",
    ) -> BatchMigrationResult:
        """
        Migrate all SAS files in directory

        Args:
            sas_directory: Directory containing SAS files
            output_dir: Output directory
            pattern: File pattern
            recursive: Search subdirectories
            visualize: Generate visualizations
            progress_callback: Optional callback(file, index, total) for progress
            output_layout: "flat" for legacy output or "project" for package layout
            package_name: Package name for project layout

        Returns:
            BatchMigrationResult
        """
        start_time = datetime.now()

        # Discover files
        sas_files = self.discover_sas_files(sas_directory, pattern, recursive)

        if not sas_files:
            raise ValueError(f"No SAS files found in {sas_directory} matching {pattern}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        if output_layout not in {"flat", "project"}:
            raise ValueError("output_layout must be 'flat' or 'project'")

        project_generator: Optional[ProjectOutputGenerator] = None
        plans_by_file: Dict[Path, ProjectFilePlan] = {}
        if output_layout == "project":
            project_generator = ProjectOutputGenerator(
                source_root=sas_directory,
                output_root=output_dir,
                package_name=package_name,
            )
            plans = project_generator.build_plans(sas_files)
            plans_by_file = {plan.sas_path: plan for plan in plans}

        # Initialize result
        batch_result = BatchMigrationResult(
            total_files=len(sas_files),
            start_time=start_time.isoformat()
        )

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {}
            for sas_file in sas_files:
                if project_generator:
                    plan = plans_by_file[sas_file.resolve()]
                    file_output_dir = str(project_generator.code_dir_for(plan))
                    artifact_dir = str(project_generator.artifact_dir_for(plan))
                else:
                    file_output_dir = output_dir
                    artifact_dir = None

                future = executor.submit(
                    self.migrate_file_safe,
                    sas_file,
                    file_output_dir,
                    visualize,
                    artifact_dir,
                )
                future_to_file[future] = sas_file

            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_file):
                sas_file = future_to_file[future]
                completed += 1

                try:
                    result = future.result()

                    # Update batch result (thread-safe)
                    with self._lock:
                        batch_result.file_results.append(result)

                        batch_result.total_chunks_converted += result.chunks_converted
                        batch_result.total_chunks += result.total_chunks

                        if result.success:
                            batch_result.successful_files += 1
                        else:
                            batch_result.failed_files += 1
                            batch_result.errors[str(sas_file)] = result.errors

                        batch_result.total_execution_time += result.execution_time

                    # Progress callback
                    if progress_callback:
                        progress_callback(sas_file, completed, len(sas_files))

                    # Stop on error if configured
                    if not self.continue_on_error and not result.success:
                        # Cancel remaining tasks
                        for f in future_to_file:
                            f.cancel()
                        break

                except Exception as e:
                    # Handle unexpected errors
                    with self._lock:
                        batch_result.failed_files += 1
                        batch_result.errors[str(sas_file)] = [str(e)]

                    if not self.continue_on_error:
                        for f in future_to_file:
                            f.cancel()
                        break

        end_time = datetime.now()
        batch_result.end_time = end_time.isoformat()

        if project_generator:
            migration_summary = {
                "Total Files": batch_result.total_files,
                "Successful": batch_result.successful_files,
                "Failed": batch_result.failed_files,
                "Total Chunks": batch_result.total_chunks,
                "Chunks Converted": batch_result.total_chunks_converted,
                "Execution Time": f"{batch_result.total_execution_time:.2f}s",
            }
            project_generator.finalize(list(plans_by_file.values()), migration_summary)

        return batch_result

    def generate_batch_summary(
        self,
        batch_result: BatchMigrationResult,
        output_path: str
    ) -> None:
        """
        Generate batch migration summary report

        Args:
            batch_result: Batch migration result
            output_path: Path for summary report
        """
        lines = []

        lines.append("# BATCH MIGRATION SUMMARY")
        lines.append("=" * 80)
        lines.append("")

        # Overall Statistics
        lines.append("## Overall Statistics")
        lines.append("")
        lines.append(f"- **Total Files**: {batch_result.total_files}")
        lines.append(f"- **Successful**: {batch_result.successful_files}")
        lines.append(f"- **Failed**: {batch_result.failed_files}")

        success_rate = 0
        if batch_result.total_files > 0:
            success_rate = (batch_result.successful_files / batch_result.total_files) * 100
        lines.append(f"- **Success Rate**: {success_rate:.1f}%")
        lines.append("")

        lines.append(f"- **Total Chunks Converted**: {batch_result.total_chunks_converted}/{batch_result.total_chunks}")
        lines.append(f"- **Total Execution Time**: {batch_result.total_execution_time:.2f}s")
        lines.append("")

        # Timing
        lines.append("## Timing")
        lines.append("")
        lines.append(f"- **Start Time**: {batch_result.start_time}")
        lines.append(f"- **End Time**: {batch_result.end_time}")
        lines.append("")

        # Failed Files
        if batch_result.failed_files > 0:
            lines.append("## Failed Files")
            lines.append("")
            for file_path, errors in batch_result.errors.items():
                lines.append(f"### {file_path}")
                lines.append("")
                lines.append("**Errors:**")
                for error in errors:
                    lines.append(f"- {error}")
                lines.append("")

        # Successful Files
        if batch_result.successful_files > 0:
            lines.append("## Successful Files")
            lines.append("")
            lines.append("| File | Chunks | Warnings | Time (s) |")
            lines.append("|------|--------|----------|----------|")

            for result in batch_result.file_results:
                if result.success:
                    file_name = Path(result.sas_file).name
                    chunks_str = f"{result.chunks_converted}/{result.total_chunks}"
                    warnings_count = len(result.warnings)
                    time_str = f"{result.execution_time:.2f}"
                    lines.append(f"| {file_name} | {chunks_str} | {warnings_count} | {time_str} |")

            lines.append("")

        # Write summary
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
