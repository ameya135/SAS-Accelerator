# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col, lit, when

spark = SparkSession.builder.appName("bull_bear_beta").getOrCreate()

# Initialize Spark session

# Calculate discrete returns using pandas/numpy

# Define risk-free rate

rf = 0.01 / 252

# Helper functions for bull and bear beta calculations

    market = returns[market_col]

    mask = market > 0

    betas = {}
    for col_name in asset_cols:

        cov = np.cov(returns.loc[mask, col_name], market[mask])[0, 1]

        var = np.var(market[mask])
        betas[col_name] = cov / var if var != 0 else np.nan
    return pd.DataFrame([betas], index=['bull'])

    market = returns[market_col]

    mask = market < 0

    betas = {}
    for col_name in asset_cols:

        cov = np.cov(returns.loc[mask, col_name], market[mask])[0, 1]

        var = np.var(market[mask])
        betas[col_name] = cov / var if var != 0 else np.nan
    return pd.DataFrame([betas], index=['bear'])

# Specify asset and market columns

asset_cols = ['IBM', 'GE', 'DOW', 'GOOGL']

# Set up configuration variables

market_col = 'SPY'

def capm_beta_bull(returns, market_col, asset_cols):

def capm_beta_bear(returns, market_col, asset_cols):

# Calculate bull and bear betas

# Combine results and set market beta to 1

bull_and_bear_pd = pd.concat([capm_bull, capm_bear])
bull_and_bear_pd[market_col] = 1.0  # Market beta is 1 by definition
bull_and_bear_pd.reset_index(inplace=True)
bull_and_bear_pd.rename(columns={'index': 'regime'}, inplace=True)

# Convert results back to Spark DataFrames

bull_and_bear_df = spark.createDataFrame(bull_and_bear_pd)

# Handle empty DataFrames by replacing with error rows
if bull_and_bear_df.count() == 0:

keep = False  # Set to True to keep intermediate DataFrames

    error_data = [{'regime': 'error', 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}]

    bull_and_bear_df = spark.createDataFrame(error_data)

    error_data = [{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}]

    returns_from_r_df = spark.createDataFrame(error_data)

# Compare DataFrames: find differences (fuzzy match for numeric columns)

diff_exprs = [
    when(abs(col('base.' + c) - col('compare.' + c)) > 1e-6, lit(1)).otherwise(lit(0)).alias(c + '_diff')
    for c in asset_cols + [market_col]
]

# Count number of differences

diff_sum_cols = [col(c + '_diff') for c in asset_cols + [market_col]]

data_dir = os.environ.get('DIR', '/path/to/dir')

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST bull_bear_beta_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST bull_bear_beta_TEST')

# Clean up temporary DataFrames if keep is False
if not keep:

    prices_df = None

    bull_and_bear_df = None

    returns_from_r_df = None

# Read prices CSV as Spark DataFrame

    diff_df = None

prices_path = os.path.join(data_dir, 'prices.csv')

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

prices_pd = prices_df.toPandas()
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

capm_bull = capm_beta_bull(returns_pd, market_col, asset_cols)

capm_bear = capm_beta_bear(returns_pd, market_col, asset_cols)

returns_from_r_df = spark.createDataFrame(returns_pd.reset_index())

if returns_from_r_df.count() == 0:

diff_df = (
    returns_from_r_df.alias('base')
    .join(bull_and_bear_df.alias('compare'), on=None, how='outer')
    .select(*diff_exprs)
)

n = diff_df.select(sum(diff_sum_cols).alias('n')).collect()[0]['n']

# Set pass/fail and notes
if n == 0:

# Convert prices to Pandas DataFrame for financial calculations
