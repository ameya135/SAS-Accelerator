# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("OmegaSharpeRatioTest").getOrCreate()

# -------------------------------
# Initialize Spark session
# -------------------------------

# -------------------------------
# Calculate Omega Sharpe Ratio
# -------------------------------

MAR = 0.01 / 252

# -------------------------------
# Convert pandas DataFrames to Spark DataFrames
# -------------------------------

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# -------------------------------
# Compare DataFrames and output differences
# -------------------------------

diff = diff.withColumn('IBM_DIF', pyspark_abs(col('base.IBM') - col('compare.IBM')) > 1e-8)

diff = diff.withColumn('GE_DIF', pyspark_abs(col('base.GE') - col('compare.GE')) > 1e-8)

# -------------------------------
# Define file paths and parameters
# -------------------------------

diff = diff.withColumn('DOW_DIF', pyspark_abs(col('base.DOW') - col('compare.DOW')) > 1e-8)

diff = diff.withColumn('GOOGL_DIF', pyspark_abs(col('base.GOOGL') - col('compare.GOOGL')) > 1e-8)

diff = diff.withColumn('SPY_DIF', pyspark_abs(col('base.SPY') - col('compare.SPY')) > 1e-8)

# -------------------------------
# Count number of differences
# -------------------------------

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST OMEGA_SHARPERATIO_TEST')
else:

    pass_test = False

dir_path = dir  # Provided macro variable

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST OMEGA_SHARPERATIO_TEST')

prices_csv_path = os.path.join(dir_path, 'prices.csv')

keep_files = keep  # Provided macro variable, should be boolean

# -------------------------------
# Read and preprocess prices data
# -------------------------------

prices_pd = pd.read_csv(prices_csv_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

excess_returns = returns_pd - MAR

omega_sharpe = excess_returns.mean() / excess_returns.std()

omega_sharpe_df = pd.DataFrame([omega_sharpe], columns=omega_sharpe.index)
omega_sharpe_df['date'] = returns_pd.index[-1]

omega_sharpe_df = omega_sharpe_df[['date'] + list(omega_sharpe.index)]

returns_from_r_df = returns_pd.copy()
returns_from_r_df.reset_index(inplace=True)

OmegaSharpe = spark.createDataFrame(omega_sharpe_df)

# Prepare OmegaSharpe DataFrame

returns_from_r = spark.createDataFrame(returns_from_r_df)

# Prepare returns_from_r DataFrame

# -------------------------------
# Handle empty DataFrames
# -------------------------------
if OmegaSharpe.count() == 0:

    OmegaSharpe = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r.count() == 0:

diff = returns_from_r.alias('base').join(
    OmegaSharpe.alias('compare'),
    on=['date'],
    how='outer'
)

diff_filtered = diff.filter(
    col('IBM_DIF') | col('GE_DIF') | col('DOW_DIF') | col('GOOGL_DIF') | col('SPY_DIF')
)

n = diff_filtered.count()

# -------------------------------
# Set pass/fail and notes variables
# -------------------------------
if n == 0:

# -------------------------------
# Cleanup if keep_files is False
# -------------------------------
if not keep_files:
    OmegaSharpe.unpersist()
    returns_from_r.unpersist()
    diff.unpersist()

# -------------------------------
# Calculate discrete returns
# -------------------------------
