import json
import sys
import types
from pathlib import Path

if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")
    for name in [
        "APIConnectionError",
        "APIStatusError",
        "APITimeoutError",
        "AsyncAzureOpenAI",
        "AsyncOpenAI",
        "AzureOpenAI",
        "OpenAI",
    ]:
        setattr(fake_openai, name, type(name, (Exception,), {}))
    sys.modules["openai"] = fake_openai
if "dotenv" not in sys.modules:
    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = fake_dotenv

from graph_approach.migration.batch_migrator import BatchMigrator
from graph_approach.migration.graph_migrator import MigrationResult


class FakeMigrator:
    def migrate_file(
        self,
        sas_file_path,
        output_dir,
        visualize=False,
        artifact_dir=None,
    ):
        sas_path = Path(sas_file_path)
        output_path = Path(output_dir)
        artifacts_path = Path(artifact_dir or output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        artifacts_path.mkdir(parents=True, exist_ok=True)

        code = (
            "from pyspark.sql import functions as F\n\n"
            f"spark.table('{sas_path.stem}')\n"
        )
        result = MigrationResult(
            success=True,
            sas_file=str(sas_path),
            pyspark_code=code,
            mapping=f"mapping for {sas_path.name}",
            chunks_converted=1,
            total_chunks=1,
        )

        py_path = output_path / f"{sas_path.stem}.py"
        mapping_path = artifacts_path / f"{sas_path.stem}_mapping.txt"
        validation_path = artifacts_path / f"{sas_path.stem}_validation.txt"
        result_path = artifacts_path / f"{sas_path.stem}_result.json"

        py_path.write_text(code, encoding="utf-8")
        mapping_path.write_text(result.mapping, encoding="utf-8")
        validation_path.write_text("validation", encoding="utf-8")
        result.metadata["output_files"] = {
            "pyspark": str(py_path),
            "mapping": str(mapping_path),
            "validation": str(validation_path),
            "result": str(result_path),
        }
        result_path.write_text(json.dumps(result.to_dict()), encoding="utf-8")
        return result


def test_flat_output_layout_remains_default(tmp_path):
    source_dir = tmp_path / "sas"
    source_dir.mkdir()
    (source_dir / "job.sas").write_text("data out; run;\n", encoding="utf-8")
    output_dir = tmp_path / "out"

    migrator = BatchMigrator(FakeMigrator(), max_workers=1)
    migrator.migrate_batch(str(source_dir), str(output_dir))

    assert (output_dir / "job.py").exists()
    assert not (output_dir / "src").exists()


def test_project_output_creates_package_and_separates_artifacts(tmp_path):
    source_dir = tmp_path / "sas_codebase"
    project_dir = source_dir / "financial_etl"
    project_dir.mkdir(parents=True)
    (project_dir / "common_setup.sas").write_text(
        "libname raw '/data/raw'; options mprint;\n", encoding="utf-8"
    )
    (project_dir / "run_etl.sas").write_text(
        '%include "common_setup.sas";\n%include "extract_transactions.sas";\n',
        encoding="utf-8",
    )
    (project_dir / "extract_transactions.sas").write_text(
        "data staging.transactions; set raw.transactions; run;\n", encoding="utf-8"
    )
    output_dir = tmp_path / "out"

    migrator = BatchMigrator(FakeMigrator(), max_workers=1)
    migrator.migrate_batch(
        str(source_dir),
        str(output_dir),
        recursive=True,
        output_layout="project",
        package_name="sas_migrator",
    )

    package_root = output_dir / "src" / "sas_migrator"
    assert (output_dir / "pyproject.toml").exists()
    assert (package_root / "runtime.py").exists()
    assert (package_root / "context.py").exists()
    assert (package_root / "runner.py").exists()
    assert (package_root / "common" / "common_setup.py").exists()
    assert (
        package_root
        / "projects"
        / "financial_etl"
        / "run_etl.py"
    ).exists()
    assert (
        package_root
        / "projects"
        / "financial_etl"
        / "extract"
        / "extract_transactions.py"
    ).exists()
    assert (
        output_dir
        / "artifacts"
        / "common"
        / "common_setup_mapping.txt"
    ).exists()
    assert not (package_root / "common" / "common_setup_mapping.txt").exists()

    module_text = (
        package_root
        / "projects"
        / "financial_etl"
        / "extract"
        / "extract_transactions.py"
    ).read_text(encoding="utf-8")
    assert "def run(spark, context):" in module_text

    manifest = json.loads((output_dir / "migration_manifest.json").read_text())
    assert manifest["package_name"] == "sas_migrator"
    assert any(item["classification"] == "common" for item in manifest["files"])
    assert any(item["stage"] == "extract" for item in manifest["files"])


def test_project_output_avoids_same_stem_collisions(tmp_path):
    source_dir = tmp_path / "sas_codebase"
    (source_dir / "project_a").mkdir(parents=True)
    (source_dir / "project_b").mkdir()
    (source_dir / "project_a" / "job.sas").write_text("data a; run;\n")
    (source_dir / "project_b" / "job.sas").write_text("data b; run;\n")
    output_dir = tmp_path / "out"

    migrator = BatchMigrator(FakeMigrator(), max_workers=1)
    migrator.migrate_batch(
        str(source_dir),
        str(output_dir),
        recursive=True,
        output_layout="project",
        package_name="sas_migrator",
    )

    assert (
        output_dir / "src" / "sas_migrator" / "projects" / "project_a" / "job.py"
    ).exists()
    assert (
        output_dir / "src" / "sas_migrator" / "projects" / "project_b" / "job.py"
    ).exists()
    assert (
        output_dir / "artifacts" / "projects" / "project_a" / "job_result.json"
    ).exists()
    assert (
        output_dir / "artifacts" / "projects" / "project_b" / "job_result.json"
    ).exists()


def test_project_runner_uses_include_order_before_fallback(tmp_path):
    source_dir = tmp_path / "sas_codebase"
    project_dir = source_dir / "financial_etl"
    project_dir.mkdir(parents=True)
    (project_dir / "run_etl.sas").write_text(
        '%include "b_transform.sas";\n%include "a_extract.sas";\n',
        encoding="utf-8",
    )
    (project_dir / "a_extract.sas").write_text("data a; run;\n", encoding="utf-8")
    (project_dir / "b_transform.sas").write_text("data b; set a; run;\n", encoding="utf-8")
    (project_dir / "z_report.sas").write_text("proc print data=b; run;\n", encoding="utf-8")
    output_dir = tmp_path / "out"

    migrator = BatchMigrator(FakeMigrator(), max_workers=1)
    migrator.migrate_batch(
        str(source_dir),
        str(output_dir),
        recursive=True,
        output_layout="project",
        package_name="sas_migrator",
    )

    runner = (
        output_dir / "src" / "sas_migrator" / "runner.py"
    ).read_text(encoding="utf-8")
    b_index = runner.index("b_transform")
    a_index = runner.index("a_extract")
    z_index = runner.index("z_report")
    assert b_index < a_index < z_index
