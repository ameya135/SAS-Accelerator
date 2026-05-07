"""
Dependency Extractor

Extracts comprehensive dependencies from parsed SAS code including:
- DATA step dependencies (SET, MERGE, UPDATE, MODIFY)
- PROC dependencies (DATA=, OUT= options)
- Macro dependencies (calls, variable references)
- File and library references
"""

import re
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class DataStepDependencies:
    """Dependencies extracted from a DATA step"""
    outputs: List[str] = field(default_factory=list)       # Created datasets
    inputs: List[str] = field(default_factory=list)        # Input datasets (SET, MERGE, etc.)
    macro_vars_used: List[str] = field(default_factory=list)      # &var references
    macro_vars_defined: List[str] = field(default_factory=list)   # CALL SYMPUT
    file_refs: List[str] = field(default_factory=list)     # INFILE, FILE references


@dataclass
class ProcDependencies:
    """Dependencies extracted from a PROC step"""
    proc_name: str = ""
    inputs: List[str] = field(default_factory=list)        # DATA= option
    outputs: List[str] = field(default_factory=list)       # OUT= option
    file_refs: List[str] = field(default_factory=list)     # FILE references
    macro_vars_used: List[str] = field(default_factory=list)


@dataclass
class MacroDependencies:
    """Dependencies extracted from a macro"""
    macro_name: str = ""
    calls: List[str] = field(default_factory=list)         # Other macros called
    macro_vars_used: List[str] = field(default_factory=list)      # &vars used
    macro_vars_defined: List[str] = field(default_factory=list)   # %LET statements
    datasets_referenced: List[str] = field(default_factory=list)  # Datasets mentioned


