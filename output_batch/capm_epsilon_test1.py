# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

spark = SparkSession.builder.appName("CAPM_epsilon_test1").getOrCreate()

# Initialize Spark session

    excess_returns = returns.sub(rf)

    benchmark_excess = returns[benchmark_col] - rf

    epsilon = pd.DataFrame(index=returns.index)
    for col in returns.columns:
        if col == benchmark_col:
            continue

# --- CAPM epsilon calculation ---

        X = benchmark_excess.values.reshape(-1, 1)

        y = excess_returns[col].values

        beta = np.linalg.lstsq(X, y, rcond=None)[0][0]

        pred = beta * X.flatten()
        epsilon[col] = y - pred
    return epsilon

benchmark_col = 'SPY'

def capm_epsilon(returns, benchmark_col, rf=0.01/252):

# --- Convert pandas DataFrames to Spark DataFrames ---

    epsilon_sdf = None

# --- Create error DataFrames if needed ---

schema = StructType([
    StructField('date', IntegerType(), True),
    StructField('IBM', DoubleType(), True),
    StructField('GE', DoubleType(), True),
    StructField('DOW', DoubleType(), True),
    StructField('GOOGL', DoubleType(), True),
    StructField('SPY', DoubleType(), True)
])

# Define file paths and macro variables (assumed provided externally)

    epsilon_sdf = spark.createDataFrame([(-1, -999.0, -999.0, -999.0, -999.0, -999.0)], schema)

# --- Compare returns and epsilon DataFrames ---

# --- Count number of differences ---

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST CAPM_epsilon_TEST1')
else:

dir_path = dir  # Provided macro variable

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST CAPM_epsilon_TEST1')

keep = keep     # Provided macro variable (should be boolean or string 'TRUE'/'FALSE')

# --- Clean up temporary tables if keep is FALSE ---
if str(keep).upper() == 'FALSE':
    for df in ['diff_sdf', 'returns_sdf', 'epsilon_sdf']:
        if df in locals():
            eval(df).unpersist()

# --- Read and process price data ---

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)  # Assume first column is date

# Calculate returns (discrete, drop NA)

returns_pd = prices_pd.pct_change().dropna()

epsilon_pd = capm_epsilon(returns_pd, benchmark_col, rf=0.01/252)

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

epsilon_sdf = spark.createDataFrame(epsilon_pd.reset_index())

# --- Save intermediate results if keep is TRUE ---
if str(keep).upper() == 'TRUE':
    returns_sdf.write.mode('overwrite').parquet(os.path.join(dir_path, 'returns_from_r.parquet'))
    epsilon_sdf.write.mode('overwrite').parquet(os.path.join(dir_path, 'epsilon.parquet'))

# --- Handle empty DataFrames ---
if returns_sdf.count() == 0:
    returns_sdf.unpersist()

    returns_sdf = None
if epsilon_sdf.count() == 0:
    epsilon_sdf.unpersist()

if returns_sdf is None:

    returns_sdf = spark.createDataFrame([(1, 999.0, 999.0, 999.0, 999.0, 999.0)], schema)
if epsilon_sdf is None:

diff_sdf = returns_sdf.join(
    epsilon_sdf,
    on='date',
    how='inner',
    suffixes=('_r', '_e')
).withColumn(
    'IBM_diff', F.abs(F.col('IBM_r') - F.col('IBM_e'))
).withColumn(
    'GE_diff', F.abs(F.col('GE_r') - F.col('GE_e'))
).withColumn(
    'DOW_diff', F.abs(F.col('DOW_r') - F.col('DOW_e'))
).withColumn(
    'GOOGL_diff', F.abs(F.col('GOOGL_r') - F.col('GOOGL_e'))
).filter(
    (F.col('IBM_diff') > 1e-4) |
    (F.col('GE_diff') > 1e-4) |
    (F.col('DOW_diff') > 1e-4) |
    (F.col('GOOGL_diff') > 1e-4)
)

n = diff_sdf.count()

# --- Set pass/fail and notes variables ---
if n == 0:
