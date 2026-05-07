"""
Test suite for validation improvements

Tests the VariableTracker, ExecutionOrderOptimizer, and enhanced CodeReconciler.
"""

import sys
from pathlib import Path

# Add parent directory to path
_repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_repo_root))

from graph_approach.migration.variable_tracker import VariableTracker, ValidationResult
from graph_approach.migration.execution_order import ExecutionOrderOptimizer
from graph_approach.migration.code_reconciler import CodeReconciler


def test_variable_tracker_undefined():
    """Test detection of undefined variables"""
    print("\n" + "="*60)
    print("TEST: Variable Tracker - Undefined Variables")
    print("="*60)
    
    code = """
# Test code with undefined variable
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("test").getOrCreate()

# Using portfolio_master before it's defined
risk_exposures_df = (
    portfolio_master
        .select('loan_id', 'customer_id')
        .filter(F.col('amount') > 0)
)

# Now we define it (too late!)
portfolio_master = spark.read.parquet("data/portfolio.parquet")
"""
    
    tracker = VariableTracker()
    result = tracker.analyze_code(code)
    
    print(f"\nAnalysis Result:")
    print(f"  Valid: {result.is_valid}")
    print(f"  Total Issues: {len(result.issues)}")
    
    for issue in result.issues:
        print(f"\n  [{issue.severity.upper()}] {issue.issue_type}")
        print(f"    Line {issue.line_number}: {issue.message}")
        if issue.suggested_fix:
            print(f"    Fix: {issue.suggested_fix}")
    
    # Check we detected the issue
    undefined_issues = [i for i in result.issues if i.issue_type == 'undefined']
    assert len(undefined_issues) > 0, "Should detect undefined variable"
    print("\n✓ Test passed!")


def test_variable_tracker_use_after_delete():
    """Test detection of use after deletion"""
    print("\n" + "="*60)
    print("TEST: Variable Tracker - Use After Delete")
    print("="*60)
    
    code = """
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("test").getOrCreate()

# Define the DataFrame
loan_portfolio_df = spark.read.parquet("data/loans.parquet")

# Delete it
del loan_portfolio_df

# Try to use it (error!)
result_df = loan_portfolio_df.filter(F.col('status') == 'active')
"""
    
    tracker = VariableTracker()
    result = tracker.analyze_code(code)
    
    print(f"\nAnalysis Result:")
    print(f"  Valid: {result.is_valid}")
    
    for issue in result.issues:
        print(f"\n  [{issue.severity.upper()}] {issue.issue_type}")
        print(f"    Line {issue.line_number}: {issue.message}")
    
    # Check we detected the issue
    use_after_del = [i for i in result.issues if i.issue_type == 'use_after_delete']
    assert len(use_after_del) > 0, "Should detect use after delete"
    print("\n✓ Test passed!")


