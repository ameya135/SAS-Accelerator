# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Calculate variability (standard deviation * sqrt(252))

    error_data = {'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    variability_table = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_from_r = spark.createDataFrame(pd.DataFrame(error_data))

returns_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

returns_from_r = returns_from_r.select(*returns_cols)

variability_table = variability_table.select(*returns_cols)

diff = diff.select(
    *[pyspark_abs(col(f'{c}_left') - col(f'{c}_right')).alias(c) 
      for c in returns_cols]
) if all(f'{c}_left' in diff.columns and f'{c}_right' in diff.columns for c in returns_cols) else \
    diff.select(
        *[pyspark_abs(col(f'{c}') - col(f'{c}')).alias(c) for c in returns_cols]
    )

diff = diff.filter(
    (pyspark_abs(col('IBM')) > 1e-4) |
    (pyspark_abs(col('GE')) > 1e-4) |
    (pyspark_abs(col('DOW')) > 1e-4) |
    (pyspark_abs(col('GOOGL')) > 1e-4) |
    (pyspark_abs(col('SPY')) > 1e-4)
)

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_variability_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_variability_TEST1')

# Clean up temporary tables if keep is False
if not keep:
    for df_name in ['diff', 'returns_from_r', 'variability_table']:
        try:

            df = locals()[df_name]
            df.unpersist()
        except Exception:
            pass

# Define file path for prices.csv

prices_csv_path = os.path.join(dir, 'prices.csv')

# Read prices.csv into a Pandas DataFrame for time series operations

prices_pd = pd.read_csv(prices_csv_path, index_col=0, parse_dates=True)

# Calculate discrete returns using pandas

returns_pd = prices_pd.pct_change().dropna()

variability_pd = returns_pd.std() * np.sqrt(252)

variability_table_pd = pd.DataFrame([variability_pd], columns=returns_pd.columns)

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

variability_table = spark.createDataFrame(variability_table_pd)

# Convert returns and variability_table to Spark DataFrames

# Handle empty DataFrames by replacing with error DataFrames if needed
if variability_table.count() == 0:

if returns_from_r.count() == 0:

# Compare returns_from_r and variability_table: absolute difference > 1e-4 for any column
# Join on row order since there is no key

diff = returns_from_r.join(variability_table, how='inner')

n = diff.count()

# Set variables from dependencies (assume these are provided elsewhere in the pipeline)
# n, dir, nv, keep are assumed to be set as Python variables

# Set pass/fail and notes based on comparison
if n == 0:
