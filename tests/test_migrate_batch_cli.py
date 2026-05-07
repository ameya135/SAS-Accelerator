from graph_approach.cli.migrate_batch import _find_nested_sas_files


def test_find_nested_sas_files_reports_only_nested_sas_files(tmp_path):
    top_level = tmp_path / "top_level.sas"
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_sas = nested / "macro.sas"
    nested_text = nested / "notes.txt"

    top_level.write_text("data top; run;\n")
    nested_sas.write_text("%macro example; %mend;\n")
    nested_text.write_text("not sas\n")

    count, examples = _find_nested_sas_files(str(tmp_path))

    assert count == 1
    assert examples == [nested_sas]


def test_find_nested_sas_files_respects_limit(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    for index in range(3):
        (nested / f"file_{index}.sas").write_text("data x; run;\n")

    count, examples = _find_nested_sas_files(str(tmp_path), limit=2)

    assert count == 3
    assert len(examples) == 2
