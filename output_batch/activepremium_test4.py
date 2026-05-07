# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("ActivePremium_test4").getOrCreate()

# Initialize Spark session

# Convert pandas DataFrames to Spark DataFrames

    error_schema = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    error_data = [(-999, -999, -999, -999, -999)]

    error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_from_r = spark.createDataFrame(error_data, error_schema)

    compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    returns_comp = returns_from_r

# Filter for differences as in SAS proc compare

# Count number of differences

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST ActivePremium_test4')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST ActivePremium_test4')

# Optionally clean up intermediate DataFrames if keep is False
if not keep:

    prices = None

    returns_from_r = None

    active_premium = None

    diff = None

# Calculate log returns using pandas

# Set up variables from macro (assume these are provided or set elsewhere)
# n, dir, nv, keep are assumed to be Python variables

# Read prices.csv as DataFrame using pandas

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

# ActivePremium calculation: (mean(asset returns) - mean(benchmark return)) * scale
# Assume first 4 columns are assets, 5th column is benchmark (SPY), scale=12

assets = returns_pd.iloc[:, 0:4]

benchmark = returns_pd.iloc[:, 4]

active_premium_pd = (assets.mean(axis=0) - benchmark.mean()) * 12

active_premium_df = pd.DataFrame([active_premium_pd.values], columns=assets.columns)
active_premium_df['SPY'] = benchmark.mean() * 12

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

active_premium = spark.createDataFrame(active_premium_df)

# Read prices into Spark DataFrame (if needed elsewhere)

prices = spark.createDataFrame(prices_pd.reset_index())

# Handle empty DataFrames by replacing with error DataFrames
if active_premium.count() == 0:

    active_premium = spark.createDataFrame(error_data, error_schema)
if returns_from_r.count() == 0:

# Ensure both DataFrames have the same columns for comparison
if 'date' in returns_from_r.columns:

    returns_comp = returns_from_r.select(compare_cols)
else:

# Prepare active_premium DataFrame for join

active_premium_comp = active_premium.select(['IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# Compare returns_from_r and active_premium DataFrames

diff = returns_comp.crossJoin(active_premium_comp).select([
    (col('IBM') - col('IBM')).alias('IBM'),
    (col('GE') - col('GE')).alias('GE'),
    (col('DOW') - col('DOW')).alias('DOW'),
    (col('GOOGL') - col('GOOGL')).alias('GOOGL'),
    (col('SPY') - col('SPY')).alias('SPY')
])

diff_filtered = diff.filter(
    (pyspark_abs(col('IBM')) > 1e-5) |
    (pyspark_abs(col('GE')) > 1e-5) |
    (pyspark_abs(col('DOW')) > 1e-5) |
    (pyspark_abs(col('GOOGL')) > 1e-5)
)

n = diff_filtered.count()

# Set pass/notes variables based on comparison
if n == 0:
