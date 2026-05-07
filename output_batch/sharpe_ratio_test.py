# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit, max as pyspark_max, mean, sqrt, stddev
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SharpeRatioTest").getOrCreate()

# Initialize Spark session

# Calculate Sharpe Ratio (annualized, risk-free rate 0.02, using standard deviation)

rf = 0.02

# Convert pandas DataFrames to Spark DataFrames

# --- Calculate returns in Spark (discrete method) ---

# Remove first row with null returns

# --- Calculate Sharpe Ratio in Spark ---

annualization_factor = sqrt(lit(252))

# Set variables (assume these are provided elsewhere or set here for testing)

    mean_col = mean(col(col_name) - rf / 252)

    std_col = stddev(col(col_name))

SharpeRatio_spark = SharpeRatio_spark.withColumn('date', pyspark_max('date'))

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Keep only the last row in SharpeRatio

SharpeRatio = SharpeRatio.orderBy(col('date').desc()).limit(1)

dir_path = os.environ.get('DIR', '/path/to/dir')

prices = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

# --- Read prices.csv as Spark DataFrame ---

window_spec = Window.orderBy('date')
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(
            f'{col_name}_return',
            (col(col_name) - lag(col(col_name), 1).over(window_spec)) / lag(col(col_name), 1).over(window_spec)
        )

return_cols = [f'{c}_return' for c in prices.columns if c != 'date']

prices = prices.dropna(subset=return_cols)

sharpe_exprs = []
for col_name in [c for c in prices.columns if c.endswith('_return')]:

    sharpe_expr = (mean_col / std_col) * annualization_factor
    sharpe_exprs.append(sharpe_expr.alias(col_name.replace('_return', '')))

SharpeRatio_spark = prices.agg(*sharpe_exprs)

    diff = diff.withColumn(f'{ticker}_DIF', pyspark_abs(col(f'{ticker}_r') - col(f'{ticker}_s')))

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Sharpe_Ratio_TEST')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Sharpe_Ratio_TEST')

keep = os.environ.get('KEEP', 'FALSE')

# --- Read and process prices.csv using pandas ---

prices_pdf = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pdf['date'] = pd.to_datetime(prices_pdf['date'])
prices_pdf.set_index('date', inplace=True)

# Calculate returns using pandas (discrete method)

returns_pdf = prices_pdf.pct_change().dropna()

excess_returns = returns_pdf - rf / 252  # Assuming daily data

sharpe_ratios = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

sharpe_ratio_pdf = pd.DataFrame([sharpe_ratios], columns=sharpe_ratios.index)
sharpe_ratio_pdf['date'] = returns_pdf.index.max()

sharpe_ratio_pdf = sharpe_ratio_pdf[['date'] + [c for c in sharpe_ratios.index]]

returns_from_r = spark.createDataFrame(returns_pdf.reset_index())

SharpeRatio = spark.createDataFrame(sharpe_ratio_pdf)

# --- Handle empty DataFrames for error signaling ---
if SharpeRatio.count() == 0:

    SharpeRatio = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r.count() == 0:

# --- Compare returns_from_r and SharpeRatio ---

diff = returns_from_r.join(SharpeRatio, on='date', how='inner', suffixes=('_r', '_s'))
for ticker in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

diff_filtered = diff.filter(
    (col('IBM_DIF') > 1e-4) |
    (col('GE_DIF') > 1e-4) |
    (col('DOW_DIF') > 1e-4) |
    (col('GOOGL_DIF') > 1e-4) |
    (col('SPY_DIF') > 1e-4)
)

n = diff_filtered.count()

# --- Set pass/notes based on comparison ---
if n == 0:

# --- Drop intermediate tables if keep==FALSE ---
if keep == 'FALSE':
    SharpeRatio.unpersist()
    returns_from_r.unpersist()
    prices.unpersist()
    diff.unpersist()