class DependencyExtractor:
    """
    Extract all types of dependencies from parsed SAS code

    This class analyzes parsed SAS structures to identify dependencies
    between different code elements.
    """

    def __init__(self):
        """Initialize the dependency extractor"""
        self.dataset_pattern = re.compile(r'\b[a-zA-Z_]\w*\b')
        self.macro_var_pattern = re.compile(r'&([a-zA-Z_]\w*)')
        self.macro_call_pattern = re.compile(r'%([a-zA-Z_]\w*)\s*\(')

    def extract_data_step_dependencies(self, data_step: Dict[str, Any]) -> DataStepDependencies:
        """
        Extract dependencies from a DATA step

        Args:
            data_step: Parsed DATA step dictionary

        Returns:
            DataStepDependencies object
        """
        deps = DataStepDependencies()

        # Extract output datasets
        output_datasets = data_step.get('output_datasets', '')
        if output_datasets:
            deps.outputs = self._parse_dataset_list(output_datasets)

        # Extract body for analysis
        body = data_step.get('body', '')

        # Extract SET statements (input datasets)
        set_matches = re.findall(r'\bSET\s+([^;]+)', body, re.IGNORECASE)
        for match in set_matches:
            datasets = self._parse_dataset_list(match)
            deps.inputs.extend(datasets)

        # Extract MERGE statements
        merge_matches = re.findall(r'\bMERGE\s+([^;]+)', body, re.IGNORECASE)
        for match in merge_matches:
            datasets = self._parse_dataset_list(match)
            deps.inputs.extend(datasets)

        # Extract UPDATE statements
        update_matches = re.findall(r'\bUPDATE\s+([^;]+)', body, re.IGNORECASE)
        for match in update_matches:
            datasets = self._parse_dataset_list(match)
            deps.inputs.extend(datasets)

        # Extract MODIFY statements
        modify_matches = re.findall(r'\bMODIFY\s+([^;]+)', body, re.IGNORECASE)
        for match in modify_matches:
            datasets = self._parse_dataset_list(match)
            deps.inputs.extend(datasets)

        # Extract macro variable references
        deps.macro_vars_used = self._extract_macro_var_references(body)

        # Extract macro variable definitions (CALL SYMPUT, CALL SYMPUTX)
        symput_matches = re.findall(
            r'CALL\s+SYMPUT[X]?\s*\(\s*["\']([^"\']+)["\']',
            body,
            re.IGNORECASE
        )
        deps.macro_vars_defined.extend(symput_matches)

        # Extract file references (INFILE, FILE)
        infile_matches = re.findall(r'\bINFILE\s+([^\s;]+)', body, re.IGNORECASE)
        file_matches = re.findall(r'\bFILE\s+([^\s;]+)', body, re.IGNORECASE)
        deps.file_refs.extend(infile_matches)
        deps.file_refs.extend(file_matches)

        # Remove duplicates
        deps.inputs = list(set(deps.inputs))
        deps.outputs = list(set(deps.outputs))
        deps.macro_vars_used = list(set(deps.macro_vars_used))
        deps.macro_vars_defined = list(set(deps.macro_vars_defined))
        deps.file_refs = list(set(deps.file_refs))

        return deps

    def extract_proc_dependencies(self, proc_step: Dict[str, Any]) -> ProcDependencies:
        """
        Extract dependencies from a PROC step

        Args:
            proc_step: Parsed PROC step dictionary

        Returns:
            ProcDependencies object
        """
        deps = ProcDependencies()

        proc_name = proc_step.get('proc_name', '').upper()
        deps.proc_name = proc_name

        body = proc_step.get('body', '')
        options = proc_step.get('options', '')

        # Combine body and options for analysis
        full_text = f"{options} {body}"

        # Extract DATA= option (input dataset)
        data_matches = re.findall(r'\bDATA\s*=\s*([^\s;]+)', full_text, re.IGNORECASE)
        for match in data_matches:
            datasets = self._parse_dataset_list(match)
            deps.inputs.extend(datasets)

        # Extract OUT= option (output dataset)
        out_matches = re.findall(r'\bOUT\s*=\s*([^\s;]+)', full_text, re.IGNORECASE)
        for match in out_matches:
            datasets = self._parse_dataset_list(match)
            deps.outputs.extend(datasets)

        # Special handling for specific PROCs

        # PROC SQL: Extract FROM clauses
        if proc_name == 'SQL':
            from_matches = re.findall(r'\bFROM\s+([^\s;,WHERE]+)', body, re.IGNORECASE)
            for match in from_matches:
                datasets = self._parse_dataset_list(match)
                deps.inputs.extend(datasets)

            # Extract CREATE TABLE statements
            create_matches = re.findall(r'CREATE\s+TABLE\s+([^\s(;]+)', body, re.IGNORECASE)
            for match in create_matches:
                datasets = self._parse_dataset_list(match)
                deps.outputs.extend(datasets)

        # PROC IMPORT: Creates dataset
        if proc_name == 'IMPORT':
            outfile_matches = re.findall(r'\bOUT\s*=\s*([^\s;]+)', full_text, re.IGNORECASE)
            for match in outfile_matches:
                datasets = self._parse_dataset_list(match)
                deps.outputs.extend(datasets)

        # PROC EXPORT: Uses dataset
        if proc_name == 'EXPORT':
            data_matches_export = re.findall(r'\bDATA\s*=\s*([^\s;]+)', full_text, re.IGNORECASE)
            for match in data_matches_export:
                datasets = self._parse_dataset_list(match)
                deps.inputs.extend(datasets)

        # Extract macro variable references
        deps.macro_vars_used = self._extract_macro_var_references(full_text)

        # Extract file references
        file_matches = re.findall(r'\bFILE\s*=\s*([^\s;]+)', full_text, re.IGNORECASE)
        deps.file_refs.extend(file_matches)

        # Remove duplicates
        deps.inputs = list(set(deps.inputs))
        deps.outputs = list(set(deps.outputs))
        deps.macro_vars_used = list(set(deps.macro_vars_used))
        deps.file_refs = list(set(deps.file_refs))

        return deps

    def extract_macro_dependencies(self, macro: Dict[str, Any]) -> MacroDependencies:
        """
        Extract dependencies from a macro definition

        Args:
            macro: Parsed macro dictionary

        Returns:
            MacroDependencies object
        """
        deps = MacroDependencies()

        deps.macro_name = macro.get('name', '')
        body = macro.get('body', '')

        # Extract macro calls (e.g., %other_macro(args))
        macro_calls = self.macro_call_pattern.findall(body)
        deps.calls = list(set(macro_calls))

        # Extract macro variable references (&var)
        deps.macro_vars_used = self._extract_macro_var_references(body)

        # Extract macro variable definitions (%LET var = value;)
        let_matches = re.findall(r'%LET\s+([a-zA-Z_]\w*)\s*=', body, re.IGNORECASE)
        deps.macro_vars_defined.extend(let_matches)

        # Extract potential dataset references
        # Look for DATA and SET statements within macro
        data_matches = re.findall(r'\bDATA\s+([^;]+)', body, re.IGNORECASE)
        for match in data_matches:
            datasets = self._parse_dataset_list(match)
            deps.datasets_referenced.extend(datasets)

        set_matches = re.findall(r'\bSET\s+([^;]+)', body, re.IGNORECASE)
        for match in set_matches:
            datasets = self._parse_dataset_list(match)
            deps.datasets_referenced.extend(datasets)

        # Remove duplicates
        deps.calls = list(set(deps.calls))
        deps.macro_vars_used = list(set(deps.macro_vars_used))
        deps.macro_vars_defined = list(set(deps.macro_vars_defined))
        deps.datasets_referenced = list(set(deps.datasets_referenced))

        return deps

    def extract_all_dependencies(self, parsed_sas: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all dependencies from parsed SAS code

        Args:
            parsed_sas: Complete parsed SAS structure from SASParser

        Returns:
            Dictionary containing all extracted dependencies
        """
        result = {
            'data_steps': [],
            'proc_steps': [],
            'macros': [],
            'libraries': [],
            'file_refs': []
        }

        # Extract DATA step dependencies
        for data_step in parsed_sas.get('data_steps', []):
            deps = self.extract_data_step_dependencies(data_step)
            result['data_steps'].append({
                'step': data_step,
                'dependencies': deps
            })

        # Extract PROC dependencies
        for proc_step in parsed_sas.get('proc_steps', []):
            deps = self.extract_proc_dependencies(proc_step)
            result['proc_steps'].append({
                'step': proc_step,
                'dependencies': deps
            })

        # Extract macro dependencies
        for macro in parsed_sas.get('macros', []):
            deps = self.extract_macro_dependencies(macro)
            result['macros'].append({
                'macro': macro,
                'dependencies': deps
            })

        return result

    def _parse_dataset_list(self, dataset_string: str) -> List[str]:
        """
        Parse a string containing dataset names

        Handles various formats:
        - Single dataset: "mydata"
        - Multiple datasets: "data1 data2 data3"
        - Librefs: "mylib.dataset"
        - Options in parentheses: "data1(keep=var1)"

        Args:
            dataset_string: String containing dataset names

        Returns:
            List of cleaned dataset names
        """
        # Remove options in parentheses
        cleaned = re.sub(r'\([^)]*\)', '', dataset_string)

        # Split by whitespace and commas
        parts = re.split(r'[\s,]+', cleaned.strip())

        # Filter valid dataset names
        datasets = []
        for part in parts:
            part = part.strip()
            # Check if it looks like a dataset name (letters, numbers, underscores, dots)
            if re.match(r'^[a-zA-Z_][\w\.]*$', part):
                # Remove library reference if present, keep just dataset name
                if '.' in part:
                    # Keep full libref.dataset for now
                    datasets.append(part)
                else:
                    datasets.append(part)

        return [d for d in datasets if d and d.lower() not in ['run', 'quit', 'by', 'where', 'if']]

    def _extract_macro_var_references(self, text: str) -> List[str]:
        """
        Extract macro variable references from text

        Args:
            text: Text to search for &var references

        Returns:
            List of macro variable names (without & prefix)
        """
        matches = self.macro_var_pattern.findall(text)
        # Filter out common SAS automatic macro variables
        excluded = {'sysdate', 'systime', 'sysday', 'syslast', 'sysrc', 'sqlobs', 'sqlrc'}
        return [m for m in set(matches) if m.lower() not in excluded]

    def extract_library_references(self, sas_code: str) -> List[Dict[str, str]]:
        """
        Extract LIBNAME statements

        Args:
            sas_code: Raw SAS code

        Returns:
            List of library definitions
        """
        libraries = []
        libname_pattern = re.compile(
            r'LIBNAME\s+([a-zA-Z_]\w*)\s+["\']?([^;"\']+)["\']?',
            re.IGNORECASE
        )

        for match in libname_pattern.finditer(sas_code):
            libraries.append({
                'libref': match.group(1),
                'path': match.group(2).strip()
            })

        return libraries

    def extract_filename_references(self, sas_code: str) -> List[Dict[str, str]]:
        """
        Extract FILENAME statements

        Args:
            sas_code: Raw SAS code

        Returns:
            List of file reference definitions
        """
        file_refs = []
        filename_pattern = re.compile(
            r'FILENAME\s+([a-zA-Z_]\w*)\s+["\']([^"\']+)["\']',
            re.IGNORECASE
        )

        for match in filename_pattern.finditer(sas_code):
            file_refs.append({
                'fileref': match.group(1),
                'path': match.group(2)
            })

        return file_refs
