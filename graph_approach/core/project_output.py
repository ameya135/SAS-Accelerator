"""
Project output generation for batch SAS migrations.

This module turns per-file migration results into an importable PySpark project
layout. It is intentionally deterministic: every placement decision is based on
source paths, filenames, and simple SAS signals, then written to a manifest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional


_IDENTIFIER_RE = re.compile(r"[^0-9a-zA-Z_]+")
_INCLUDE_RE = re.compile(
    r"%include\s+(?:\([^)]*\)\s*)?['\"]([^'\"]+\.sas)['\"]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProjectFilePlan:
    """Resolved output placement for one SAS source file."""

    sas_path: Path
    source_relative_path: Path
    module_relative_path: Path
    artifact_relative_dir: Path
    import_path: str
    classification: str
    stage: Optional[str]
    project_name: Optional[str]

    @property
    def module_name(self) -> str:
        return self.module_relative_path.with_suffix("").as_posix().replace("/", ".")


class ProjectOutputGenerator:
    """Generate package scaffolding, module wrappers, runner, and manifest."""

    STAGE_SIGNALS = {
        "extract": ("extract", "input", "ingest", "read", "source"),
        "transform": ("transform", "clean", "merge", "join", "rule", "derive"),
        "load": ("load", "write", "target", "mart", "publish"),
        "score": ("score", "model", "risk"),
        "report": ("report", "summary", "print", "freq", "means"),
    }

    def __init__(self, source_root: str, output_root: str, package_name: str):
        self.source_root = Path(source_root).resolve()
        self.output_root = Path(output_root)
        self.package_name = self._sanitize_identifier(package_name)
        self.src_root = self.output_root / "src"
        self.package_root = self.src_root / self.package_name
        self.artifacts_root = self.output_root / "artifacts"

    def build_plans(self, sas_files: Iterable[Path]) -> List[ProjectFilePlan]:
        """Return deterministic project placement for SAS files."""
        plans = [self._build_plan(Path(sas_file)) for sas_file in sas_files]
        plans = self._resolve_module_collisions(plans)
        return sorted(plans, key=lambda plan: plan.source_relative_path.as_posix())

    def code_dir_for(self, plan: ProjectFilePlan) -> Path:
        """Directory where the converted Python module should be written."""
        return self.package_root / plan.module_relative_path.parent

    def artifact_dir_for(self, plan: ProjectFilePlan) -> Path:
        """Directory where non-code migration artifacts should be written."""
        return self.artifacts_root / plan.artifact_relative_dir

    def finalize(
        self,
        plans: List[ProjectFilePlan],
        migration_summary: Optional[Dict[str, object]] = None,
    ) -> None:
        """Create package files after per-file migration outputs are written."""
        self._create_package_dirs(plans)
        for plan in plans:
            self.wrap_module(plan)
        self._write_runtime()
        self._write_context()
        self._write_runner(plans)
        self._write_pyproject()
        self._write_readme(plans, migration_summary or {})
        self._write_manifest(plans)

    def wrap_module(self, plan: ProjectFilePlan) -> None:
        """Wrap a generated script in the standard file-level run boundary."""
        module_path = self.package_root / plan.module_relative_path
        if not module_path.exists():
            return

        original = module_path.read_text(encoding="utf-8")
        if re.search(r"^\s*def\s+run\s*\(\s*spark\s*,\s*context\s*\)", original, re.MULTILINE):
            return

        indented = "\n".join(
            f"    {line}" if line.strip() else "" for line in original.splitlines()
        )
        wrapped = (
            '"""Migrated PySpark module generated from SAS."""\n\n'
            "def run(spark, context):\n"
            f"    \"\"\"Run migrated logic from {plan.source_relative_path.as_posix()}.\"\"\"\n"
            f"{indented}\n"
            "    return context\n"
        )
        module_path.write_text(wrapped, encoding="utf-8")

    def _build_plan(self, sas_file: Path) -> ProjectFilePlan:
        sas_path = sas_file.resolve()
        rel_path = self._relative_to_source(sas_path)
        sas_code = sas_path.read_text(encoding="utf-8", errors="replace")
        stem = self._sanitize_identifier(sas_path.stem)
        classification = self._classify_file(rel_path, sas_code)
        stage = self._infer_stage(rel_path, sas_code) if classification == "project" else None
        project_name = self._infer_project_name(rel_path) if classification == "project" else None

        if classification == "macro":
            module_rel = Path("macros") / f"{stem}.py"
            artifact_rel = Path("macros")
        elif classification == "common":
            module_rel = Path("common") / f"{stem}.py"
            artifact_rel = Path("common")
        else:
            project_parts = [project_name or self._sanitize_identifier(self.source_root.name)]
            if stage:
                project_parts.append(stage)
            module_rel = Path("projects", *project_parts, f"{stem}.py")
            artifact_rel = Path("projects", *project_parts)

        import_path = ".".join(
            [self.package_name, *module_rel.with_suffix("").parts]
        )
        return ProjectFilePlan(
            sas_path=sas_path,
            source_relative_path=rel_path,
            module_relative_path=module_rel,
            artifact_relative_dir=artifact_rel,
            import_path=import_path,
            classification=classification,
            stage=stage,
            project_name=project_name,
        )

    def _resolve_module_collisions(
        self, plans: List[ProjectFilePlan]
    ) -> List[ProjectFilePlan]:
        """Preserve distinct outputs when inferred placement would collide."""
        by_module: Dict[Path, List[ProjectFilePlan]] = {}
        for plan in plans:
            by_module.setdefault(plan.module_relative_path, []).append(plan)

        resolved: List[ProjectFilePlan] = []
        for plan in plans:
            duplicates = by_module[plan.module_relative_path]
            if len(duplicates) == 1:
                resolved.append(plan)
                continue

            rel_without_suffix = plan.source_relative_path.with_suffix("")
            module_rel = plan.module_relative_path.parent / rel_without_suffix.with_suffix(
                ".py"
            )
            artifact_rel = plan.artifact_relative_dir / rel_without_suffix.parent
            import_path = ".".join(
                [self.package_name, *module_rel.with_suffix("").parts]
            )
            resolved.append(
                replace(
                    plan,
                    module_relative_path=module_rel,
                    artifact_relative_dir=artifact_rel,
                    import_path=import_path,
                )
            )

        return resolved

    def _relative_to_source(self, sas_path: Path) -> Path:
        try:
            return sas_path.relative_to(self.source_root)
        except ValueError:
            return Path(sas_path.name)

    def _classify_file(self, rel_path: Path, sas_code: str) -> str:
        lowered_name = rel_path.as_posix().lower()
        lowered_code = sas_code.lower()
        macro_defs = len(re.findall(r"%macro\b", lowered_code))
        data_or_proc = len(re.findall(r"\b(?:data|proc)\b", lowered_code))

        if macro_defs > 0 and macro_defs >= data_or_proc:
            return "macro"

        setup_signals = (
            "common",
            "setup",
            "config",
            "option",
            "libname",
            "filename",
            "schema",
            "catalog",
        )
        code_setup_signals = (
            "libname ",
            "filename ",
            "options ",
            "%let ",
        )
        if any(signal in lowered_name for signal in setup_signals):
            return "common"
        if any(signal in lowered_code for signal in code_setup_signals) and data_or_proc == 0:
            return "common"

        return "project"

    def _infer_project_name(self, rel_path: Path) -> str:
        if len(rel_path.parts) > 1:
            return self._sanitize_identifier(rel_path.parts[0])
        return self._sanitize_identifier(self.source_root.name)

    def _infer_stage(self, rel_path: Path, sas_code: str) -> Optional[str]:
        stem = rel_path.stem.lower()
        if any(signal in stem for signal in ("run", "main", "driver", "pipeline", "job")):
            return None
        haystack = f"{rel_path.as_posix()} {sas_code}".lower()
        for stage, signals in self.STAGE_SIGNALS.items():
            if any(signal in haystack for signal in signals):
                return stage
        return None

    def _create_package_dirs(self, plans: List[ProjectFilePlan]) -> None:
        dirs = {
            self.package_root,
            self.package_root / "macros",
            self.package_root / "common",
            self.package_root / "projects",
        }
        dirs.update((self.package_root / plan.module_relative_path.parent) for plan in plans)

        for directory in sorted(dirs):
            directory.mkdir(parents=True, exist_ok=True)
            init_path = directory / "__init__.py"
            if directory == self.package_root or self.package_root in directory.parents:
                init_path.write_text('"""Generated SAS migration package."""\n', encoding="utf-8")

    def _write_runtime(self) -> None:
        content = '''"""Spark runtime helpers for migrated SAS jobs."""

from pyspark.sql import SparkSession


def get_spark(app_name="SAS Migration"):
    """Create or return the active SparkSession."""
    return SparkSession.builder.appName(app_name).getOrCreate()
'''
        (self.package_root / "runtime.py").write_text(content, encoding="utf-8")

    def _write_context(self) -> None:
        content = '''"""Shared runtime context for migrated SAS jobs."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MigrationContext:
    """State shared across migrated modules."""

    project_root: Path = field(default_factory=lambda: Path.cwd())
    datasets: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
