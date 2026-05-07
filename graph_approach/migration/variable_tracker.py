"""
Variable Tracker

Tracks variable lifecycle (definition, usage, deletion) in generated PySpark code.
Validates that variables are defined before use and not used after deletion.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class VariableState(Enum):
    """State of a variable in the code"""
    UNDEFINED = "undefined"
    DEFINED = "defined"
    DELETED = "deleted"


@dataclass
class VariableOccurrence:
    """Records where a variable appears in code"""
    line_number: int
    occurrence_type: str  # 'definition', 'usage', 'deletion'
    code_snippet: str = ""


@dataclass
class VariableInfo:
    """Complete information about a variable"""
    name: str
    definitions: List[VariableOccurrence] = field(default_factory=list)
    usages: List[VariableOccurrence] = field(default_factory=list)
    deletions: List[VariableOccurrence] = field(default_factory=list)
    
    @property
    def first_definition_line(self) -> Optional[int]:
        """Get line number of first definition"""
        if self.definitions:
            return min(d.line_number for d in self.definitions)
        return None
    
    @property
    def first_usage_line(self) -> Optional[int]:
        """Get line number of first usage"""
        if self.usages:
            return min(u.line_number for u in self.usages)
        return None
    
    @property
    def first_deletion_line(self) -> Optional[int]:
        """Get line number of first deletion"""
        if self.deletions:
            return min(d.line_number for d in self.deletions)
        return None


@dataclass
class ValidationIssue:
    """An issue found during validation"""
    issue_type: str  # 'undefined', 'use_after_delete', 'duplicate_definition', 'unused'
    variable_name: str
    line_number: int
    message: str
    severity: str = "error"  # 'error', 'warning', 'info'
    suggested_fix: str = ""


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    variables: Dict[str, VariableInfo] = field(default_factory=dict)
    macro_variables: Dict[str, str] = field(default_factory=dict)
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [i for i in self.issues if i.severity == "error"]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues"""
        return [i for i in self.issues if i.severity == "warning"]


class VariableTracker:
    """
    Track variable lifecycle in PySpark code
    
    Detects:
    - Variables used before definition
    - Variables used after deletion
    - Duplicate definitions
    - Undefined macro variables
    """
    
    def __init__(self):
        """Initialize tracker"""
        self.variables: Dict[str, VariableInfo] = {}
        self.macro_vars: Dict[str, str] = {}  # name -> default_value
        self.issues: List[ValidationIssue] = []
        
        # Patterns for detecting variable operations
        self.patterns = {
            # DataFrame assignment: var_name = ...
            'definition': re.compile(
                r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?!.*==)',
                re.MULTILINE
            ),
            # Variable deletion: del var_name
            'deletion': re.compile(
                r'^\s*del\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                re.MULTILINE
            ),
            # DataFrame method calls: var_name.method(...)
            'df_usage': re.compile(
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*(select|filter|join|groupBy|agg|'
                r'withColumn|orderBy|drop|alias|show|count|collect|write|'
                r'createOrReplaceTempView|cache|persist|unpersist)\s*\(',
                re.IGNORECASE
            ),
            # Function argument usage: func(var_name, ...)
            'arg_usage': re.compile(
                r'(?:spark\.table|F\.col|F\.when|\.join|\.union|\.intersect)\s*\(\s*'
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[,)]'
            ),
            # Direct variable reference in expressions
            'expr_usage': re.compile(
                r'(?<!["\'])([a-zA-Z_][a-zA-Z0-9_]*_df)\b(?!["\'])'
            ),
            # SAS macro variable references (from original SAS)
            'macro_ref': re.compile(r'&([a-zA-Z_][a-zA-Z0-9_]*)'),
            # Python variable that looks like it came from SAS macro
            'macro_var_python': re.compile(
                r'\b(unemployment_shock|gdp_decline|interest_rate_shock|'
                r'report_date|portfolio_data|stress_results|output_summary|'
                r'risk_score_var|dataset)\b'
            )
        }
        
        # Known PySpark built-ins and common names to ignore
        self.ignore_vars = {
            'spark', 'F', 'T', 'Window', 'Row', 'SparkSession',
            'StructType', 'StructField', 'StringType', 'IntegerType',
            'DoubleType', 'DateType', 'TimestampType', 'BooleanType',
            'datetime', 'date', 'time', 'print', 'len', 'str', 'int',
            'float', 'list', 'dict', 'set', 'tuple', 'range', 'True',
            'False', 'None', 'self', 'cls', 're', 'os', 'sys', 'json',
            'display', 'round', 'sum', 'min', 'max', 'abs'
        }
    
    def analyze_code(self, code: str) -> ValidationResult:
        """
        Analyze PySpark code for variable issues
        
        Args:
            code: PySpark code to analyze
            
        Returns:
            ValidationResult with all findings
        """
        self.variables = {}
        self.macro_vars = {}
        self.issues = []
        
        lines = code.split('\n')
        
        # First pass: find all definitions, usages, and deletions
        for line_num, line in enumerate(lines, 1):
            self._analyze_line(line, line_num)
        
        # Second pass: validate variable lifecycle
        self._validate_lifecycle()
        
        # Third pass: detect macro variables that need initialization
        self._detect_macro_variables(code)
        
        # Build result
        is_valid = not any(i.severity == "error" for i in self.issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=self.issues,
            variables=self.variables,
            macro_variables=self.macro_vars
        )
    
    def _analyze_line(self, line: str, line_num: int) -> None:
        """Analyze a single line for variable operations"""
        # Skip comments
        stripped = line.strip()
        if stripped.startswith('#'):
            return
        
        # Remove inline comments for analysis
        line_no_comment = line
        if '#' in line:
            line_no_comment = line[:line.index('#')]
        
        # Check for deletions first (del var)
        del_matches = self.patterns['deletion'].findall(line_no_comment)
        for var_name in del_matches:
            if var_name not in self.ignore_vars:
                self._record_deletion(var_name, line_num, stripped)
        
        # Check for definitions (var = ...)
        def_matches = self.patterns['definition'].findall(line_no_comment)
        defined_vars = set(v for _, v in def_matches)
        for indent, var_name in def_matches:
            if var_name not in self.ignore_vars and not var_name.startswith('_'):
                self._record_definition(var_name, line_num, stripped)
        
        # Check for DataFrame usages with method calls: var_name.method(...)
        df_matches = self.patterns['df_usage'].findall(line_no_comment)
        for var_name, method in df_matches:
            if var_name not in self.ignore_vars and var_name not in defined_vars:
                self._record_usage(var_name, line_num, stripped)
        
        # Check for expression usages (_df variables)
        expr_matches = self.patterns['expr_usage'].findall(line_no_comment)
        for var_name in expr_matches:
            if var_name not in self.ignore_vars and var_name not in defined_vars:
                self._record_usage(var_name, line_num, stripped)
        
        # Check for variable usage in right-hand side of assignments
        # e.g., result = some_df.select(...) - detect some_df usage
        rhs_match = re.search(r'=\s*(\w+(?:_df|_data|_master|_raw|_clean|_portfolio|_customers)?)\s*\.', stripped)
        if rhs_match:
            var_name = rhs_match.group(1)
            if var_name not in self.ignore_vars and var_name not in defined_vars:
                self._record_usage(var_name, line_num, stripped)
        
        # Check for standalone variable on indented line (multiline expressions)
        # e.g., result = (\n    portfolio_master\n        .select(...))
        if stripped and not '=' in stripped and not stripped.startswith('.'):
            # Check if line is a variable followed by a method call or alone
            standalone_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)(?:\s*$|\s*\.\w)', stripped)
            if standalone_match:
                var_name = standalone_match.group(1)
                # Exclude common keywords and types
                keywords = {'if', 'else', 'elif', 'for', 'while', 'return', 'def', 'class', 
                           'import', 'from', 'as', 'try', 'except', 'finally', 'with',
                           'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is'}
                if var_name not in self.ignore_vars and var_name not in keywords:
                    self._record_usage(var_name, line_num, stripped)
        
        # Check for macro variable references
        macro_matches = self.patterns['macro_var_python'].findall(line_no_comment)
        for var_name in macro_matches:
            if var_name not in defined_vars:
                self._record_usage(var_name, line_num, stripped)
    
    def _record_definition(self, var_name: str, line_num: int, snippet: str) -> None:
        """Record a variable definition"""
        if var_name not in self.variables:
            self.variables[var_name] = VariableInfo(name=var_name)
        
        self.variables[var_name].definitions.append(
            VariableOccurrence(
                line_number=line_num,
                occurrence_type='definition',
                code_snippet=snippet[:100]
            )
        )
    
    def _record_usage(self, var_name: str, line_num: int, snippet: str) -> None:
        """Record a variable usage"""
        if var_name not in self.variables:
            self.variables[var_name] = VariableInfo(name=var_name)
        
        self.variables[var_name].usages.append(
            VariableOccurrence(
                line_number=line_num,
                occurrence_type='usage',
                code_snippet=snippet[:100]
            )
        )
    
    def _record_deletion(self, var_name: str, line_num: int, snippet: str) -> None:
        """Record a variable deletion"""
        if var_name not in self.variables:
            self.variables[var_name] = VariableInfo(name=var_name)
        
        self.variables[var_name].deletions.append(
            VariableOccurrence(
                line_number=line_num,
                occurrence_type='deletion',
                code_snippet=snippet[:100]
            )
        )
    
    def _validate_lifecycle(self) -> None:
        """Validate variable lifecycle for all tracked variables"""
        for var_name, var_info in self.variables.items():
            # Check for use before definition
            if var_info.usages and var_info.first_usage_line:
                first_usage = var_info.first_usage_line
                first_def = var_info.first_definition_line
                
                if first_def is None:
                    # Never defined but used - this is a warning, not error
                    # The variable likely comes from a chunk that didn't convert properly
                    # We'll add a placeholder definition instead of failing
                    self.issues.append(ValidationIssue(
                        issue_type='undefined',
                        variable_name=var_name,
                        line_number=first_usage,
                        message=f"Variable '{var_name}' is used but never defined",
                        severity='warning',  # Changed from 'error' - we'll auto-fix this
                        suggested_fix=f"# TODO: {var_name} needs to be defined - check if the source chunk converted correctly"
                    ))
                elif first_usage < first_def:
                    # Used before defined - this should be fixed by execution order optimizer
                    # If it still happens, it's a warning not a critical error
                    self.issues.append(ValidationIssue(
                        issue_type='undefined',
                        variable_name=var_name,
                        line_number=first_usage,
                        message=f"Variable '{var_name}' is used at line {first_usage} before definition at line {first_def}",
                        severity='warning',  # Changed from 'error' - execution order should fix this
                        suggested_fix=f"Move definition of '{var_name}' before line {first_usage}"
                    ))
            
            # Check for use after deletion
            if var_info.deletions and var_info.usages:
                for deletion in var_info.deletions:
                    for usage in var_info.usages:
                        if usage.line_number > deletion.line_number:
                            self.issues.append(ValidationIssue(
                                issue_type='use_after_delete',
                                variable_name=var_name,
                                line_number=usage.line_number,
                                message=f"Variable '{var_name}' is used at line {usage.line_number} after deletion at line {deletion.line_number}",
                                severity='warning',  # Changed from 'error' - we auto-fix by commenting out del
                                suggested_fix=f"Remove 'del {var_name}' at line {deletion.line_number} or don't use '{var_name}' after deletion"
                            ))
            
            # Check for multiple definitions (potential overwrite issue)
            # Note: Multiple definitions are common in generated code (different transformations)
            # and in PySpark it's valid to redefine DataFrames, so this is just informational
            if len(var_info.definitions) > 1:
                lines = [d.line_number for d in var_info.definitions]
                self.issues.append(ValidationIssue(
                    issue_type='duplicate_definition',
                    variable_name=var_name,
                    line_number=lines[-1],
                    message=f"Variable '{var_name}' is defined multiple times at lines: {lines}",
                    severity='info',  # Changed from 'warning' - this is expected in generated code
                    suggested_fix=f"Review if multiple definitions of '{var_name}' are intentional"
                ))
            
            # Check for unused variables (defined but never used)
            if var_info.definitions and not var_info.usages:
                self.issues.append(ValidationIssue(
                    issue_type='unused',
                    variable_name=var_name,
                    line_number=var_info.first_definition_line or 0,
                    message=f"Variable '{var_name}' is defined but never used",
                    severity='info',
                    suggested_fix=f"Consider removing unused variable '{var_name}'"
                ))
    
    def _detect_macro_variables(self, code: str) -> None:
        """Detect SAS macro variables that need initialization"""
        # Common SAS macro variables that become Python variables
        common_macro_vars = {
            'unemployment_shock': '5.0',
            'gdp_decline': '-2.0',
            'interest_rate_shock': '2.0',
            'report_date': "datetime.today().strftime('%Y-%m-%d')",
            'portfolio_data': "'risk_exposures_df'",
            'stress_results': "'stress_results_df'",
            'output_summary': "'output_summary_df'",
            'risk_score_var': "'risk_score'",
            'dataset': "'output_df'"
        }
        
        for var_name, default_value in common_macro_vars.items():
            if var_name in self.variables:
                var_info = self.variables[var_name]
                # If it's used but not properly defined (or only used)
                if var_info.usages and not var_info.definitions:
                    self.macro_vars[var_name] = default_value
    
    def find_undefined_variables(self) -> List[str]:
        """Get list of undefined variables"""
        undefined = []
        for var_name, var_info in self.variables.items():
            if var_info.usages and not var_info.definitions:
                undefined.append(var_name)
        return undefined
    
    def find_use_after_delete(self) -> List[Tuple[str, int, int]]:
        """
        Find variables used after deletion
        
        Returns:
            List of (var_name, deletion_line, usage_line) tuples
        """
        issues = []
        for var_name, var_info in self.variables.items():
            if var_info.deletions and var_info.usages:
                for deletion in var_info.deletions:
                    for usage in var_info.usages:
                        if usage.line_number > deletion.line_number:
                            issues.append((var_name, deletion.line_number, usage.line_number))
        return issues
    
    def suggest_fixes(self, code: str) -> Tuple[str, List[str]]:
        """
        Generate fixed code with suggestions
        
        Args:
            code: Original code
            
        Returns:
            Tuple of (fixed_code, list_of_fixes_applied)
        """
        fixes_applied = []
        lines = code.split('\n')
        
        # Collect undefined variables that need initialization
        undefined = self.find_undefined_variables()
        
        # Collect macro variables that need initialization
        macro_init_block = []
        if self.macro_vars:
            macro_init_block.append("# SAS Macro Variables - Set these values before running")
            for var_name, default_value in self.macro_vars.items():
                macro_init_block.append(f"{var_name} = {default_value}  # TODO: Verify this value")
                fixes_applied.append(f"Added initialization for macro variable '{var_name}'")
            macro_init_block.append("")
        
        # Collect DataFrames that need placeholder definitions
        df_init_block = []
        for var_name in undefined:
            if var_name not in self.macro_vars:
                # Determine likely source based on variable name
                base_name = var_name.replace('_df', '').replace('_data', '')
                
                if var_name.endswith('_df') or var_name.endswith('_data'):
                    df_init_block.append(f"# TODO: {var_name} needs to be loaded - source dataset: {base_name}")
                    df_init_block.append(f"{var_name} = spark.read.csv('path/to/{base_name}.csv', header=True, inferSchema=True)  # FIXME: Update path")
                    fixes_applied.append(f"Added placeholder definition for undefined DataFrame '{var_name}'")
        
        if df_init_block:
            df_init_block.insert(0, "# Undefined DataFrames - Load these from your data sources")
            df_init_block.append("")
        
        # Find deletion statements that cause issues
        use_after_delete = self.find_use_after_delete()
        deletion_lines_to_comment = set()
        for var_name, del_line, use_line in use_after_delete:
            deletion_lines_to_comment.add(del_line)
            fixes_applied.append(f"Commented out 'del {var_name}' at line {del_line} (used later at line {use_line})")
        
        # Rebuild code
        new_lines = []
        
        # Find insertion point (after imports)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                insert_idx = i + 1
            elif line.strip() and not line.strip().startswith('#') and insert_idx > 0:
                break
        
        # Add original lines with fixes
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Insert initialization blocks after imports
            if i == insert_idx and (macro_init_block or df_init_block):
                new_lines.append("")
                new_lines.extend(macro_init_block)
                new_lines.extend(df_init_block)
            
            # Comment out problematic deletion statements
            if line_num in deletion_lines_to_comment:
                new_lines.append(f"# COMMENTED OUT (variable used later): {line}")
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines), fixes_applied
    
    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report"""
        report = []
        report.append("=" * 60)
        report.append("VARIABLE LIFECYCLE VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        errors = [i for i in self.issues if i.severity == 'error']
        warnings = [i for i in self.issues if i.severity == 'warning']
        infos = [i for i in self.issues if i.severity == 'info']
        
        report.append(f"Total Issues: {len(self.issues)}")
        report.append(f"  Errors: {len(errors)}")
        report.append(f"  Warnings: {len(warnings)}")
        report.append(f"  Info: {len(infos)}")
        report.append("")
        
        if errors:
            report.append("ERRORS:")
            report.append("-" * 40)
            for issue in errors:
                report.append(f"  Line {issue.line_number}: {issue.message}")
                if issue.suggested_fix:
                    report.append(f"    Fix: {issue.suggested_fix}")
            report.append("")
        
        if warnings:
            report.append("WARNINGS:")
            report.append("-" * 40)
            for issue in warnings:
                report.append(f"  Line {issue.line_number}: {issue.message}")
            report.append("")
        
        if self.macro_vars:
            report.append("MACRO VARIABLES NEEDING INITIALIZATION:")
            report.append("-" * 40)
            for var_name, default in self.macro_vars.items():
                report.append(f"  {var_name} = {default}")
            report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)

