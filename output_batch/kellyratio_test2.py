# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

rf = 0.01 / 252

def kelly_ratio(returns, rf=rf):

    mean_excess = returns.mean() - rf

    var = returns.var()
    return mean_excess / var

# Convert pandas DataFrames to Spark DataFrames

    error_data = {'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    kellyratio = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_from_r = spark.createDataFrame(pd.DataFrame(error_data))

# Compare DataFrames and output differences (fuzz logic: allow small numerical differences)

def fuzz(a, b, tol=1e-6):
    return abs(a - b) < tol

# Join DataFrames for comparison

# Set up variables from macro dependencies

# Align columns for comparison

diff_pd = returns_pdf[diff_mask]

# Count number of differences

keep = False  # Set from macro variable

    pass_var = True

    notes = 'Passed'
else:
    print('ERROR: PROBLEM IN TEST Kellyratio_TEST2')

    pass_var = False

    notes = 'Differences detected in outputs.'

# Cleanup if keep is False
if not keep:

    returns_from_r = None

    kellyratio = None

    diff = None

dir = os.environ.get('DIR', '/path/to/dir')  # Set from macro variable

# Read prices.csv into a Pandas DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)

returns_pd = prices_pd.pct_change().dropna()

kelly_vals = kelly_ratio(returns_pd)

kellyratio_pd = pd.DataFrame([kelly_vals], columns=returns_pd.columns)

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

kellyratio = spark.createDataFrame(kellyratio_pd)

# Handle empty DataFrames by replacing with error DataFrames
if kellyratio.count() == 0:

if returns_from_r.count() == 0:

returns_pd_cols = [col for col in returns_from_r.columns if col != returns_from_r.columns[0]]

kellyratio_pd_cols = kellyratio.columns

returns_pdf = returns_from_r.toPandas()

kellyratio_pdf = kellyratio.toPandas()

diff_mask = pd.Series(False, index=returns_pdf.index)
for col in ['IBM', 'GE', 'DOW', 'GOOGL']:
    if col in returns_pdf.columns and col in kellyratio_pdf.columns:
        diff_mask |= ~fuzz(returns_pdf[col], kellyratio_pdf[col][0])

diff = spark.createDataFrame(diff_pd) if not diff_pd.empty else spark.createDataFrame([], returns_from_r.schema)

n = diff.count()

# Set pass/fail and notes
if n == 0:
    print('NOTE: NO ERROR IN TEST Kellyratio_TEST2')

# Calculate returns and Kelly Ratio using pandas/numpy
prices_pd.set_index(prices_pd.columns[0], inplace=True)