'''
        (self.package_root / "context.py").write_text(content, encoding="utf-8")

    def _write_runner(self, plans: List[ProjectFilePlan]) -> None:
        ordered = self._ordered_plans(plans)
        sequence = [
            f'    ("{plan.source_relative_path.as_posix()}", "{plan.import_path}"),'
            for plan in ordered
        ]
        content = f'''"""Entrypoint for the generated SAS migration project."""

from importlib import import_module

from .context import MigrationContext
from .runtime import get_spark


RUN_SEQUENCE = [
{chr(10).join(sequence)}
]


def run(spark=None, context=None):
    """Run migrated modules in inferred execution order."""
    spark = spark or get_spark()
    context = context or MigrationContext()
    for _source_file, module_path in RUN_SEQUENCE:
        module = import_module(module_path)
        context = module.run(spark, context) or context
    return context


if __name__ == "__main__":
    run()
'''
        (self.package_root / "runner.py").write_text(content, encoding="utf-8")

    def _ordered_plans(self, plans: List[ProjectFilePlan]) -> List[ProjectFilePlan]:
        by_abs = {plan.sas_path.resolve(): plan for plan in plans}
        by_parent_and_name = {
            (plan.sas_path.parent.resolve(), plan.sas_path.name.lower()): plan
            for plan in plans
        }
        ordered: List[ProjectFilePlan] = []
        seen: set[Path] = set()

        for plan in plans:
            for include in self._extract_includes(plan.sas_path):
                include_plan = by_parent_and_name.get(
                    (plan.sas_path.parent.resolve(), Path(include).name.lower())
                )
                if include_plan and include_plan.sas_path not in seen:
                    ordered.append(include_plan)
                    seen.add(include_plan.sas_path)

        for plan in plans:
            if plan.sas_path not in seen:
                ordered.append(plan)
                seen.add(plan.sas_path)

        return ordered

    def _extract_includes(self, sas_path: Path) -> List[str]:
        try:
            code = sas_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        return _INCLUDE_RE.findall(code)

    def _write_pyproject(self) -> None:
        content = f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{self.package_name.replace("_", "-")}"
version = "0.1.0"
description = "PySpark code migrated from SAS"
requires-python = ">=3.9"
dependencies = [
    "pyspark>=3.0.0",
    "pandas>=1.0.0",
    "numpy>=1.18.0",
]

[project.scripts]
{self.package_name}-run = "{self.package_name}.runner:run"

[tool.setuptools.packages.find]
where = ["src"]
'''
        (self.output_root / "pyproject.toml").write_text(content, encoding="utf-8")

    def _write_readme(
        self, plans: List[ProjectFilePlan], migration_summary: Dict[str, object]
    ) -> None:
        lines = [
            f"# {self.package_name}",
            "",
            "Generated PySpark project migrated from SAS.",
            "",
            "## Run",
            "",
            "```bash",
            f"python -m {self.package_name}.runner",
            "```",
            "",
            "## Migration Summary",
            "",
        ]
        for key, value in migration_summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.extend(["", "## Modules", ""])
        for plan in plans:
            lines.append(
                f"- `{plan.source_relative_path.as_posix()}` -> `{plan.import_path}`"
            )
        lines.append("")
        (self.output_root / "README.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_manifest(self, plans: List[ProjectFilePlan]) -> None:
        manifest = {
            "package_name": self.package_name,
            "source_root": str(self.source_root),
            "files": [
                {
                    "source": plan.source_relative_path.as_posix(),
                    "module": plan.module_relative_path.as_posix(),
                    "artifact_dir": plan.artifact_relative_dir.as_posix(),
                    "import_path": plan.import_path,
                    "classification": plan.classification,
                    "stage": plan.stage,
                    "project_name": plan.project_name,
                }
                for plan in plans
            ],
        }
        (self.output_root / "migration_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _sanitize_identifier(value: str) -> str:
        sanitized = _IDENTIFIER_RE.sub("_", value.strip()).strip("_").lower()
        if not sanitized:
            return "module"
        if sanitized[0].isdigit():
            return f"_{sanitized}"
        return sanitized