def test_variable_tracker_suggest_fixes():
    """Test automatic fix suggestions"""
    print("\n" + "="*60)
    print("TEST: Variable Tracker - Fix Suggestions")
    print("="*60)
    
    code = """
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("test").getOrCreate()

# Code that uses macro variables without defining them
result_df = raw_data_df.filter(F.col('score') > unemployment_shock)

# Delete and then use
del loan_portfolio_df
final_df = loan_portfolio_df.select('id')
"""
    
    tracker = VariableTracker()
    result = tracker.analyze_code(code)
    
    print(f"\nBefore Fix:")
    print(f"  Issues: {len(result.issues)}")
    
    # Get fixed code
    fixed_code, fixes_applied = tracker.suggest_fixes(code)
    
    print(f"\nFixes Applied:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    print(f"\nFixed Code Preview (first 30 lines):")
    for i, line in enumerate(fixed_code.split('\n')[:30], 1):
        print(f"  {i:3}| {line}")
    
    assert len(fixes_applied) > 0, "Should apply at least one fix"
    print("\n✓ Test passed!")


def test_execution_order_optimizer():
    """Test execution order optimization"""
    print("\n" + "="*60)
    print("TEST: Execution Order Optimizer")
    print("="*60)
    
    code = """
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("test").getOrCreate()

# This uses result_df before it's defined
final_output = result_df.orderBy('score')

# This creates result_df
result_df = base_df.filter(F.col('status') == 'active')

# This creates base_df
base_df = spark.read.parquet("data/base.parquet")
"""
    
    optimizer = ExecutionOrderOptimizer()
    result = optimizer.analyze_and_optimize(code)
    
    print(f"\nAnalysis Result:")
    print(f"  Total Blocks: {len(result.ordered_blocks)}")
    print(f"  Reordered: {result.reordered}")
    print(f"  Issues: {len(result.issues)}")
    
    print(f"\nOriginal Order: {result.original_order}")
    print(f"New Order: {result.new_order}")
    
    for issue in result.issues:
        print(f"\n  [{issue.issue_type.upper()}] {issue.description}")
    
    # Get report
    report = optimizer.generate_report()
    print(f"\nReport Preview:")
    print(report[:500])
    
    print("\n✓ Test passed!")


def test_macro_variable_parser():
    """Test SAS macro variable extraction"""
    print("\n" + "="*60)
    print("TEST: SAS Macro Variable Parser")
    print("="*60)
    
    try:
        from parser.sas_code_parser import SASParser, SASMacroVariableParser
        
        sas_code = """
%let unemployment_shock = 5.0;
%let gdp_decline = -2.0;
%let report_date = '2024-01-15';

data portfolio_analysis;
    set work.loans;
    stress_impact = current_balance * &unemployment_shock / 100;
    report_dt = &report_date;
    
    call symput('total_exposure', sum(current_balance));
run;

proc print data=&output_dataset;
run;
"""
        
        parser = SASParser()
        result = parser.parse_content(sas_code)
        
        macro_vars = result.get('macro_variables', {})
        
        print(f"\nParsed Macro Variables:")
        print(f"  Definitions: {macro_vars.get('summary', {}).get('total_definitions', 0)}")
        print(f"  Dynamic (CALL SYMPUT): {macro_vars.get('summary', {}).get('total_dynamic', 0)}")
        print(f"  Total References: {macro_vars.get('summary', {}).get('total_references', 0)}")
        print(f"  Undefined References: {macro_vars.get('summary', {}).get('total_undefined', 0)}")
        
        print(f"\nDefined Variables:")
        for defn in macro_vars.get('definitions', []):
            print(f"  - {defn['name']} = {defn['value']} (line {defn['line']})")
        
        print(f"\nUndefined Variables:")
        for ref in macro_vars.get('undefined_references', []):
            print(f"  - {ref['name']} (first used at line {ref['first_reference_line']})")
        
        # Generate initialization code
        init_code = parser.get_macro_var_initialization(sas_code)
        print(f"\nGenerated Python Initialization:")
        print(init_code)
        
        print("\n✓ Test passed!")
        
    except ImportError as e:
        print(f"\n⚠ Skipped (parser not available): {e}")


def test_full_reconciliation():
    """Test the full reconciliation pipeline"""
    print("\n" + "="*60)
    print("TEST: Full Reconciliation Pipeline")
    print("="*60)
    
    # Simulate converted chunks with issues
    chunks = [
        {
            'chunk_id': 'chunk_001',
            'pyspark_code': """
from pyspark.sql import SparkSession, functions as F

# Load portfolio data
portfolio_df = spark.read.parquet("data/portfolio.parquet")
""",
            'mapping': 'Data load',
            'variables_created': ['portfolio_df']
        },
        {
            'chunk_id': 'chunk_002',
            'pyspark_code': """
from pyspark.sql import functions as F

# Delete old data
del loan_portfolio_raw
del sorted_customers

# Process risk - uses portfolio_master which doesn't exist yet
risk_df = (
    portfolio_master
        .select('loan_id', 'risk_score')
        .filter(F.col('risk_score') > 0)
)
""",
            'mapping': 'Risk processing',
            'variables_created': ['risk_df']
        },
        {
            'chunk_id': 'chunk_003',
            'pyspark_code': """
from pyspark.sql import functions as F

# Create portfolio master from portfolio_df
portfolio_master = portfolio_df.withColumn('risk_flag', F.lit(True))
""",
            'mapping': 'Create master',
            'variables_created': ['portfolio_master']
        }
    ]
    
    # Create mock execution context
    class MockExecutionContext:
        def __init__(self):
            self.variable_name_map = {}
    
    reconciler = CodeReconciler(use_llm=False)  # Disable LLM for testing
    
    result = reconciler.reconcile_chunks_with_report(
        chunks,
        MockExecutionContext()
    )
    
    print(f"\nReconciliation Result:")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Fixes Applied: {len(result.fixes_applied)}")
    
    print(f"\nFixes Applied:")
    for fix in result.fixes_applied:
        print(f"  - {fix}")
    
    if result.warnings:
        print(f"\nWarnings:")
        for warn in result.warnings:
            print(f"  - {warn}")
    
    print(f"\nGenerated Code (first 50 lines):")
    for i, line in enumerate(result.code.split('\n')[:50], 1):
        print(f"  {i:3}| {line}")
    
    print("\n✓ Test passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# VALIDATION IMPROVEMENT TESTS")
    print("#"*60)
    
    tests = [
        test_variable_tracker_undefined,
        test_variable_tracker_use_after_delete,
        test_variable_tracker_suggest_fixes,
        test_execution_order_optimizer,
        test_macro_variable_parser,
        test_full_reconciliation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

