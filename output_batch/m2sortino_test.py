# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StructField, StructType
# Compare DataFrames: compute differences with fuzz logic
from pyspark.sql.functions import abs as spark_abs, col

spark = SparkSession.builder.appName("M2Sortino_Test").getOrCreate()

# Initialize Spark session

# Define M2Sortino calculation in pandas

    downside = np.where(returns < MAR, (returns - MAR) ** 2, 0)

    downside_deviation = np.sqrt(np.mean(downside, axis=0)) * np.sqrt(scale)

    mean_returns = returns.mean(axis=0) * scale

    sortino = (mean_returns - MAR * scale) / downside_deviation

    bm_returns = returns[benchmark_col]

    bm_downside = np.where(bm_returns < MAR, (bm_returns - MAR) ** 2, 0)

    bm_downside_deviation = np.sqrt(np.mean(bm_downside)) * np.sqrt(scale)

    bm_sortino = (bm_returns.mean() * scale - MAR * scale) / bm_downside_deviation

    m2sortino_val = bm_sortino + (sortino - bm_sortino)
    return pd.DataFrame([m2sortino_val], columns=returns.columns)

# Compute M2Sortino using the 5th column as benchmark (SPY assumed)

# Convert results back to Spark DataFrames

# Handle empty DataFrames by replacing with error DataFrames

error_schema = StructType([
    StructField('IBM', DoubleType(), True),
    StructField('GE', DoubleType(), True),
    StructField('DOW', DoubleType(), True),
    StructField('GOOGL', DoubleType(), True),
    StructField('SPY', DoubleType(), True)
])

# Macro variable equivalents (should be set externally or passed as arguments)
# Example usage:
# dir = '/path/to/dir'
# keep = False

    returns_spark_df = spark.createDataFrame([(float(999), float(999), float(999), float(999), float(999))], schema=error_schema)

def fuzz_expr(col1, col2):
    return (spark_abs(col1 - col2) > 1e-6)

# Filter rows where any difference is detected

# Count number of differences

# Read prices CSV as Spark DataFrame

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST M2sortino_test')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST M2sortino_test')

prices_path = os.path.join(dir, 'prices.csv')

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Convert prices to Pandas DataFrame for financial calculations

prices_pd = prices_df.toPandas().set_index(prices_df.columns[0])

returns_pd = prices_pd.pct_change().dropna()

benchmark_col = returns_pd.columns[4]

def m2sortino(returns, benchmark_col, MAR=0.01/252, scale=252):

m2sortino_pd = m2sortino(returns_pd, benchmark_col, MAR=0.01/252, scale=252)

returns_spark_df = spark.createDataFrame(returns_pd.reset_index())

m2sortino_spark_df = spark.createDataFrame(m2sortino_pd)

if m2sortino_spark_df.count() == 0:

    m2sortino_spark_df = spark.createDataFrame([(float(-999), float(-999), float(-999), float(-999), float(-999))], schema=error_schema)
if returns_spark_df.count() == 0:

diff_df = returns_spark_df.join(
    m2sortino_spark_df,
    on=['IBM', 'GE', 'DOW', 'GOOGL', 'SPY'],
    how='outer'
).withColumn(
    'IBM_DIF', fuzz_expr(col('IBM'), col('IBM'))
).withColumn(
    'GE_DIF', fuzz_expr(col('GE'), col('GE'))
).withColumn(
    'DOW_DIF', fuzz_expr(col('DOW'), col('DOW'))
).withColumn(
    'GOOGL_DIF', fuzz_expr(col('GOOGL'), col('GOOGL'))
)

diff_filtered_df = diff_df.filter(
    col('IBM_DIF') | col('GE_DIF') | col('DOW_DIF') | col('GOOGL_DIF')
)

n_diff = diff_filtered_df.count()

# Set pass/fail and notes based on n_diff
if n_diff == 0:

# If keep is False, unpersist intermediate tables
if not keep:
    prices_df.unpersist()
    diff_filtered_df.unpersist()
    returns_spark_df.unpersist()
    m2sortino_spark_df.unpersist()

# Calculate returns using pandas (discrete method)
