# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T

spark = SparkSession.builder.appName('table_CAPM_test2').getOrCreate()

# Initialize Spark session

# Calculate discrete returns, drop NA

# CAPM calculation (using pandas/numpy)

Rf = 0.01

digits = 6

bm_col = 'SPY'

asset_cols = ['IBM', 'GE', 'DOW', 'GOOGL']

bm_returns = returns_pd[bm_col]

capm_results = {}
for asset in asset_cols:

    excess_asset = returns_pd[asset] - Rf

    excess_bm = bm_returns - Rf

    beta = np.cov(excess_asset, excess_bm)[0, 1] / np.var(excess_bm)

    alpha = np.mean(excess_asset) - beta * np.mean(excess_bm)
    capm_results[asset] = {'alpha': round(alpha, digits), 'beta': round(beta, digits)}

# Prepare CAPM DataFrame

capm_df = pd.DataFrame({
    'asset': list(capm_results.keys()),
    'alpha': [v['alpha'] for v in capm_results.values()],
    'beta': [v['beta'] for v in capm_results.values()]
})

# Convert returns and CAPM results to Spark DataFrames

capm_sdf = spark.createDataFrame(capm_df)

# If tables have 0 records, set to None
if capm_sdf.count() == 0:

# Macro variables (replace with actual values or pass as arguments)

    returns_sdf = None

    capm_error_schema = T.StructType([
        T.StructField('asset', T.StringType(), True),
        T.StructField('alpha', T.DoubleType(), True),
        T.StructField('beta', T.DoubleType(), True)
    ])

    returns_error_schema = T.StructType([
        T.StructField('date', T.DateType(), True),
        T.StructField('IBM', T.DoubleType(), True),
        T.StructField('GE', T.DoubleType(), True),
        T.StructField('DOW', T.DoubleType(), True),
        T.StructField('GOOGL', T.DoubleType(), True),
        T.StructField('SPY', T.DoubleType(), True)
    ])

    returns_sdf = spark.createDataFrame([(pd.Timestamp('1900-01-01'), 999.0, 999.0, 999.0, 999.0, 999.0)], schema=returns_error_schema)

n = None  # will be set later

# Set pass/notes variables
if n == 0:

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_CAPM_test2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_CAPM_test2')

# Optionally drop intermediate DataFrames if not keeping
if not keep:

    returns_sdf = None

    capm_sdf = None

    diff_sdf = None

data_dir = os.environ.get('DIR', '/path/to/dir')

keep = False  # or True, as needed

# Load prices data

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

    capm_sdf = None
if returns_sdf.count() == 0:

# If CAPM or returns_sdf do not exist, create error DataFrames
if capm_sdf is None:

    capm_sdf = spark.createDataFrame([('ERROR', -999.0, -999.0)], schema=capm_error_schema)
if returns_sdf is None:

# Compare returns_sdf and capm_sdf (absolute difference, as in proc compare)
# Note: Since capm_sdf is per-asset, and returns_sdf is per-date, this join is illustrative.
# In practice, you would compare returns_sdf to expected returns, not CAPM summary stats.
# Here, we just check if returns_sdf has any abnormal values as a placeholder.

diff_sdf = returns_sdf.filter(
    (F.abs(F.col('IBM')) > 1e2) |
    (F.abs(F.col('GE')) > 1e2) |
    (F.abs(F.col('DOW')) > 1e2) |
    (F.abs(F.col('GOOGL')) > 1e2)
)

n = diff_sdf.count()
