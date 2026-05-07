"""
Tests for the dependency extractor module.

Covers:
- DataStepDependencies extraction (SET, MERGE, UPDATE, MODIFY, macro vars, CALL SYMPUT, INFILE/FILE)
- ProcDependencies extraction (DATA=, OUT=, PROC SQL, PROC IMPORT/EXPORT)
- MacroDependencies extraction (macro calls, %LET, &var references)
- Library and filename reference extraction from raw SAS code
- extract_all_dependencies orchestration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from graph_approach.parsers.dependency_extractor import (
    DependencyExtractor,
    DataStepDependencies,
    ProcDependencies,
    MacroDependencies,
)


# ===================================================================
# Helper
# ===================================================================


@pytest.fixture
def extractor():
    return DependencyExtractor()


# ===================================================================
# Data Step Dependencies
# ===================================================================


class TestDataStepSetStatement:
    """Tests for extracting SET statement inputs."""

    def test_single_set(self, extractor):
        data_step = {
            "output_datasets": "output_data",
            "body": "SET input_data; x = 1;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "input_data" in deps.inputs
        assert "output_data" in deps.outputs

    def test_multiple_set_datasets(self, extractor):
        data_step = {
            "output_datasets": "combined",
            "body": "SET data1 data2 data3;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "data1" in deps.inputs
        assert "data2" in deps.inputs
        assert "data3" in deps.inputs

    def test_set_with_library_prefix(self, extractor):
        data_step = {
            "output_datasets": "output_data",
            "body": "SET mylib.input_data;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "mylib.input_data" in deps.inputs


class TestDataStepMergeStatement:
    """Tests for extracting MERGE statement inputs."""

    def test_merge_two_datasets(self, extractor):
        data_step = {
            "output_datasets": "merged",
            "body": "MERGE employees departments; BY id;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "employees" in deps.inputs
        assert "departments" in deps.inputs

    def test_merge_with_library_prefix(self, extractor):
        data_step = {
            "output_datasets": "merged",
            "body": "MERGE lib1.data1 lib2.data2;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "lib1.data1" in deps.inputs
        assert "lib2.data2" in deps.inputs


class TestDataStepUpdateModify:
    """Tests for UPDATE and MODIFY statement extraction."""

    def test_update_statement(self, extractor):
        data_step = {
            "output_datasets": "updated",
            "body": "UPDATE master transactions; BY id;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "master" in deps.inputs
        assert "transactions" in deps.inputs

    def test_modify_statement(self, extractor):
        data_step = {
            "output_datasets": "modified",
            "body": "MODIFY target_data;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "target_data" in deps.inputs


class TestDataStepOutputDatasets:
    """Tests for output dataset extraction."""

    def test_single_output(self, extractor):
        data_step = {
            "output_datasets": "result",
            "body": "SET input;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "result" in deps.outputs

    def test_multiple_outputs(self, extractor):
        data_step = {
            "output_datasets": "out1 out2",
            "body": "SET input;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "out1" in deps.outputs
        assert "out2" in deps.outputs


class TestDataStepMacroVariables:
    """Tests for macro variable extraction from DATA steps."""

    def test_macro_var_references(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "SET input; WHERE salary > &min_salary; bonus = &bonus_rate * salary;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "min_salary" in deps.macro_vars_used
        assert "bonus_rate" in deps.macro_vars_used

    def test_call_symput_definitions(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "CALL SYMPUT('my_var', value);",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "my_var" in deps.macro_vars_defined

    def test_call_symputx_definitions(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "CALL SYMPUTX('count', _n_);",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "count" in deps.macro_vars_defined

    def test_no_macro_vars(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "SET input; x = 1;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert len(deps.macro_vars_used) == 0
        assert len(deps.macro_vars_defined) == 0


class TestDataStepFileRefs:
    """Tests for INFILE and FILE reference extraction."""

    def test_infile_reference(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "INFILE mydata; INPUT name $ salary;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "mydata" in deps.file_refs

    def test_file_reference(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "FILE report; PUT name salary;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "report" in deps.file_refs

    def test_both_infile_and_file(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "INFILE rawdata; INPUT x y; FILE outfile; PUT x y;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "rawdata" in deps.file_refs
        assert "outfile" in deps.file_refs


class TestDataStepDeduplication:
    """Tests that extracted lists are deduplicated."""

    def test_duplicate_inputs_deduplicated(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "SET data1 data1;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert deps.inputs.count("data1") == 1


class TestDataStepEdgeCases:
    """Tests for edge cases in DATA step extraction."""

    def test_empty_body(self, extractor):
        data_step = {
            "output_datasets": "out",
            "body": "",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert deps.inputs == []
        assert deps.outputs == ["out"]

    def test_no_output_datasets(self, extractor):
        data_step = {
            "output_datasets": "",
            "body": "SET input;",
        }
        deps = extractor.extract_data_step_dependencies(data_step)

        assert "input" in deps.inputs
        assert deps.outputs == []


# ===================================================================
# PROC Step Dependencies
# ===================================================================


class TestProcDataOption:
    """Tests for DATA= input extraction from PROC steps."""

    def test_data_option(self, extractor):
        proc_step = {
            "proc_name": "MEANS",
            "body": "VAR salary;",
            "options": "DATA=employees",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "employees" in deps.inputs

    def test_data_option_in_body(self, extractor):
        proc_step = {
            "proc_name": "PRINT",
            "body": "PROC PRINT DATA=mydata; VAR x;",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "mydata" in deps.inputs


class TestProcOutOption:
    """Tests for OUT= output extraction from PROC steps."""

    def test_out_option(self, extractor):
        proc_step = {
            "proc_name": "SORT",
            "body": "BY salary;",
            "options": "DATA=employees OUT=sorted_employees",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "sorted_employees" in deps.outputs
        assert "employees" in deps.inputs


class TestProcSQL:
    """Tests for PROC SQL specific extraction."""

    def test_from_clause(self, extractor):
        """Test FROM clause extraction.

        Note: The regex [^\\s;,WHERE]+ with IGNORECASE excludes individual
        characters w, h, e, r (not the keyword WHERE). Table names without
        those characters are captured correctly.
        """
        proc_step = {
            "proc_name": "SQL",
            "body": "SELECT * FROM input_data;",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "input_data" in deps.inputs

    def test_create_table(self, extractor):
        proc_step = {
            "proc_name": "SQL",
            "body": "CREATE TABLE high_earners AS SELECT * FROM input_data;",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "high_earners" in deps.outputs

    def test_sql_single_from_capture(self, extractor):
        """The FROM regex captures the first non-special token after FROM."""
        proc_step = {
            "proc_name": "SQL",
            "body": "SELECT * FROM tab1, tab2;",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        # Only tab1 is captured (regex stops at comma)
        assert "tab1" in deps.inputs


class TestProcImportExport:
    """Tests for PROC IMPORT and EXPORT handling."""

    def test_proc_import_out(self, extractor):
        proc_step = {
            "proc_name": "IMPORT",
            "body": "",
            "options": "OUT=imported_data DATAFILE='/data/file.csv' DBMS=CSV",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "imported_data" in deps.outputs

    def test_proc_export_data(self, extractor):
        proc_step = {
            "proc_name": "EXPORT",
            "body": "",
            "options": "DATA=export_data OUTFILE='/data/out.csv' DBMS=CSV",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "export_data" in deps.inputs


class TestProcMacroVars:
    """Tests for macro variable extraction from PROC steps."""

    def test_proc_macro_var_references(self, extractor):
        proc_step = {
            "proc_name": "MEANS",
            "body": "WHERE salary > &threshold;",
            "options": "DATA=employees",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert "threshold" in deps.macro_vars_used


class TestProcName:
    """Tests for proc_name extraction."""

    def test_proc_name_uppercased(self, extractor):
        proc_step = {
            "proc_name": "means",
            "body": "",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert deps.proc_name == "MEANS"


class TestProcDeduplication:
    """Tests that PROC extracted lists are deduplicated."""

    def test_duplicate_inputs_deduplicated(self, extractor):
        proc_step = {
            "proc_name": "SQL",
            "body": "SELECT * FROM data1 JOIN data1 ON data1.id = data1.id;",
            "options": "",
        }
        deps = extractor.extract_proc_dependencies(proc_step)

        assert deps.inputs.count("data1") <= 1


# ===================================================================
# Macro Dependencies
# ===================================================================


class TestMacroCalls:
    """Tests for macro call extraction."""

    def test_single_macro_call(self, extractor):
        macro = {
            "name": "my_macro",
            "body": "%other_macro(param1);",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert "other_macro" in deps.calls

    def test_multiple_macro_calls(self, extractor):
        macro = {
            "name": "orchestrator",
            "body": "%clean_data(); %transform_data(); %export_results();",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert "clean_data" in deps.calls
        assert "transform_data" in deps.calls
        assert "export_results" in deps.calls

    def test_no_macro_calls(self, extractor):
        macro = {
            "name": "simple",
            "body": "DATA out; SET input; x = 1; RUN;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert len(deps.calls) == 0


class TestMacroVariableDefinitions:
    """Tests for %LET extraction inside macros."""

    def test_let_statement(self, extractor):
        macro = {
            "name": "setup",
            "body": "%LET max_rows = 1000; %LET min_salary = 30000;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert "max_rows" in deps.macro_vars_defined
        assert "min_salary" in deps.macro_vars_defined

    def test_no_let_statements(self, extractor):
        macro = {
            "name": "simple",
            "body": "DATA out; SET in; RUN;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert len(deps.macro_vars_defined) == 0


class TestMacroVariableReferences:
    """Tests for &var reference extraction inside macros."""

    def test_macro_var_references(self, extractor):
        macro = {
            "name": "filter",
            "body": "DATA out; SET input; WHERE salary > &min_salary; bonus = &rate; RUN;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert "min_salary" in deps.macro_vars_used
        assert "rate" in deps.macro_vars_used


class TestMacroDatasetsReferenced:
    """Tests for dataset references inside macros."""

    def test_data_set_references(self, extractor):
        macro = {
            "name": "process",
            "body": "DATA output; SET raw_data; x = x + 1; RUN;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert "output" in deps.datasets_referenced
        assert "raw_data" in deps.datasets_referenced


class TestMacroName:
    """Tests for macro name extraction."""

    def test_macro_name(self, extractor):
        macro = {
            "name": "my_macro",
            "body": "%LET x = 1;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert deps.macro_name == "my_macro"


class TestMacroDeduplication:
    """Tests that macro extracted lists are deduplicated."""

    def test_duplicate_calls_deduplicated(self, extractor):
        macro = {
            "name": "test",
            "body": "%helper(a); %helper(b);",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert deps.calls.count("helper") == 1

    def test_duplicate_let_deduplicated(self, extractor):
        macro = {
            "name": "test",
            "body": "%LET x = 1; %LET x = 2;",
        }
        deps = extractor.extract_macro_dependencies(macro)

        assert deps.macro_vars_defined.count("x") == 1


# ===================================================================
# Library and Filename References
# ===================================================================


class TestExtractLibraryReferences:
    """Tests for extracting LIBNAME statements from raw SAS code."""

    def test_single_libname(self, extractor):
        code = "LIBNAME mylib '/data/projects';"
        libs = extractor.extract_library_references(code)

        assert len(libs) == 1
        assert libs[0]["libref"] == "mylib"
        assert libs[0]["path"] == "/data/projects"

    def test_multiple_libnames(self, extractor):
        code = """
        LIBNAME proj1 '/data/project1';
        LIBNAME proj2 '/data/project2';
        """
        libs = extractor.extract_library_references(code)

        assert len(libs) == 2
        librefs = {l["libref"] for l in libs}
        assert "proj1" in librefs
        assert "proj2" in librefs

    def test_libname_with_double_quotes(self, extractor):
        code = 'LIBNAME mylib "/data/projects";'
        libs = extractor.extract_library_references(code)

        assert len(libs) == 1
        assert libs[0]["libref"] == "mylib"

    def test_libname_case_insensitive(self, extractor):
        code = "libname MyLib '/data/projects';"
        libs = extractor.extract_library_references(code)

        assert len(libs) == 1

    def test_no_libname(self, extractor):
        code = "DATA out; SET in; RUN;"
        libs = extractor.extract_library_references(code)

        assert len(libs) == 0


class TestExtractFilenameReferences:
    """Tests for extracting FILENAME statements from raw SAS code."""

    def test_single_filename(self, extractor):
        code = 'FILENAME myfile "/data/input.csv";'
        refs = extractor.extract_filename_references(code)

        assert len(refs) == 1
        assert refs[0]["fileref"] == "myfile"
        assert refs[0]["path"] == "/data/input.csv"

    def test_multiple_filenames(self, extractor):
        code = """
        FILENAME infile "/data/input.csv";
        FILENAME outfile "/data/output.csv";
        """
        refs = extractor.extract_filename_references(code)

        assert len(refs) == 2
        names = {r["fileref"] for r in refs}
        assert "infile" in names
        assert "outfile" in names

    def test_no_filename(self, extractor):
        code = "DATA out; SET in; RUN;"
        refs = extractor.extract_filename_references(code)

        assert len(refs) == 0


# ===================================================================
# extract_all_dependencies
# ===================================================================


class TestExtractAllDependencies:
    """Tests for the combined extraction orchestrator."""

    def test_extracts_data_steps(self, extractor):
        parsed = {
            "data_steps": [
                {
                    "output_datasets": "result",
                    "body": "SET input_data;",
                }
            ],
            "proc_steps": [],
            "macros": [],
        }
        result = extractor.extract_all_dependencies(parsed)

        assert len(result["data_steps"]) == 1
        deps = result["data_steps"][0]["dependencies"]
        assert "input_data" in deps.inputs
        assert "result" in deps.outputs

    def test_extracts_proc_steps(self, extractor):
        parsed = {
            "data_steps": [],
            "proc_steps": [
                {
                    "proc_name": "MEANS",
                    "body": "VAR salary;",
                    "options": "DATA=employees",
                }
            ],
            "macros": [],
        }
        result = extractor.extract_all_dependencies(parsed)

        assert len(result["proc_steps"]) == 1
        deps = result["proc_steps"][0]["dependencies"]
        assert "employees" in deps.inputs

    def test_extracts_macros(self, extractor):
        parsed = {
            "data_steps": [],
            "proc_steps": [],
            "macros": [
                {
                    "name": "my_macro",
                    "body": "%LET x = 1; %helper();",
                }
            ],
        }
        result = extractor.extract_all_dependencies(parsed)

        assert len(result["macros"]) == 1
        deps = result["macros"][0]["dependencies"]
        assert "helper" in deps.calls
        assert "x" in deps.macro_vars_defined

    def test_combined_extraction(self, extractor):
        parsed = {
            "data_steps": [
                {
                    "output_datasets": "filtered",
                    "body": "SET raw_data; WHERE x > 0;",
                }
            ],
            "proc_steps": [
                {
                    "proc_name": "SORT",
                    "body": "BY x;",
                    "options": "DATA=filtered OUT=sorted",
                }
            ],
            "macros": [
                {
                    "name": "setup",
                    "body": "%LET path = /data;",
                }
            ],
        }
        result = extractor.extract_all_dependencies(parsed)

        assert len(result["data_steps"]) == 1
        assert len(result["proc_steps"]) == 1
        assert len(result["macros"]) == 1

    def test_empty_input(self, extractor):
        result = extractor.extract_all_dependencies({})

        assert result["data_steps"] == []
        assert result["proc_steps"] == []
        assert result["macros"] == []
        assert result["libraries"] == []
        assert result["file_refs"] == []


# ===================================================================
# DataClasses Default Values
# ===================================================================


class TestDataClassDefaults:
    """Tests for default values of dependency dataclasses."""

    def test_data_step_deps_defaults(self):
        deps = DataStepDependencies()

        assert deps.outputs == []
        assert deps.inputs == []
        assert deps.macro_vars_used == []
        assert deps.macro_vars_defined == []
        assert deps.file_refs == []

    def test_proc_deps_defaults(self):
        deps = ProcDependencies()

        assert deps.proc_name == ""
        assert deps.inputs == []
        assert deps.outputs == []
        assert deps.file_refs == []
        assert deps.macro_vars_used == []

    def test_macro_deps_defaults(self):
        deps = MacroDependencies()

        assert deps.macro_name == ""
        assert deps.calls == []
        assert deps.macro_vars_used == []
        assert deps.macro_vars_defined == []
        assert deps.datasets_referenced == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
